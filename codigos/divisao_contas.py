import numpy as np
import pandas as pd


# %%
def calcular_despesas(df):
    checar_valores = lambda x: True if isinstance(x, int) or (isinstance(x, float) and not np.isnan(x)) else False
    itens_com_valores = pd.concat([df[pessoa].map(checar_valores) for pessoa in pessoas], axis=1).any(axis=1)
    df.loc[df['Fonte'].isnull(), 'Fonte'] = df.loc[df['Fonte'].isnull(), 'Nome']
    df.loc[itens_com_valores, pessoas] = df.loc[itens_com_valores, pessoas].fillna(0)
    df.loc[~itens_com_valores, pessoas] = df.loc[~itens_com_valores, pessoas].fillna('E')
    for i, linha in df.iterrows():
        pessoas_para_receber = (linha[pessoas] == 'R').sum()
        pessoas_para_enviar = (linha[pessoas] == 'E').sum()
        qtd_pessoas = pessoas_para_receber + pessoas_para_enviar
        if qtd_pessoas == 0:
            continue
        valor_por_pessoa = linha['Valor'] / qtd_pessoas
        if pessoas_para_receber > 0:
            valor_para_receber = -valor_por_pessoa * pessoas_para_enviar / pessoas_para_receber
        else:
            valor_para_receber = np.nan
        for pessoa in pessoas:
            if linha[pessoa] == 'E':
                df.loc[i, pessoa] = valor_por_pessoa
            elif linha[pessoa] == 'R':
                df.loc[i, pessoa] = valor_para_receber
            else:
                df.loc[i, pessoa] = 0
    for pessoa in pessoas:
        df[pessoa] = pd.to_numeric(df[pessoa])
    return df


# %%
data = '22_01'
arquivo = f'/home/sergio/Documentos/repositorios/casa_inteligente/contas_casa/contas_{data}.xlsx'
pessoas = ['Ana', 'Camilla', 'Sérgio']
boletos = ['hiper', 'itaú', 'marisa']

# %%
df_itens = pd.read_excel(arquivo, sheet_name='itens')
df_contas = pd.read_excel(arquivo, sheet_name='contas')
boletos += df_contas['Nome'].drop_duplicates().to_list()
df_detalhado = pd.concat((df_itens, df_contas), ignore_index=True)
del df_itens, df_contas

df_detalhado = calcular_despesas(df_detalhado)
valores_por_pessoa = df_detalhado[pessoas].sum()
df_pagamentos = df_detalhado[df_detalhado['Fonte'].isin(boletos)].groupby('Fonte').sum()[['Valor'] + pessoas]
df_pagamentos = df_pagamentos.reset_index()

if valores_por_pessoa.sum().round(2) == df_pagamentos['Valor'].sum().round(2):
    print('Os valores por pessoa e os boletos batem.')
else:
    print('Os valores por pessoa e os boletos NÃO batem. Favor, corrigir.')

# %%
df_exportar = df_detalhado[['Nome', 'Valor'] + pessoas].copy()
df_exportar[['Valor'] + pessoas] = df_exportar[['Valor'] + pessoas].round(2)
total = df_exportar.sum()
total['Nome'] = 'Total'
df_exportar = df_exportar.append(total, ignore_index=True)
del total
df_exportar.to_excel(arquivo[:-5] + '_relatorio.xlsx', index=False)

# %%
fixos = [['Ana'], ['dízimo'],
         ['Camilla'], ['oi fibra', 'unimed'],
         ['Sérgio'], ['netflix']]

