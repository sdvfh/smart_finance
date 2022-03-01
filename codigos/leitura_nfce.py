import pandas as pd
import requests
import xmltodict
from pymongo import MongoClient

DIRETORIO = '/home/sergio/Documentos/repositorios/casa_inteligente/nfce/historico.txt'
URI = 'mongodb://localhost'
lista_nfce = pd.read_csv(DIRETORIO, header=None)
cliente = MongoClient(URI)
nfce = cliente['nfce']
enderecos = nfce['enderecos']

# %%
for i, nota in enumerate(lista_nfce[0]):
    if 'http' in nota:
        req = nota
    else:
        req = f'http://nfce.sefaz.pe.gov.br/nfce/consulta?p={nota}'
    conteudo = xmltodict.parse(requests.get(req).content)
    if conteudo['nfeProc']['erro'] is not None:
        continue
    conteudo['nfeProc']['requisicao'] = req
    lista_nfce.loc[i, 'resposta'] = enderecos.replace_one({'requisicao': req}, conteudo['nfeProc'], upsert=True)
    print(i, lista_nfce.loc[i, 'resposta'].raw_result)
