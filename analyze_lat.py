f = open("../simple_lat.xml", "r+")
lines = f.readlines()
lats = {"TransactionType=\"NewOrder\"": [], 
"TransactionType=\"Payment\"": [],
"TransactionType=\"OrderStatus\"": [],
"TransactionType=\"Delivery\"": [],
"TransactionType=\"StockLevel\"": []}
for line in lines:
    es = line.split(" ")
    lat = es[1].split("=")[1].replace("\"", "")
    lats[es[0]].append(1000*float(lat))

for key,value in lats.items():
    value.sort()
    sum = 0
    for v in value:
        sum += v
    num = len(value)
    print(f"{key} : {sum/num}/{value[int(num/2)]}/{value[int((9*num)/10)]}/{value[int((99*num)/100)]}")

