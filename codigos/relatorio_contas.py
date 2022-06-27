import shutil

import numpy as np
import pandas as pd
from pandas.tseries.offsets import DateOffset

# %% definição de funções
caminho = (
    lambda data: f"/home/sergio/Documentos/repositorios/casa_inteligente/contas_casa/contas_{data}.xlsx"
)


def calcular_despesas(df, pessoas, boletos):
    checar_valores = (
        lambda x: True
        if isinstance(x, int) or (isinstance(x, float) and not np.isnan(x))
        else False
    )
    itens_com_valores = pd.concat(
        [df[pessoa].map(checar_valores) for pessoa in pessoas], axis=1
    ).any(axis=1)
    df.loc[df["Fonte"].isnull(), "Fonte"] = df.loc[df["Fonte"].isnull(), "Nome"]
    df.loc[itens_com_valores, pessoas] = df.loc[itens_com_valores, pessoas].fillna(0)
    df.loc[~itens_com_valores, pessoas] = df.loc[~itens_com_valores, pessoas].fillna(
        "E"
    )

    for i, linha in df.iterrows():
        pessoas_para_receber = (linha[pessoas] == "R").sum()
        pessoas_para_enviar = (linha[pessoas] == "E").sum()
        qtd_pessoas = pessoas_para_receber + pessoas_para_enviar
        if qtd_pessoas == 0:
            soma_pessoas = np.round(linha[pessoas].sum(), 2)
            divisao_correta = (
                linha["Fonte"] in boletos and soma_pessoas == linha["Valor"]
            ) or (soma_pessoas == 0)
            if not divisao_correta:
                raise ValueError(
                    f'Despesa "{linha["Nome"]}", linha {i + 2}, com valores discrepantes entre o total e o dividido.'
                )
            continue
        valor_por_pessoa = linha["Valor"] / qtd_pessoas
        if pessoas_para_receber > 0:
            valor_para_receber = (
                -valor_por_pessoa * pessoas_para_enviar / pessoas_para_receber
            )
        else:
            valor_para_receber = np.nan
        for pessoa in pessoas:
            if linha[pessoa] == "E":
                df.loc[i, pessoa] = valor_por_pessoa
            elif linha[pessoa] == "R":
                df.loc[i, pessoa] = valor_para_receber
            else:
                df.loc[i, pessoa] = 0
    for pessoa in pessoas:
        df[pessoa] = pd.to_numeric(df[pessoa])
    return df


# %% definições de variáveis
data = "22_06"
arquivo = caminho(data)
fixos = [
    ["Ana", ["dízimo", "hiper"]],
    ["Camilla", ["oi fibra", "unimed_camilla", "água"]],
    ["Sérgio", ["netflix", "unimed_ana"]],
]
boletos = ["hiper", "itaú", "marisa"]

# %% cálculo das despesas
pessoas = [fixo[0] for fixo in fixos]
df_itens = pd.read_excel(arquivo, sheet_name="itens")
df_contas = pd.read_excel(arquivo, sheet_name="contas")
boletos += df_contas["Nome"].drop_duplicates().to_list()
df_detalhado = pd.concat((df_itens, df_contas), ignore_index=True)
del df_itens, df_contas

df_detalhado = calcular_despesas(df_detalhado, pessoas, boletos)
valores_por_pessoa = df_detalhado[pessoas].sum().sort_values()
df_pagamentos = (
    df_detalhado[df_detalhado["Fonte"].isin(boletos)]
    .groupby("Fonte")
    .sum()[["Valor"] + pessoas]
)
df_pagamentos = df_pagamentos.reset_index().sort_values("Valor")

diff = np.abs(
    np.round(
        valores_por_pessoa.sum().round(2) - df_pagamentos["Valor"].sum().round(2), 2
    )
)
assert (
    diff == 0
), f"Os valores por pessoa e os boletos NÃO batem. A diferença é de {diff}. Favor, corrigir."

# %% Distribuição dos boletos
boletos_pagamento = {}
df_pagamentos_tmp = df_pagamentos.copy()

for pessoa, boletos in fixos:
    boletos_pagamento.update(
        {
            pessoa: df_pagamentos_tmp.loc[
                df_pagamentos_tmp["Fonte"].isin(boletos), ["Fonte", "Valor"]
            ]
        }
    )
    df_pagamentos_tmp = df_pagamentos_tmp[~df_pagamentos_tmp["Fonte"].isin(boletos)]


for pessoa in pessoas:
    drop_indexes = []
    for i, linha in df_pagamentos_tmp.iterrows():
        if (
            boletos_pagamento[pessoa]["Valor"].sum() + linha["Valor"]
            <= valores_por_pessoa[pessoa]
        ) or pessoa == pessoas[-1]:
            boletos_pagamento[pessoa] = boletos_pagamento[pessoa].append(
                linha[["Fonte", "Valor"]]
            )
            drop_indexes.append(i)
        else:
            break
    df_pagamentos_tmp = df_pagamentos_tmp.drop(index=drop_indexes)
del df_pagamentos_tmp

valor = 0
for pessoa in pessoas:
    valor += boletos_pagamento[pessoa]["Valor"].sum()
diff = np.round(np.abs(np.round(valor, 2) - valores_por_pessoa.sum().round(2)), 2)

assert (
    diff == 0
), f"Os valores de cada pessoa e o valor total NÃO batem. A diferença é de {diff}. Favor, corrigir."

for pessoa in pessoas:
    diferenca = valores_por_pessoa[pessoa] - boletos_pagamento[pessoa]["Valor"].sum()
    print("\n")
    print(f"-------- {pessoa} --------")
    # print('Despesa real: ', np.round(valores_por_pessoa[pessoa].round(2) - outras_despesas, 2))
    print("Despesa atual: ", valores_por_pessoa[pessoa].round(2))
    print(boletos_pagamento[pessoa].sort_values("Valor").reset_index(drop=True))
    print("Para transferir:", diferenca.round(2))

del pessoa, diferenca, i, linha, valor, boletos

# %% geração do relatório
df_exportar = df_detalhado[["Nome", "Valor"] + pessoas].copy()
df_exportar[["Valor"] + pessoas] = df_exportar[["Valor"] + pessoas].round(2)
total = df_exportar.sum()
total["Nome"] = "Total"
df_exportar = df_exportar.append(total, ignore_index=True)
df_exportar.to_excel(arquivo[:-5] + "_relatorio.xlsx", index=False)
del total, df_exportar, pessoas

# %% Gerar a planilha para o próximo mês, contando apenas com os itens parcelados e fixos
data = data.split("_")
data = pd.Timestamp(year=2000 + int(data[0]), month=int(data[1]), day=1)
data += DateOffset(months=1)
data = data.strftime("%y_%m")
arquivo_futuro = caminho(data)
shutil.copyfile(arquivo, arquivo_futuro)

df_itens = pd.read_excel(arquivo_futuro, sheet_name="itens")
df_contas = pd.read_excel(arquivo_futuro, sheet_name="contas")
df_itens["Parcelas"] -= 1
df_itens = df_itens[df_itens["Parcelas"].notnull() & df_itens["Parcelas"] != 0]
df_itens.loc[df_itens["Parcelas"] < 0, "Parcelas"] = -1

with pd.ExcelWriter(arquivo_futuro) as writer:
    df_itens.to_excel(writer, sheet_name="itens", index=False)
    df_contas.to_excel(writer, sheet_name="contas", index=False)
