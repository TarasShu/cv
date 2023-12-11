from datetime import datetime
import json
import os
import glob

import os
import json

import os
import json
from datetime import datetime

json_folder_path = "/workspaces/ole/docs/json_for_pravo/"
json_files = os.listdir(json_folder_path)

data = []

def process_data(data):
    question_pairs = len(data)
    
    if question_pairs > 0:
        first_date = data[0]['date']
        last_date = data[-1]['date']
        category = data[0]['category']  # Assuming 'category' is the same for all items in data
    else:
        first_date = None
        last_date = None
        category = None
    
    return category, question_pairs, first_date, last_date

def loadJsons(json_files):
    for file in json_files:
        if file.endswith(".json"):
            file_path = os.path.join(json_folder_path, file)
            
            with open(file_path, 'r') as json_file:
                json_data = json.load(json_file)
                for item in json_data:
                    item_date = datetime.strptime(item['date'], "%Y-%m-%d %H:%M:%S")
                    item['date'] = item_date.strftime("%m.%d")
                
                data.extend(json_data)
                
    return data

data = loadJsons(json_files)

category_data = {}  # Dictionary to store aggregated data by category

question_pairs = []

for item in data:
    category = item['category']
    category_data[category]['question_pairs'] += 1

    
    if category_data[category]['first_date'] is None:
        category_data[category]['first_date'] = item['date']
    else:
        category_data[category]['first_date'] = min(category_data[category]['first_date'], item['date'])
    
    if category_data[category]['last_date'] is None:
        category_data[category]['last_date'] = item['date']
    else:
        category_data[category]['last_date'] = max(category_data[category]['last_date'], item['date'])


data_to_visual = []


for category, data_proed in category_data.items():
    if data_proed['question_pairs'] > 15000:
        print(data_proed)
        data_proed['dates'] = data_proed['dates'][-15:]
        data_proed['question_pairs'] = 15

for category, data_proed in category_data.items():
    data_to_visual.append((category, data_proed['question_pairs'], data_proed['first_date'], data_proed['last_date']))
    print((category, data_proed['question_pairs'], data_proed['first_date'], data_proed['last_date']))

#with open("data_to_visual.json", 'w') as json_file:
#    json.dump(data_to_visual, json_file, ensure_ascii=False, indent=2)


