import json
import os

# Caminho para a pasta que contém os arquivos JSON
pasta_json = '.cache'

# Lista para armazenar todos os dados JSON modificados
dados_agregados = []

# Percorrer todos os arquivos na pasta especificada
for nome_arquivo in os.listdir(pasta_json):
    if nome_arquivo.endswith('.json'):
        caminho_completo = os.path.join(pasta_json, nome_arquivo)
        
        # Ler o conteúdo do arquivo JSON
        with open(caminho_completo, 'r') as arquivo:
            dados = json.load(arquivo)
            
            # Assegurar que apenas as chaves 'instruction' e 'output' estão presentes
            dados_filtrados = {chave: dados[chave] for chave in ['instruction', 'output'] if chave in dados}
            
            # Adicionar a chave 'input' com um valor vazio
            dados_filtrados['input'] = ""
            
            # Adicionar ao conjunto de dados agregados
            dados_agregados.append(dados_filtrados)

# Criar um único arquivo JSON com todos os dados agregados
with open('ptbr_instruction.json', 'w', encoding='utf-8') as arquivo_saida:
    json.dump(dados_agregados, arquivo_saida, ensure_ascii=False, indent=4)

print(f'Arquivo "ptbr_instruction.json" criado com {len(dados_agregados)} entradas.')
