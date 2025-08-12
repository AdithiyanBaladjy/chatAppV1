import json
ip_json=None
with open('Layout_desk.json','r') as f:
    ip_json=json.load(f)
ip_sections=ip_json["sections"]
fields=[]
for s in ip_sections:
    current_s_fields=s["fields"]
    for f in current_s_fields:
        fields.append(f)
with open("fields_array.json",'w') as f:
    json.dump(fields,f)