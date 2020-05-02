import csv

filename = "bot/table.csv"
with open(filename, "r") as file:
    reader = csv.reader(file, delimiter=',')
    data = {int(x[0]): ",".join(x[1:]) for x in reader}


def get_table(effect_id):
    return data[effect_id] if effect_id in data else "Unknown"
