from selenium import webdriver
import selenium
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import pandas as pd
import time
import json

sign_in_url="https://ucrm.unionbankofindia.co.in/crm/org60009764661/tab/Home/begin"
desk_create_ticket_url="https://service.unionbankofindia.co.in/agent/ccudesk/union-bank-of-india/tickets/new"
def find_drop_down_ind(query,options_list):
    for i in range(len(options_list)):
        if options_list[i].lower()==query.lower():
            return i
    return -1
def sign_in(driver,uname,password,sign_in_url):
    driver.get(sign_in_url)
    driver.find_element("id", "login_id").send_keys(uname)
    driver.find_element("id","nextbtn").click()
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "password"))).click()
    driver.find_element("id", "password").send_keys(password)
    driver.find_element("id","nextbtn").click()

def open_desk_create_ticket_for_test(driver,url):
    driver.execute_script("window.open('');")
    driver.switch_to.window(driver.window_handles[-1])
    driver.get(url)
    WebDriverWait(driver,20).until(EC.element_to_be_clickable((By.ID,"ZD_17"))).click()
    # WebDriverWait(driver,20).until(EC.element_to_be_clickable((By.XPATH,"//body"))).click()
    WebDriverWait(driver,20).until(EC.element_to_be_clickable((By.ID,"ZD_17"))).click()

def field_name_to_cf_name(field_name):
    field_name_words=field_name.lower().split(" ")
    return '_'.join(''.join('_'.join(field_name_words).split(".")).split('/'))

def set_value_in_drop_down(driver,field_name,value_to_set):
    try:
        cf_name=field_name_to_cf_name(field_name)
        cf_box=driver.find_element(By.XPATH, "//div[@data-id='cf_"+cf_name+"']")
        # print("cf area element is",cf_area_box.get_attribute('innerHTML'))
        cf_box.click()
        type_options=driver.find_elements(By.XPATH,"//div[@data-id='cf_"+cf_name+"_Options']/li/div[1]")
        type_options=[c.text for c in type_options]
        print_log("value tbs"+str(value_to_set)+"options for cf:"+cf_name+" are"+str(type_options))
        req_ind=find_drop_down_ind(value_to_set,type_options)
        if req_ind==-1:
            try:
                #check if the drop-down has a search element
                cf_name=field_name_to_cf_name(field_name)
                cf_search_box=driver.find_element(By.XPATH, "//input[@data-id='cf_"+cf_name+"_search']")
                print_log("Searching value"+str(value_to_set))
                cf_search_box.click()
                cf_search_box.send_keys(value_to_set)
                cf_result_list=driver.find_elements(By.XPATH,"//div[@data-id='cf_"+cf_name+"_Options']/li")
                search_results=[c.text for c in cf_result_list]
                print_log("Search results:"+str(search_results))
                req_ind=find_drop_down_ind(value_to_set,search_results)
                if req_ind==-1:
                    #close the opened drop down, return -1
                    cf_box=driver.find_element(By.XPATH, "//div[@data-id='cf_"+cf_name+"']")
                    # print("cf area element is",cf_area_box.get_attribute('innerHTML'))
                    cf_box.click()
                    return -1
                else:
                    #click the required result and return 1
                    req_li=driver.find_element(By.XPATH,"//div[@data-id='cf_"+cf_name+"_Options']/li["+str(req_ind+1)+"]")
                    req_li.click()
                    return 1
            except:
                #If no search box is present, return -1, closing the dropdown
                cf_box=driver.find_element(By.XPATH, "//div[@data-id='cf_"+cf_name+"']")
                # print("cf area element is",cf_area_box.get_attribute('innerHTML'))
                cf_box.click()
                return -1
        else:
            req_li=driver.find_element(By.XPATH,"//div[@data-id='cf_"+cf_name+"_Options']/li["+str(req_ind+1)+"]")
            req_li.click()
        return 1
    except:
        cf_name=field_name_to_cf_name(field_name)
        cf_box=driver.find_element(By.XPATH, "//div[@data-id='cf_"+cf_name+"']")
        # print("cf area element is",cf_area_box.get_attribute('innerHTML'))
        cf_box.click()
        return -1

def get_api_name(label_name):
    #check if out.json is properly loaded - production readiness
    try:
        result=api_names_dict[label_name]
        return result
    except:
        return -1

