import json
import pandas as pd
ip_js=None
with open('fields_array.json','r') as f:
    ip_js=json.load(f)
df=pd.DataFrame(ip_js)
print(df)
df.to_excel('ad_hoc.xlsx')