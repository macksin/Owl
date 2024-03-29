import pandas as pd
from dotenv import load_dotenv
import os
import maritalk
import time
import json

load_dotenv()
maritaka_api = os.getenv("MARITACA")

model = maritalk.MariTalk(
    key=maritaka_api,
    model="sabia-2-medium"  # No momento, suportamos os modelos sabia-2-medium e sabia-2-small
)

def traduzir_texto(texto, model=model):
    prompt = f"""Traduza este texto para o português, mantendo os termos técnicos da área de computação e linhas de código de programação, e não forneça nenhum output adicional além do solicitado no input.
    Também mantenha o exato mesmo formato que recebeu que é um json.

    # Exemplo de input
    {{"id": 152, "question": "Regarding the discussion of the proxy server, the correct one is", "A": "To use an existing public proxy server on the Internet, only the client needs to be configured.", "B": "The proxy server can only proxy client HTTP requests.", "C": "The configured proxy server can be used by any host on the network.", "D.": "Clients using proxy servers do not have their own ip addresses."}}

    # Exemplo de output
    {{"id": 152, "question": "Em relação à discussão sobre o servidor proxy, a correta é:", "A": "Utilizar um servidor proxy público existente na Internet, apenas o cliente precisa ser configurado.", "B": "O servidor proxy só pode proxiar solicitações HTTP do cliente.", "C": "O servidor proxy configurado pode ser utilizado por qualquer host na rede.", "D.": "Os clientes que usam servidores proxy não têm seus próprios endereços IP."}}

    # Input
    {texto}

    # Output
    """
    response = model.generate(prompt)
    answer = response["answer"]
    return answer

# Carregar o arquivo XLS
caminho_do_arquivo = 'Multiple_Choice/data/ops_data_en.xlsx'
df = pd.read_excel(caminho_do_arquivo)
print(df.columns)
print("Shape ", df.shape)

# Número total de células a serem traduzidas
colunas_de_interesse = ["id", "question", "A", "B", "C", "D."]
df_filtrado = df[colunas_de_interesse]

# Definindo o caminho da pasta de cache
pasta_cache = '.cache/mc_translate'

# Verifica se a pasta de cache existe, se não, cria
if not os.path.exists(pasta_cache):
    os.makedirs(pasta_cache)
    print(f"Pasta {pasta_cache} criada.")
    

# Loop pelo DataFrame
for index, row in df_filtrado.iterrows():
    # Formando o nome do arquivo baseado no índice (ou qualquer outra coluna de interesse)
    # Se o índice for numérico ou algo que não seja diretamente um nome de arquivo, você pode adaptar esta linha
    nome_arquivo = f"{row['id']}.json"  # Exemplo de formatação do nome do arquivo
    caminho_completo = os.path.join(pasta_cache, nome_arquivo)
    
    # Verifica se o arquivo existe
    if os.path.isfile(caminho_completo):
        print(f"Arquivo {nome_arquivo} já existe. Pulando...")
        continue
    
    # Aqui você colocaria sua lógica de processamento para os itens que não foram pulados
    print(f"Processando {nome_arquivo}...")
    entrada = json.dumps(row.to_dict())
    saida = traduzir_texto(entrada)

    # Exemplo de como salvar um arquivo (substitua esta parte pela sua lógica real de processamento)
    with open(caminho_completo, 'w') as f:
        f.write(saida)
    print(f"Estamos em {index}/{len(df_filtrado)}")

# Processando Jsons

import json
import re
import os

def extrair_ultimo_json(caminho_do_arquivo):
    # Lendo o conteúdo do arquivo
    with open(caminho_do_arquivo, 'r', encoding='utf-8') as arquivo:
        conteudo = arquivo.read()

    # Encontrando todos os trechos que parecem JSON usando expressão regular
    # Isso busca por strings que começam com { e terminam com }, sendo flexível com espaços e quebras de linha
    possiveis_jsons = re.findall(r'{[\s\S]*?}', conteudo)

    if possiveis_jsons:
        # Pega o último possível JSON encontrado
        ultimo_json = possiveis_jsons[-1]

        # Converte a string JSON em um dicionário Python
        json_objeto = json.loads(ultimo_json)
        return json_objeto
    else:
        print("Nenhum JSON encontrado no arquivo:", caminho_do_arquivo)
        return None

# Substitua 'seu_diretorio' pelo diretório contendo seus arquivos de texto
caminho_dos_arquivos = '.cache/mc_translate'
arquivos = sorted(os.listdir(caminho_dos_arquivos))

# Iterando sobre cada arquivo no diretório
reprocessar = []
translated_multiple_choice = []
for nome_do_arquivo in arquivos:
    caminho_completo = os.path.join(caminho_dos_arquivos, nome_do_arquivo)
    try:
        json_extraido = extrair_ultimo_json(caminho_completo)
        # if json_extraido is not None:
            # print(f"JSON extraído de {nome_do_arquivo}:", json_extraido)
    except Exception as e:
        try:
            with open(caminho_completo, 'r', encoding='utf-8') as arquivo:
                conteudo = arquivo.read()
                json_extraido = json.loads(conteudo)
        except Exception as e:
            print(nome_do_arquivo, str(e))
            reprocessar.append(nome_do_arquivo)
    if json_extraido is None:
        reprocessar.append(nome_do_arquivo)
    if "id" not in json_extraido.keys():
        print("Verifique ", nome_do_arquivo)
    translated_multiple_choice.append(json_extraido)

print("Os arquivos a seguir precisam ser reprocessados.")
for i in reprocessar:
    print(i)


# construindo dataframe de Multiple Choice
caminho_do_arquivo = 'Multiple_Choice/data/ops_data_en.xlsx'
df = pd.read_excel(caminho_do_arquivo)

for i, file in enumerate(translated_multiple_choice):
    if "id" not in file.keys():
        print(i, file)

df_translate = pd.DataFrame(translated_multiple_choice)
df_translate['id'] = df_translate['id'].astype(int)
df_translate.sort_values('id', ascending=True, inplace=True)

df['question'] = df_translate['question']
df['A'] = df_translate['A']
df['B'] = df_translate['B']
df['C'] = df_translate['C']
df['D.'] = df_translate['D.']

print(df_translate)

df.to_csv("translated/ops_data_ptbr.csv", index=False, encoding='utf-8', sep=',')