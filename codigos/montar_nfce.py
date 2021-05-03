import requests
import xmltodict
import pandas as pd

req1 = 'http://nfce.sefaz.pe.gov.br/nfce/consulta?p=26210406057223028009650220001344921222422632%7C2%7C1%7C1%7C94F1F3F3149DE3FCA81E5E1E38E71CA6EB8664DF'
# req2 = 'http://nfce.sefaz.pe.gov.br/nfce-web/consNfce?tp=C&chave=26210406057223028009650220001344921222422632&hash=4c8418abc2879f5cc2cea88c387b80df'
resposta1 = xmltodict.parse(requests.get(req1).content)
del req1
# resposta2 = xmltodict.parse(requests.get(req2).content)

# %%
lista_itens = resposta1['nfeProc']['proc']['nfeProc']['NFe']['infNFe']['det']
produtos = pd.DataFrame(map(lambda x: x['prod'], lista_itens))
ordem_produtos = pd.DataFrame(map(lambda x: x['@nItem'], lista_itens), columns=['@nItem'])
lista_impostos_v_total = list()
lista_impostos_ICMS = list()
lista_impostos_PIS = list()
lista_impostos_COFINS = list()
for item in lista_itens:
    imposto = item['imposto']
    lista_impostos_v_total.append({'vTotTrib': imposto['vTotTrib']})
    for it in imposto['ICMS'].keys():
        lista_impostos_ICMS.append(imposto['ICMS'][it])
    for it in imposto['PIS'].keys():
        lista_impostos_PIS.append(imposto['PIS'][it])
    for it in imposto['COFINS'].keys():
        lista_impostos_COFINS.append(imposto['COFINS'][it])

impostos_ICMS = pd.DataFrame(lista_impostos_ICMS)
impostos_PIS = pd.DataFrame(lista_impostos_PIS)
impostos_COFINS = pd.DataFrame(lista_impostos_COFINS)
impostos_total = pd.DataFrame(lista_impostos_v_total)
produtos_impostos = pd.concat((ordem_produtos, produtos, impostos_ICMS, impostos_PIS, impostos_COFINS,
                               impostos_total), axis=1)

del lista_impostos_v_total, lista_impostos_ICMS, lista_impostos_PIS, lista_impostos_COFINS
del impostos_ICMS, impostos_PIS, impostos_COFINS, impostos_total, ordem_produtos
del lista_itens, produtos, item, imposto, it

# %%
info_empresa = resposta1['nfeProc']['proc']['nfeProc']['NFe']['infNFe']['emit']
info_empresa_localidade = resposta1['nfeProc']['proc']['nfeProc']['NFe']['infNFe']['emit']['enderEmit']

empresa = pd.DataFrame([info_empresa])
empresa.drop(columns=['enderEmit'], inplace=True)
empresa_localidade = pd.DataFrame([info_empresa_localidade])

empresa_consolidado = pd.concat((empresa, empresa_localidade), axis=1)

del info_empresa, info_empresa_localidade, empresa, empresa_localidade
# %%
info_adicionais = resposta1['nfeProc']['proc']['nfeProc']['NFe']['infNFe']['ide']
adicionais = pd.DataFrame([info_adicionais])

del info_adicionais
# %%
lista_formas_pagamentos = resposta1['nfeProc']['proc']['nfeProc']['NFe']['infNFe']['pag']['detPag']

itens_pagamento = list()
for item in lista_formas_pagamentos:
    item_pagamento = dict(item.copy())
    if 'card' in item_pagamento:
        item_pagamento.update(item_pagamento.pop('card'))
    itens_pagamento.append(item_pagamento)

formas_pagamento = pd.DataFrame(itens_pagamento)

del lista_formas_pagamentos, item, item_pagamento, itens_pagamento


