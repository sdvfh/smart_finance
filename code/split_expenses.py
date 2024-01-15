import numpy as np
import pandas as pd


def compute_expenses(df, people):
    check_values = (
        lambda x: True
        if isinstance(x, int) or (isinstance(x, float) and not np.isnan(x))
        else False
    )

    item_with_values = pd.concat(
        [df[person].map(check_values) for person in people], axis=1
    ).any(axis=1)
    df.loc[df["Source"].isnull(), "Source"] = df.loc[df["Source"].isnull(), "Name"]

    df[people] = df[people].astype("string")

    df.loc[item_with_values, people] = df.loc[item_with_values, people].fillna("0")
    df.loc[~item_with_values, people] = df.loc[~item_with_values, people].fillna("E")

    for i, line in df.iterrows():
        receive_people_qty = (line[people] == "R").sum()
        send_people_qty = (line[people] == "E").sum()
        people_qty = receive_people_qty + send_people_qty
        if people_qty == 0:
            expense_sum = line[people].astype("float").sum()
            correct_division = (expense_sum == line["Value"]) or (expense_sum == 0)
            if not correct_division:
                raise ValueError(
                    f'Despesa "{line["Name"]!r}", linha {i + 2}, com valores discrepantes entre o total e o dividido.'
                )
            continue
        value_per_person = line["Value"] / people_qty
        if value_per_person > 0:
            value_to_receive = -value_per_person * send_people_qty / receive_people_qty
        else:
            value_to_receive = np.nan
        for person in people:
            if line[person] == "E":
                df.loc[i, person] = str(value_per_person)
            elif line[person] == "R":
                df.loc[i, person] = str(value_to_receive)
            else:
                df.loc[i, person] = "0"
    for person in people:
        df[person] = pd.to_numeric(df[person]).round(4)
    return df


df = pd.read_excel("expenses.xlsx", sheet_name="expenses")

fixed_columns = ["Name", "Value", "Source"]

people = df.columns.drop(fixed_columns).to_list()

df = compute_expenses(df, people)

df.to_excel("expenses_report.xlsx", sheet_name="expenses", index=False)

expenses_report_per_person = df[people].sum(axis=0).round(2).to_string()

print(expenses_report_per_person)

with open("expenses_report_per_person.txt", "w") as f:
    f.write(expenses_report_per_person)

input("Press Enter to continue...")
