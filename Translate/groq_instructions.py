import os
import json
from dotenv import load_dotenv
import maritalk
from collections import deque
import time

from pydantic import BaseModel
from groq import Groq, BadRequestError
from pydantic_core import ValidationError

load_dotenv()
groq = Groq()

# RateLimiter class definition
class RateLimiter:
    def __init__(self, max_calls, period=60):
        self.max_calls = max_calls
        self.period = period
        self.call_times = deque()

    def __call__(self, func):
        def wrapped(*args, **kwargs):
            current_time = time.time()
            while self.call_times and current_time - self.call_times[0] > self.period:
                self.call_times.popleft()

            if len(self.call_times) >= self.max_calls:
                sleep_time = self.period - (current_time - self.call_times[0])
                print(f"Rate limit reached, sleeping for {sleep_time:.2f} seconds.")
                time.sleep(sleep_time)
                return wrapped(*args, **kwargs)
            else:
                self.call_times.append(time.time())
                return func(*args, **kwargs)
        return wrapped

# Data model for LLM to generate
class Instruction(BaseModel):
    instruction: str
    output: str

@RateLimiter(max_calls=30)
def get_translation(documento: dict) -> Instruction:
    max_retries = 3
    attempts = 0
    while attempts < max_retries:
        try:
            chat_completion = groq.chat.completions.create(
                messages=[
            {
                "role": "system",
                "content": "Você é um tradutor português brasileiro da área de TI, sua única tarefa é traduzir e manter o schema apresentado a seguir em JSON. Sob hipótese alguma você respode ou insere comentários além da tradução.\n"
                # Pass the json schema to the model. Pretty printing improves results.
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
            print(chat_completion.choices[0].message.content)
            if "documento['instruction']" in chat_completion.choices[0].message.content:
                raise ValueError("A mensagem não foi traduzida.")
            if "Translate the following" in chat_completion.choices[0].message.content or "Traduza a seguinte" in chat_completion.choices[0].message.content:
                raise ValueError("Parte do prompt está na mensagem")
            return Instruction.model_validate_json(chat_completion.choices[0].message.content)
        except BadRequestError as e:
            print(f"BadRequestError encountered: {e}. Retrying ({attempts+1}/{max_retries})...")
            attempts += 1
            time.sleep(1)  # Wait a bit before retrying
        except ValidationError as e:
            print(f"ValidationError encountered: {e}. Retrying ({attempts+1}/{max_retries})...")
            attempts += 1
            time.sleep(1)  # Wait a bit before retrying
        except ValueError as e:
            print(f"ValueError encountered: {e}. Retrying ({attempts+1}/{max_retries})...")
            attempts += 1
            time.sleep(1)  # Wait a bit before retrying
        except Exception as e:
            if 'Rate limit reached for model' in str(e):
                time.sleep(5)
                attempts += 1

def save_to_cache(index, data, cache_folder='.cache'):
    if not os.path.exists(cache_folder):
        os.makedirs(cache_folder)
    file_path = os.path.join(cache_folder, f'{index}.json')
    with open(file_path, 'w') as f:
        json.dump(data, f, ensure_ascii=False)

def is_processed(index, cache_folder='.cache'):
    file_path = os.path.join(cache_folder, f'{index}.json')
    return os.path.exists(file_path)

def process_document(index, documento):
    if not is_processed(index):
        translation = get_translation(documento)
        save_to_cache(index, translation.dict())
    else:
        print(f"File {index}.json already processed")

if __name__ == "__main__":
    caminho_completo = 'OWL-Instruct/data/ops_ch_en_001_english.json'
    with open(caminho_completo, 'r', encoding='utf-8') as arquivo:
        conteudo = arquivo.read()
        instruct = json.loads(conteudo)

    for index, documento in enumerate(instruct):
        try:
            process_document(index, documento)
        except Exception as e:
            time.sleep(15)
            continue
