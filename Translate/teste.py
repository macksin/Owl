
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
        {"role": "system", "content": "Você é um tradutor da área de tecnologia e programação."},
        {"role": "user", "content": f"Traduza o seguinte texto para o português brasileiro, mantendo palavras e jargões da área de TI em inglês.\n# Texto para traduzir\n{texto}\n"},
    ]

    answer = model.generate(
    messages,
    do_sample=True,
    max_tokens=1024,
    temperature=0.2,
    top_p=0.95)["answer"]

    return answer

import os
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configuração inicial
cache_folder = '.cache/instruct'
os.makedirs(cache_folder, exist_ok=True)

def process_item(item, index):
    file_path = os.path.join(cache_folder, f"{index}.json")

    if os.path.exists(file_path):
        return f"Skipping already processed item {index}."

    attempts = 0
    max_attempts = 5

    while attempts < max_attempts:
        try:
            # Processamento do item, incluindo a tradução
            item['instruction'] = traduzir_texto(item['instruction'])
            item['output'] = traduzir_texto(item['output'])

            with open(file_path, 'w') as f:
                json.dump(item, f, ensure_ascii=False)

            return f"Item {index} processed."
        except Exception as e:
            if "HTTP Error: 429" in str(e):
                wait_time = 2 ** (attempts+3)  # Espera exponencial
                print(f"Rate limit reached processing item {index}. Waiting {wait_time} seconds to retry...")
                time.sleep(wait_time)
                attempts += 1
            else:
                return f"Error processing item {index}: {e}"

    return f"Failed to process item {index} after {max_attempts} attempts."

def process_batch(batch, start_index):
    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(process_item, item, index + start_index) for index, item in enumerate(batch)]
        for future in as_completed(futures):
            print(future.result())

def divide_into_batches(data, batch_size):
    for i in range(0, len(data), batch_size):
        yield data[i:i+batch_size]

def process_in_batches(instruct, batch_size, wait_between_batches):
    start_index = 0
    for batch in divide_into_batches(instruct, batch_size):
        print(f"Processing batch starting with item {start_index}...")
        process_batch(batch, start_index)
        start_index += len(batch)  # Atualiza o índice inicial para o próximo lote
        print(f"Completed batch. Waiting {wait_between_batches} seconds before the next batch...")
        time.sleep(wait_between_batches)

# Define o tamanho do lote e o tempo de espera entre os lotes
batch_size = 5  # Ajuste conforme necessário
wait_between_batches = 0.1  # Tempo de espera em segundos

# Substitua `instruct` pelo seu conjunto de dados real
process_in_batches(instruct, batch_size, wait_between_batches)

print("Processing complete. Translated items are saved in the cache folder.")