def isFieldMandatory(driver,field_name):
    if field_name=="Loan A/c No.":
        pass

    api_name=get_api_name(field_name.lower())
    if api_name==-1:
        return False
    try:
        cf_box=driver.find_element(By.XPATH, "//label[@data-id='"+api_name+"_label_mandatory']")
        return True
    except:
        return False

def checkFieldVisibility(driver,field_name):
    if field_name=="Loan A/c No.":
        pass

    api_name=get_api_name(field_name.lower())
    if api_name==-1:
        return False
    try:
        cf_box=driver.find_element(By.XPATH, "//div[@data-id='"+api_name+"_field']")
        return True
    except:
        return False

def print_log(log_msg):
    global logs
    logs+=log_msg
    logs+='\n'

def out_log():
    with open("logs.txt","w") as f:
        f.write(logs)
    
username = "ubideskdev1@unionbankcrm.co.in"
password = "Code@ubi1234"
#Ubi@12345
logs=""
# username = "ubitest8@gmail.com"
# password = "Ubi@1947"
req_type = 'Complaint'
# initialize the Chrome driver
driver = webdriver.Chrome("chromedriver")
sign_in(driver,username,password,sign_in_url)
open_desk_create_ticket_for_test(driver,desk_create_ticket_url)
# driver.get("https://service.unionbankofindia.co.in/agent/ccudesk/union-bank-of-india/tickets/new")

# driver.get("https://ucrm.unionbankofindia.co.in/crm/org60009764661/tab/Leads/create?layoutId=1068000000000167")
# driver.find_element("id","visible_leads").click()


#driver script
api_names_dict=None
with open("out.json","r") as f:
    api_names_dict=json.load(f)
input_df=pd.read_excel("input-5.xlsx",sheet_name="Sheet1")
conditional_columns=["TYPE","AREA","SUB_AREA","CHILD_SUB_AREA"]
#reading the input excel line by line
test_results=[] #Layout rule test result
reasons=[]  #Layout rule test failed reason
mandatory_test_results=[]   #mandatory field test result
mandatory_test_reasons=[]   #mandatory field test failed reason
row_ind=0
for _i,row in input_df.iterrows():
    reasons.append("")
    test_results.append("")
    mandatory_test_results.append("")
    mandatory_test_reasons.append("")
    test_case_ready=True
    print_log("Test case no:"+str(row_ind+1))
    for c in conditional_columns:
        test_case_col_val=row[c]
        if test_case_col_val!="" and test_case_col_val!=None and not pd.isna(test_case_col_val):
            ret=set_value_in_drop_down(driver,c,test_case_col_val.strip())
            time.sleep(0.2)
            if ret==-1:
                reasons[row_ind]+="{0} not found in cf:{1}".format(test_case_col_val,c)
                mandatory_test_reasons[row_ind]+="{0} not found in cf:{1}".format(test_case_col_val,c)
                test_case_ready=False
                break
    if test_case_ready:
        if not pd.isna(row["Fields to be shown"]):
            fields_to_be_shown=row["Fields to be shown"].split(",")
            test_case_success=True
            for field in fields_to_be_shown:
                if field=='':
                    continue
                shown=checkFieldVisibility(driver,field.strip())
                if(not shown):
                    test_case_success=False
                    reasons[row_ind]+=", cf:{0} is not visible".format(field)
        if test_case_success:
            test_results[row_ind]="Success"
        else:
            test_results[row_ind]="Failure"
        
        #Mandatory fields testing
        if not pd.isna(row["Mandatory fields"]):
            mandatory_fields=row["Mandatory fields"].split(",")
            mandatory_test_case_success=True
            for field in mandatory_fields:
                if field=='':
                    continue
                isMandatory=isFieldMandatory(driver,field.strip())
                if(not isMandatory):
                    mandatory_test_case_success=False
                    mandatory_test_reasons[row_ind]+=", cf:{0} is not mandatory".format(field)
        if mandatory_test_case_success:
            mandatory_test_results[row_ind]="Success"
        else:
            mandatory_test_results[row_ind]="Failure"
    else:
        test_results[row_ind]="Failure"
        mandatory_test_results[row_ind]="Failure"

    print(row_ind,". Test case completed, result:\t",reasons[row_ind])
    row_ind+=1
input_df["Layout Test Result"]=test_results
input_df["Layout Test Failed Reason"]=reasons
input_df["Mandatory Test Result"]=mandatory_test_results
input_df["Mandatory Test Failed Reason"]=mandatory_test_reasons
input_df.to_excel("output.xlsx")
driver.close()
out_log()
print("read xlsx is",input_df)
