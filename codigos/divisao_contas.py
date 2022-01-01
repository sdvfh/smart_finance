import numpy as np
import pandas as pd
from itertools import combinations


# %%
def transformar_df(df, pessoas):
    df[pessoas] = df[pessoas].fillna('S')
    for i, linha in df.iterrows():
        pessoas_entrada = (linha[pessoas] == 'E').sum()
        pessoas_saida = (linha[pessoas] == 'S').sum()
        qtd_pessoas = pessoas_entrada + pessoas_saida
        valor_por_pessoa_saida = linha['Valor'] / qtd_pessoas
        if pessoas_entrada > 0:
            valor_por_pessoa_entrada = -valor_por_pessoa_saida * pessoas_saida / pessoas_entrada
        else:
            valor_por_pessoa_entrada = np.nan
        for pessoa in pessoas:
            valor_pessoa = 'valor_' + pessoa
            if valor_pessoa in df.columns:
                if not np.isnan(df.loc[i, valor_pessoa]):
                    continue
            if linha[pessoa] == 'S':
                df.loc[i, valor_pessoa] = valor_por_pessoa_saida
            elif linha[pessoa] == 'E':
                df.loc[i, valor_pessoa] = valor_por_pessoa_entrada
            else:
                df.loc[i, valor_pessoa] = 0
    return df


# %% itens
mes = 'jan'
ano = str(22)
diretorio = '/home/sergio/Documentos/repositorios/casa_inteligente/contas_casa/contas_casa_'

df = pd.read_excel(diretorio + mes + '_' + ano + '.xlsx', sheet_name='itens')
df_contas = pd.read_excel(diretorio + mes + '_' + ano + '.xlsx', sheet_name='contas')
pessoas = ['Ana', 'Camilla', 'Sérgio']
valor_pessoas = ['valor_' + pessoa for pessoa in pessoas]

# %%
df = transformar_df(df, pessoas)
df_contas = transformar_df(df_contas, pessoas)
df_detalhado = pd.concat((df, df_contas), ignore_index=True)
df_detalhado.loc[df_detalhado['Fonte'].isnull(), 'Fonte'] = df_detalhado.loc[df_detalhado['Fonte'].isnull(), 'Nome']
resultado = df_detalhado[valor_pessoas].sum()

# %%
df_pagamentos = df_detalhado[df_detalhado['Pagamento_boleto'] == 'X'].groupby('Fonte').sum()['Valor']
df_pagamentos = df_pagamentos.reset_index()

# %%
print(resultado.sum().round(2) == df_pagamentos['Valor'].sum().round(2))


# %%
def separar_contas(pessoas_espec, resultado, df):
    contas = df.values.tolist()
    valores = pd.DataFrame(resultado).T
    pessoas = list(pessoas_espec.keys())
    valores.columns = pessoas

    for n in range(len(contas)):
        for conta in combinations(contas, n):
            print(n, calculo_separar_contas(pessoas_espec, pessoas, 0, conta))
    return contas


def calculo_separar_contas(pessoas_espec, pessoas, pessoa_index, df, lista_final=None):
    if len(pessoas_espec) == pessoa_index:
        return None
    if lista_final is None:
        lista_final = dict()
    nomes_contas_espec = pessoas_espec[pessoas[pessoa_index]]
    for n in range(len(df)):
        for lista_conta in combinations(df, n):
            nomes_contas = list(map(lambda x: x[0], lista_conta))
            if all(elem in nomes_contas for elem in nomes_contas_espec):
                print(lista_conta)
                df_novo = df.copy()
                for conta in lista_conta:
                    df_novo.remove(conta)
                if len(df_novo) == 0:
                    lista_final.update({pessoas[pessoa_index]: lista_conta})
                    return lista_final
                else:
                    return calculo_separar_contas(pessoas_espec, pessoas, pessoa_index + 1, df_novo, lista_final)


# pessoas_espec = dict(zip(pessoas, [['dízimo'], ['oi fibra', 'unimed'], ['netflix']]))
# pessoas_espec = dict(zip(pessoas, [[], ['oi fibra', 'unimed'], ['netflix']]))
# print(separar_contas(pessoas_espec, resultado, df_pagamentos))

# %%
lista = list()
qtd_contas1 = len(df_contas)

contas_espec1 = ['dízimo']
# contas_espec1.append('água')
# contas_espec1.append('hiper')
# contas_espec1.append('itaú')
contas_espec2 = ['oi fibra', 'unimed']
contas_espec3 = ['netflix']
contas_espec3.append('água')
for i in range(qtd_contas1):
    for item1 in combinations(df_pagamentos.values, i + 1):
        df_contas1_atual = pd.DataFrame(item1, columns=['Nome', 'Valor'])
        nome1 = '_'.join(df_contas1_atual['Nome'].values.tolist())
        valor1 = df_contas1_atual['Valor'].sum()

        if df_contas1_atual[df_contas1_atual['Nome'].isin(contas_espec1)].shape[0] != len(contas_espec1):
            continue

        df_contas2 = df_contas[~df_contas['Nome'].isin(df_contas1_atual['Nome'])]
        qtd_contas2 = len(df_contas2)
        if qtd_contas2 == 0:
            continue
        for o in range(qtd_contas2):
            for item2 in combinations(df_contas2[['Nome', 'Valor']].values, o + 1):
                df_contas2_atual = pd.DataFrame(item2, columns=['Nome', 'Valor'])
                nome2 = '_'.join(df_contas2_atual['Nome'].values.tolist())
                valor2 = df_contas2_atual['Valor'].sum()
                # if valor2 < resultado_conta[1]:
                #     continue

                if df_contas2_atual[df_contas2_atual['Nome'].isin(contas_espec2)].shape[0] != len(contas_espec2):
                    continue

                df_contas3 = df_contas2[~df_contas2['Nome'].isin(df_contas2_atual['Nome'])]

                if df_contas3[df_contas3['Nome'].isin(contas_espec3)].shape[0] != len(contas_espec3):
                    continue

                if len(df_contas3) == 0:
                    continue
                nome3 = '_'.join(df_contas3['Nome'].values.tolist())
                valor3 = df_contas3['Valor'].sum()
                valor_min = (valor1 - resultado[0]) ** 2 + (valor2 - resultado[1]) ** 2 + (valor3 - resultado[2]) ** 2

                lista.append((nome1, valor1, nome2, valor2, nome3, valor3, valor_min))

df_final = pd.DataFrame(lista)
df_final = df_final.sort_values(6)
df_final = df_final.reset_index(drop=True)

df_final = df_final[df_final[[1, 3, 5]].sum(axis=1).round(2) == resultado.sum().round(2)].reset_index(drop=True)

for i, valor_pessoa in enumerate(valor_pessoas):
    print(valor_pessoa, resultado[valor_pessoa] - df_final.loc[0, 2 * i + 1])

# %%
colunas = ['Nome', 'Valor', 'Parcelas', 'Início_Parcelas', 'Fonte'] + valor_pessoas
df_detalhado[colunas].to_excel(diretorio + mes + '_' + ano + '_relatorio.xlsx')
