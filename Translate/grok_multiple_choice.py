from typing import List
import pandas as pd
from dotenv import load_dotenv
import os

from groq import Groq, BadRequestError
from pydantic_core import ValidationError
import json
from pydantic import BaseModel
from tqdm import tqdm
import time

load_dotenv()
groq = Groq()


class Instruction(BaseModel):
    id: int
    question: str
    A: str
    B: str
    C: str
    D: str


class GroqTranslator:

    def __init__(self, model: Groq):
        self.model = model

    def make_api_call(self, document: dict):
        chat_completion = groq.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "Você é um tradutor de inglês para português brasileiro especializado em tecnologia da informação e computação.\n"
                    f"A saída deve obedecer ao schema do JSON:"
                    """
                    {
                        "id": integer, já vem com a pergunta,
                        "question": string, Questão traduzida,
                        "A": string, opção A traduzida,
                        "B": string, opção B traduzida,
                        "C": string, opção C traduzida,
                        "D": string, opção D traduzida
                    }
                    """
                },
                {
                    "role": "user",
                    "content": f"""Traduza o documento a seguir, mantenha o jargão técnico e termos da área de tecnologia em inglês, além de linhas de programação. Não faça nenhum comentário apenas traduza seguinte as diretrizes:
                    {{
                        "id": {document['id']}, 
                        "question": {document['question']}, 
                        "A": {document['A']},
                        "B": {document['B']},
                        "C": {document['C']},
                        "D": {document['D']}
                    }}
                    """
                },
            ],
            model="mixtral-8x7b-32768",
            stream=False,
            response_format={"type": "json_object"},
        )
        return Instruction.model_validate_json(chat_completion.choices[0].message.content)


def load_cache(cache_file: str) -> List[dict]:
    if os.path.exists(cache_file):
        with open(cache_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        return []

def save_cache(cache: List[dict], cache_file: str) -> None:
    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=4)
def retry_with_exponential_backoff(func, max_retries=3, base_delay=1):
    """
    Decorator to retry a function with exponential backoff.

    Parameters:
    - func: The function to retry.
    - max_retries: Maximum number of retries.
    - base_delay: Base delay in seconds for the backoff.
    """
    def wrapper(*args, **kwargs):
        retries = 0
        while retries < max_retries:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                wait = base_delay * 2 ** retries
                print(f"Attempt {retries + 1} failed with error: {e}. Retrying in {wait} seconds...")
                time.sleep(wait)
                retries += 1
        raise Exception(f"All {max_retries} retries failed.")
    return wrapper

@retry_with_exponential_backoff
def make_api_call_with_retry(translator, document):
    return translator.make_api_call(document)

def process_dataframe_with_cache_and_retry(df: pd.DataFrame, translator: GroqTranslator, cache_file: str) -> List[dict]:
    cache = load_cache(cache_file)
    processed_ids = {item['id'] for item in cache}  # Extract already processed IDs
    multiple_choice = cache  # Start with what's in the cache

    for i, row in df.iterrows():
        if row.id not in processed_ids:
            document = dict(
                id=row.id,
                question=row.question,
                A=row.A,
                B=row.B,
                C=row.C,
                D=row['D.']
            )
            try:
                document = make_api_call_with_retry(translator, document).dict()
                document['answer'] = row['answer'][:1]
                document['category'] = row['category']
                multiple_choice.append(document)
                save_cache(multiple_choice, cache_file)  # Update cache file with new data
            except Exception as e:
                print(f"Final failure processing ID {row.id}: {e}")
                # Decide whether to break, continue, or handle differently
                continue

    return multiple_choice
    

if __name__ == "__main__":
    grok = Groq()
    grok_translate = GroqTranslator(model=grok)
    document = dict(
        id = 1,
        question = "Suppose you are an operation and maintenance engineer of a large network company, and you need to write a Bash script to regularly monitor and record the CPU and memory usage of the server. Which of the following commands can be used in a Bash script to gather this information?",
        A = "ifconfig",
        B = "netstat",
        C = "top",
        D = "lsblk"
    )

    translation = grok_translate.make_api_call(document=document)
    print(translation)

    # Dataframe
    caminho_do_arquivo = 'Multiple_Choice/data/ops_data_en.xlsx'
    df = pd.read_excel(caminho_do_arquivo)
    multiple_choice = process_dataframe_with_cache_and_retry(df, translator=grok_translate, cache_file='arquivodecache.txt')

    multiple_choice = pd.DataFrame(multiple_choice)

    multiple_choice.to_csv("translated/multiple_choice_ptbr.csv", index=False, encoding='utf-8', sep=',')    