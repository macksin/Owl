
import pandas as pd
from dotenv import load_dotenv
import os
import maritalk

load_dotenv()
maritaka_api = os.getenv("MARITACA")

model = maritalk.MariTalk(
    key=maritaka_api,
    model="sabia-2-medium"
)

# Load the file
import json
caminho_completo = 'OWL-Instruct/data/ops_ch_en_001_english.json'
with open(caminho_completo, 'r', encoding='utf-8') as arquivo:
    conteudo = arquivo.read()
    instruct = json.loads(conteudo)

import json
import os

# Simulated translation function
def traduzir_texto(texto, model=model):
    messages = [
        {"role": "system", "content": "Você é um tradutor da área de tecnologia e programação, você traduz para o português brasileiro."},
        {"role": "user", "content": f"traduza: {texto}"},
    ]

    answer = model.generate(
    messages,
    do_sample=True,
    max_tokens=1024,
    temperature=0.2,
    top_p=0.95)["answer"]

    return answer


# Path to the cache folder where individual JSON files will be saved
cache_folder = '.cache/instruct'
os.makedirs(cache_folder, exist_ok=True)

# Process each item in the JSON data
for i, item in enumerate(instruct):
    print(f"{i}/{len(instruct)}")
    file_path = os.path.join(cache_folder, f"{i}.json")
    
    # Check if this item has already been processed by looking for its file
    if os.path.exists(file_path):
        print(f"Skipping already processed item {i}.")
        continue

    try:
        # Translate the 'instruction' and 'output' fields
        item['instruction'] = traduzir_texto(item['instruction'])
        item['output'] = traduzir_texto(item['output'])
        
        # Save the translated item to a separate JSON file in the cache folder
        with open(file_path, 'w') as f:
            json.dump(item, f, ensure_ascii=False)
    except Exception as e:
        print(f"Error processing item {i}: {e}")

# Output a message when processing is complete
print("Processing complete. Translated items are saved in the cache folder.")
