import os
import openai
openai.organization = "org-l04YV8WpN6hwxoVLNOrW3Gr0"
openai.api_key_path = 'api_key.txt'

# print(openai.Model.list())

# Set up the model and prompt
model_engine = "text-davinci-003"


# Generate a response
def request(prompt: str):
    completion = openai.Completion.create(
        engine=model_engine,
        prompt=prompt,
        max_tokens=1024,
        n=1,
        stop=None,
        temperature=0.5,
    )
    response = completion.choices[0].text
    return response


if __name__ == '__main__':
    request('Hello, how are you date?')


