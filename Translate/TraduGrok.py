import os
import json
from dotenv import load_dotenv
import maritalk
from collections import deque
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from pydantic import BaseModel
from groq import Groq, BadRequestError
from pydantic_core import ValidationError

load_dotenv()
groq = Groq()

class RateLimiter:
    def __init__(self, max_calls, period=60):
        self.max_calls = max_calls
        self.period = period
        self.call_times = deque()

    def wait_for_slot(self):
        current_time = time.time()
        while self.call_times and current_time - self.call_times[0] > self.period:
            self.call_times.popleft()

        if len(self.call_times) >= self.max_calls:
            sleep_time = self.period - (current_time - self.call_times[0])
            print(f"Rate limit reached, sleeping for {sleep_time:.2f} seconds.")
            time.sleep(sleep_time)
        self.call_times.append(time.time())

rate_limiter = RateLimiter(max_calls=30)

class Instruction(BaseModel):
    instruction: str
    output: str

def save_to_cache(index, data, cache_folder='.cache'):
    if not os.path.exists(cache_folder):
        os.makedirs(cache_folder)
    file_path = os.path.join(cache_folder, f'{index}.json')
    with open(file_path, 'w') as f:
        json.dump(data, f, ensure_ascii=False)

def is_processed(index, cache_folder='.cache'):
    file_path = os.path.join(cache_folder, f'{index}.json')
    return os.path.exists(file_path)

def get_translation_batch(documents: list, start_index: int):
    for idx, documento in enumerate(documents):
        index = start_index + idx
        if not is_processed(index):
            rate_limiter.wait_for_slot()  # Ensure we're within rate limit before each call
            try:
                translation = get_translation(documento)
                save_to_cache(index, translation.dict())
            except Exception as e:
                print(f"Error processing document {index}: {e}")
        else:
            print(f"Document {index} already processed.")

# Split your existing `get_translation` into two functions
# One for the try-except block (get_translation) and another for making the API call (make_api_call)
def get_translation(documento: dict) -> Instruction:
    max_retries = 3
    attempts = 0
    while attempts < max_retries:
        try:
            response = make_api_call(documento)
            if "documento['instruction']" in response:
                raise ValueError("A mensagem não foi traduzida.")
            if "Translate the following" in response or "Traduza a seguinte" in response:
                raise ValueError("Parte do prompt está na mensagem")
            return Instruction.model_validate_json(response)
        except (BadRequestError, ValidationError, ValueError) as e:
            print(f"Error encountered: {e}. Retrying ({attempts+1}/{max_retries})...")
            attempts += 1
            time.sleep(1)  # Wait a bit before retrying
        except Exception as e:
            print(f"Unhandled exception: {e}. Giving up.")
            break  # Exit the loop for unhandled exceptions
    raise Exception("Failed to process document after several retries.")

def make_api_call(documento: dict):
    chat_completion = groq.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": "Você é um tradutor português brasileiro da área de TI, sua única tarefa é traduzir e manter o schema apresentado a seguir em JSON. Sob hipótese alguma você respode ou insere comentários além da tradução.\n"
                f" O Schema do JSON é: {json.dumps(Instruction.model_json_schema(), indent=2)}",
            },
            {
                "role": "user",
                "content": f"""Traduza a seguinte instrução/pergunta e resposta do inglês para o português.
                O output deve ser um JSON com as chaves intruction (para a instrução) e output (para a resposta).
                Sua resposta deve conter apenas as traduções e nada mais. AS CHAVES PERMANECEM EM INGLÊS evite traduzir logs e mensagens de sistema de computador pois o público alvo é da área de TI também. Lembre-se você apenas traduz.\n 
                # Documento para traduzir:
                {{"instruction": {documento['instruction']}, "output": {documento['output']}}}
                """
            },
        ],
        model="mixtral-8x7b-32768",
        stream=False,
        response_format={"type": "json_object"},
    )
    return chat_completion.choices[0].message.content

# Your existing functions for saving to cache and checking if processed

def process_batch(start_index, batch):
    get_translation_batch(batch, start_index)

if __name__ == "__main__":
    caminho_completo = 'OWL-Instruct/data/ops_ch_en_001_english.json'
    with open(caminho_completo, 'r', encoding='utf-8') as arquivo:
        conteudo = arquivo.read()
        instruct = json.loads(conteudo)

    batch_size = 10
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = []
        for i in range(0, len(instruct), batch_size):
            batch = instruct[i:i + batch_size]
            futures.append(executor.submit(process_batch, i, batch))
        
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"An error occurred: {e}")

