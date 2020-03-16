import csv

data = {}
filename = "bot/table.csv"
with open(filename, "r") as file:
    #[print(y.split(" ", 1)) for x in file.readlines() if x == "" or ord(x[0]) != 12 for y in re.split(r" +(\d{4}.*)", x) if y != '\n']
    #effects = {int(y.split(" ", 1)[0]): y.split(" ", 1)[1].strip() for x in file.readlines() if x == "" or ord(x[0]) != 12 for y in re.split(r" +(\d{4}.*)", x)  if y != '\n'}
    #[ofile.write(f"{x},{effects[x]}\n") for x in sorted(effects.keys())]
    #pfr = PyPDF2.PdfFileReader(file)
    #[ofile.write(x.extractText()) for x in pfr.pages[4:-1]]
    reader = csv.reader(file, delimiter=',')
    data = {int(x[0]): ",".join(x[1:]) for x in reader}

def get_table(effect_id):
	return data[effect_id] if effect_id in data else "Unknown"