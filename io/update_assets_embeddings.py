import json
import requests
from typing import List
import os

import time
import threading

from concurrent.futures import ThreadPoolExecutor

from gptworld.models.openai_api import get_embedding


def get_embeddings_for_assets(type='tile'):
    # 设置要读取的目录路径
    dir_path = f'assets/{type}'

    # 获取目录中所有的PNG文件
    png_files = [f for f in os.listdir(dir_path) if f.endswith('.png')]

    # 初始化一个空列表用于存储所有的字典
    dict_list = []

    success = 0

    # 定义一个函数，用于获取嵌入向量并将其添加到字典列表中
    def process_file(png_file):
        # 提取PNG文件的名称并去除后缀
        name = os.path.splitext(png_file)[0]

        # 重试操作，最多尝试3次
        retries = 3
        while retries > 0:
            try:
                # 获取嵌入向量
                embedding = get_embedding(os.path.join(dir_path, png_file))
                print("success!")
                break  # 如果成功，则退出循环
            except Exception as e:
                print(f'Error while processing file {png_file}: {e}')
                retries -= 1
                if retries == 0:
                    print(f'Failed to process file {png_file}')
                    return  # 如果失败，则返回

                print(f'Retrying in 5 seconds...')
                time.sleep(1)  # 等待5秒后重试

        # 构建字典并将其添加到列表中
        file_dict = {'name': name, 'embedding': embedding, 'path': png_file}
        # dict_list.append(file_dict)


        # 将字典列表保存为JSON文件
        with open(os.path.join("assets/", f"{type}_embeddings.jsonl"), 'a') as f:
            f.write(json.dumps(file_dict)+"\n")
        

    with open(os.path.join("assets/", f"{type}_embeddings.jsonl"), 'w') as f:
            f.write('')
    # 使用线程池来管理线程
    with ThreadPoolExecutor(max_workers=30) as executor:
        # 提交任务给线程池处理
        for png_file in png_files:
            executor.submit(process_file, png_file)


if __name__ == "__main__":
    get_embeddings_for_assets(type='tile')