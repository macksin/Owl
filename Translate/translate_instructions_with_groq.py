import pandas as pd
from dotenv import load_dotenv
import os
import maritalk

load_dotenv()

from typing import List, Optional
import json

from pydantic import BaseModel
from groq import Groq

groq = Groq()


# Data model for LLM to generate
class Instruction(BaseModel):
    instruction: str
    output: str

def get_translation(documento: str) -> Instruction:
    chat_completion = groq.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": "Você é um tradutor português brasileiro da área de TI, você mantém jargões e linhas de programação e logs em inglês traduzindo apenas o conteúdo que é adequado. Seu output sempre é em JSON.\n"
                # Pass the json schema to the model. Pretty printing improves results.
                f" O Schema do JSON é: {json.dumps(Instruction.model_json_schema(), indent=2)}",
            },
            {
                "role": "user",
                "content": f"Traduza a seguinte instrução/pergunta e resposta do inglês para o português. O output deve ser um JSON com as chaves intruction (para a instrução) e output (para a resposta).\n # Instrução:\n{documento['instruction']}\n\n# Resposta:\n{documento['output']}",
            },
        ],
        model="mixtral-8x7b-32768",
        # Streaming is not supported in JSON mode
        stream=False,
        # Enable JSON mode by setting the response format
        response_format={"type": "json_object"},
    )
    print(chat_completion.choices[0].message.content)
    return Instruction.model_validate_json(chat_completion.choices[0].message.content)

# Load the file
import json
caminho_completo = 'OWL-Instruct/data/ops_ch_en_001_english.json'
with open(caminho_completo, 'r', encoding='utf-8') as arquivo:
    conteudo = arquivo.read()
    instruct = json.loads(conteudo)

