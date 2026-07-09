import re

text = "Glucose \n 108.00"

values1 = {}
match1 = re.search(r"Glucose.*?(\d+(\.\d+)?)", text, re.IGNORECASE)
if match1:
    values1['Glucose'] = float(match1.group(1))

values2 = {}
match2 = re.search(r"Glucose.*?(\d+(\.\d+)?)", text, re.IGNORECASE | re.DOTALL)
if match2:
    values2['Glucose'] = float(match2.group(1))

print("WITHOUT DOTALL:", values1)
print("WITH DOTALL:", values2)
