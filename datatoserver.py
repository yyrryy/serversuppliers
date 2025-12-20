import requests as req
import csv
import json
from datetime import datetime
start = datetime.today().strftime('%d/%m/%Y %H:%M:%S')
with open('C:/backups/backup.csv', 'r') as file:
    reader = csv.DictReader(file)
    data_list = [row for row in reader]

# Prepare the data for the HTTP POST request
#products=[i for i in data_list if int(i['stocktotal'])<=5]
articles=0
referr=[]
for i in data_list:
    if i['ref']=='' or i['ref'].startswith('.'):
        pass
    else:
        try:
            print('>>>', i['ref'], i['stocktotal'])
            res=req.get('http://157.245.74.156/products/updatepdctdata', {
            'password':'gadwad123',
            'id':i['id'],
            'ref':i['ref'],
            'stocktotal':i['stocktotal'],
            'image':i['image']
            })
            articles+=1
        except Exception as e:
            print('>>>>> err', e)
            referr.append((i['id'], i['ref']))


end = datetime.today().strftime('%d/%m/%Y %H:%M:%S')
with open('errorsref.txt', 'a') as ff:
    print('--------------------------------------', file=ff)
    print(start, ' - ', end, file=ff)
    print(f">>> articles: {articles}", file=ff)
    print('ERRORS', file=ff)
    print(f">>> errr: {referr}",  file=ff)
# req.get('http://167.99.39.116/products/addclient', {
# 'name':'ALOUROBA PA',
# 'code':'180120',
# 'ice':'',
# 'city':'SAFI',
# 'represent_id':7,
# 'region':'s1',
# 'address':''
# })
