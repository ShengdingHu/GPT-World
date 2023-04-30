import os
import json
from functools import lru_cache
import numpy as np
from typing import List, Dict
from PIL import Image
from io import BytesIO


def load_jsonl(file_path):
    """Loads a JSONL file into a list of dictionaries."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return [json.loads(line) for line in f]

def calculate_similarity(list1: List[float], list2: List[float]) -> float:
    """ calculate the cosine similarity of two semantic vectors
    """
    arr1 = np.array(list1)
    arr2 = np.array(list2)
    dot_product = np.dot(arr1, arr2)
    norm1 = np.linalg.norm(arr1)
    norm2 = np.linalg.norm(arr2)
    cosine_similarity = dot_product / (norm1 * norm2)
    return cosine_similarity

def find_most_similar_list(query: List[float], n: int, database: Dict[str, List[float]]) -> List[str]:
    """ find the most similar icons for new query in predefined database
    """
    similarities = {}
    for list_id, lst in database.items():
        similarity = calculate_similarity(query, lst)
        similarities[list_id] = similarity
    sorted_similarities = sorted(similarities.items(), key=lambda x: x[1], reverse=True)
    most_similar_lists = [list_id for list_id, similarity in sorted_similarities[:n]]
    return most_similar_lists

class TextToImage:
    def __init__(self, assets_dir: str, category: str):
        self.assets_dir = assets_dir
        self.category = category
        self.existing_object_name_to_embedding = {}
        # Build a map of image path -> semantic embedding vectors
        self.image_path_to_embedding = {}

        try:
            icon_data = load_jsonl(os.path.join(self.assets_dir, f'{self.category}_embeddings.jsonl'))
            for item in icon_data:
                path = item["path"]
                embedding = item["embedding"]
                self.image_path_to_embedding[path] = embedding
            print(f"Loaded {self.category} embeddings")
        except:
            print(f"Failed to load {self.category} embeddings")

        return

    def add_existing_object(self, name: str, embedding: List[float]):
        self.existing_object_name_to_embedding[name] = embedding
        return
    
    @lru_cache(maxsize=512)
    def query(self, name: str, n: int = 1):
        """ Find top icons according to a query, use cache to avoid redundant computation
        """

        # First get the embedding of query word
        query_vector = self.existing_object_name_to_embedding.get(name, None)
        if query_vector is None:
            # print("error")
            return []
        
        # After getting the query embedding, find the top icon names
        top_icon_paths = find_most_similar_list(query_vector, n, self.image_path_to_embedding)

        # Load icon from file system
        icon_images = []
        for path in top_icon_paths:
            full_path = os.path.join(self.assets_dir, self.category, path)
            image = Image.open(full_path)
            icon_images.append(image)

        return icon_images
        


