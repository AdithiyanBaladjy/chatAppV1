import json
fields_array=None
with open('fields_array.json','r') as f:
    fields_array=json.load(f)
op_json=dict()
for f in fields_array:
    op_json[f["displayLabel"].lower()]=f["apiName"]
with open("out.json",'w') as f:
    json.dump(op_json,f)