from selenium import webdriver
import selenium
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
import pandas as pd
import time
import json
#Global variables
sign_in_url="sign_in_url"
desk_create_ticket_url="create_ticket_url"
api_names_dict=None
with open("out.json","r") as f:
    api_names_dict=json.load(f)

def get_api_name(label_name):
    #check if out.json is properly loaded - production readiness
    try:
        result=api_names_dict[label_name]
        return result
    except:
        return -1

def print_log(log_msg):
    print(log_msg)
    global logs
    logs+=log_msg
    logs+='\n'

#get list of values of a picklist field
def get_available_fields(field,df):
    return list(df[field])

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
    if "*" in field_name:
        try:
            field_name=field_name[:-1]
            cf_name=get_api_name(field_name.lower())
            if cf_name==-1:
                # out_log("Could not find API name for field: "+field_name)
                return -2
            cf_box=driver.find_element(By.XPATH, "//div[@data-id='property("+field_name+")']")
            # data-id for nested dropdown is identified using @data-id='property(<field label>)'
            cf_box.click()
            cf_search_box=driver.find_element(By.XPATH, "//input[@data-id='property("+field_name+")_search']")
            try:
                cf_search_box_clear_icon=driver.find_element(By.XPATH, "button[@data-id='property("+field_name+")_search_ClearIcon']")
                # data-id for nested dropdown is identified using //button[@data-id='property(<field label>)_search_ClearIcon']
                cf_search_box_clear_icon.click()
            except:
                pass
            cf_search_box.click()
            cf_search_box.send_keys(value_to_set)
            time.sleep(0.1)
            cf_result_list=driver.find_elements(By.XPATH,"//div[@data-id='property("+field_name+")_suggestions']//div[@data-id='CardContent']/li/div[1]")
            search_results=[c.text for c in cf_result_list]
            print_log("Search results:"+str(search_results))
            req_ind=find_drop_down_ind(value_to_set,search_results)
            if req_ind==-1:
                #close the opened drop down, return -1
                cf_box=driver.find_element(By.XPATH, "//div[@data-id='property("+field_name+")']")
                # print("cf area element is",cf_area_box.get_attribute('innerHTML'))
                cf_box.click()
                return -1
            else:
                #click the required result and return 1
                req_li=driver.find_element(By.XPATH,"//div[@data-id='property("+field_name+")_suggestions']//div[@data-id='CardContent']/li["+str(req_ind+1)+"]")
                req_li.click()
                return 1
        except:
            try:
                cf_name=get_api_name(field_name.lower())
                cf_box=driver.find_element(By.XPATH, "//div[@data-id='property("+field_name+")']")
                # print("cf area element is",cf_area_box.get_attribute('innerHTML'))
                cf_box.click()
            except:
                return -1
            return -1
        #field is a nested drop-down
              
    try:
        # cf_name=field_name_to_cf_name(field_name)
        cf_name=get_api_name(field_name.lower())
        if cf_name==-1:
            # out_log("Could not find API name for field: "+field_name)
            return -2
        cf_box=driver.find_element(By.XPATH, "//div[@data-id='"+cf_name+"']")
        # data-id for nested dropdown is identified using @data-id='property(<field label>)'

        # print("cf area element is",cf_area_box.get_attribute('innerHTML'))
        cf_box.click()
        type_options=driver.find_elements(By.XPATH,"//div[@data-id='"+cf_name+"_Options']/li/div[1]")
        # data-id for nested dropdown is identified using1 //div[@data-id='property(<field label>)_suggestions']//div[@data-id='CardContent']/li/div[1]
        
        type_options=[c.text for c in type_options]
        print_log("value tbs"+str(value_to_set)+"options for cf:"+cf_name+" are"+str(type_options))
        req_ind=find_drop_down_ind(value_to_set,type_options)
        if req_ind==-1:
            try:
                #check if the drop-down has a search element
                cf_name=get_api_name(field_name)
                cf_search_box=driver.find_element(By.XPATH, "//input[@data-id='"+cf_name+"_search']")
                # data-id for nested dropdown is identified using //input[@data-id='property(<field label>)_search']

                try:
                    cf_search_box_clear_icon=driver.find_element(By.XPATH, "//button[@data-id='"+cf_name+"_search_ClearIcon']")
                    # data-id for nested dropdown is identified using //button[@data-id='property(<field label>)_search_ClearIcon']
                    cf_search_box_clear_icon.click()
                except:
                    pass
                print_log("Searching value"+str(value_to_set))
                cf_search_box.click()
                cf_search_box.send_keys(value_to_set)
                time.sleep(0.1)
                cf_result_list=driver.find_elements(By.XPATH,"//div[@data-id='"+cf_name+"_Options']/li/div[1]")
                #//div[@data-id='property(<field label>)_suggestions']//div[@data-id='CardContent']/li/div[1]
                search_results=[c.text for c in cf_result_list]
                print_log("Search results:"+str(search_results))
                req_ind=find_drop_down_ind(value_to_set,search_results)
                if req_ind==-1:
                    #close the opened drop down, return -1
                    cf_box=driver.find_element(By.XPATH, "//div[@data-id='"+cf_name+"']")
                    # print("cf area element is",cf_area_box.get_attribute('innerHTML'))
                    cf_box.click()
                    return -1
                else:
                    #click the required result and return 1
                    req_li=driver.find_element(By.XPATH,"//div[@data-id='"+cf_name+"_Options']/li["+str(req_ind+1)+"]")
                    req_li.click()
                    return 1
            except:
                #If no search box is present, return -1, closing the dropdown
                cf_box=driver.find_element(By.XPATH, "//div[@data-id='"+cf_name+"']")
                # print("cf area element is",cf_area_box.get_attribute('innerHTML'))
                cf_box.click()
                return -1
        else:
            req_li=driver.find_element(By.XPATH,"//div[@data-id='"+cf_name+"_Options']/li["+str(req_ind+1)+"]")
            req_li.click()
        return 1
    except:
        try:
            cf_name=get_api_name(field_name.lower())
            cf_box=driver.find_element(By.XPATH, "//div[@data-id='"+cf_name+"']")
            # print("cf area element is",cf_area_box.get_attribute('innerHTML'))
            cf_box.click()
        except:
            return -1
        return -1

def check_values_in_drop_down(driver,field_name,values_to_check,total_values,test_case_comment_str):
    values_not_to_be=[]
    case_success=True
    for v in total_values:
        if not pd.isna(v) and v.strip() not in values_to_check:
            values_not_to_be.append(v)
    field_api_name=get_api_name(field_name.lower())
    if field_api_name==-1:
        # out_log("Could not find API name for field: "+field_name)
        if test_case_comment_str=="":
            test_case_comment_str="API name could not be found for the field: "+field_name+"\n"
        else:
            test_case_comment_str+=", API name could not be found for the field: "+field_name+"\n"
        return {'respCode':False,'comment':test_case_comment_str}

    #find the drop-down to be clicked
    #if not found, append box not found msg to be appended to comment str
    #if found, click the drop down, find if the values to check are there in the options one by one
    #if not there, check if the dropdown contains a search bar
    #if there is a search bar, check if the value is return
    try:
        cf_box=driver.find_element(By.XPATH, "//div[@data-id='"+field_api_name+"']")
    except:
        return {"respCode":False,"comment":"Field: "+field+" could not be found."}
    
    # print("cf area element is",cf_area_box.get_attribute('innerHTML'))
    cf_box.click()
    type_options=driver.find_elements(By.XPATH,"//div[@data-id='"+field_api_name+"_Options']/li/div[1]")
    type_options=[c.text.strip().lower() for c in type_options]
    values_len=len(values_to_check)
    temp_ls=[]
    for ind in range(0,values_len):
        try:
            if values_to_check[ind].strip().lower() in type_options:
                pass
            else:
                temp_ls.append(values_to_check[ind])
        except:
            break
    values_to_check=temp_ls
        
    if len(values_to_check)>0:
        #search all elements left in values to check
        ind=-1
        while(True):
        # for ind in range(len(values_to_check)):
            ind+=1
            if(ind>=len(values_to_check)):
                break
            try:
                v=values_to_check[ind].strip()
            except:
                break
            try:
                try:
                    cf_search_box_clear_icon=driver.find_element(By.XPATH, "//button[@data-id='"+field_api_name+"_search_ClearIcon']")
                    cf_search_box_clear_icon.click()
                except:
                    pass
                cf_search_box=driver.find_element(By.XPATH, "//input[@data-id='"+field_api_name+"_search']")
            except:
                break
            cf_search_box.click()
            cf_search_box.send_keys(v.strip())
            time.sleep(0.1)
            cf_result_list=driver.find_elements(By.XPATH,"//div[@data-id='"+field_api_name+"_Options']/li/div[1]")
            search_results=[c.text.strip().lower() for c in cf_result_list]
            if v.strip().lower() in search_results:
                values_to_check.pop(ind)
                ind-=1
        if len(values_to_check)>0:
            case_success=False
            if test_case_comment_str=="":
                test_case_comment_str="Values: "+",".join(values_to_check)+" not found in field: "+field_name+"\n"
            else:
                test_case_comment_str+=", Values: "+",".join(values_to_check)+" not found in field: "+field_name+"\n"
    #checking for values not-to-be
    ind=-1
    while(True):
        ind+=1
        if(ind>=len(values_not_to_be)):
            break
    # for ind in range(len(values_not_to_be)):
        try:
            v=values_not_to_be[ind].strip().lower()
        except:
            break
        if v in type_options:
            case_success=False
            if test_case_comment_str=="":
                test_case_comment_str="Value: "+values_not_to_be.pop(ind)+"  be found in field:"+field_name+"\n"
            else:
                test_case_comment_str+=", Value: "+values_not_to_be.pop(ind)+" should not be found in field: "+field_name+"\n"
            # values_not_to_be.pop(ind)
            ind-=1
    if len(values_not_to_be)>0:
        for ind_1 in range(len(values_not_to_be)):
            try:
                v=values_not_to_be[ind_1].strip().lower()
            except:
                break
            try:
                cf_search_box=driver.find_element(By.XPATH, "//input[@data-id='"+field_api_name+"_search']")
                try:
                    cf_search_box_clear_icon=driver.find_element(By.XPATH, "//button[@data-id='"+field_api_name+"_search_ClearIcon']")
                    cf_search_box_clear_icon.click()
                except:
                    pass
            except:
                break
            cf_search_box.click()
            cf_search_box.send_keys(v.strip())
            time.sleep(0.1)
            cf_result_list=driver.find_elements(By.XPATH,"//div[@data-id='"+field_api_name+"_Options']/li/div[1]")
            search_results=[c.text.strip().lower() for c in cf_result_list]
            if v.strip().lower() in search_results:
                case_success=False
                if test_case_comment_str=="":
                    test_case_comment_str="Value: "+values_not_to_be.pop(ind_1)+" should not be found in field:"+field_name
                else:
                    test_case_comment_str+=", Value: "+values_not_to_be.pop(ind_1)+" should not be found in field: "+field_name
                ind-=1

    if case_success:
        return {"respCode":True,"comment":test_case_comment_str}
    else:
        return {"respCode":False,"comment":test_case_comment_str}


    




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

def out_log():
    with open("Field_dependency_logs.txt","w") as f:
        f.write(logs)
    
username = ""
password = ""
logs=""
# username = "ubitest8@gmail.com"
# password = "Ubi@1947"
# driver.get("https://service.unionbankofindia.co.in/agent/ccudesk/union-bank-of-india/tickets/new")

# driver.get("https://ucrm.unionbankofindia.co.in/crm/org60009764661/tab/Leads/create?layoutId=1068000000000167")
# driver.find_element("id","visible_leads").click()



#driver script for map dependency testing
username = "ubideskdev1@unionbankcrm.co.in"
password = "Code@ubi1234"
logs=""
# initialize the Chrome driver
options=Options()
# options.headless=True
driver = webdriver.Chrome("chromedriver",options=options)
sign_in(driver,username,password,sign_in_url)
print_log("Signing into UBI DC")
open_desk_create_ticket_for_test(driver,desk_create_ticket_url)
print_log("Ticket creation page opened")
input_df=pd.read_excel('Layout_Testing_Sheet.xlsx','Sheet1')

#include below line if field dependency has to be tested
# picklist_values_df=pd.read_excel('Field_dependency_input.xlsx','Sheet2')

#load all the pick list values to be used for testing the tbt fields
input_cols=list(input_df.columns)
#seperate all the when columns and tbt columns
when_cols={} #contains when columns and their respective field labels
tbt_cols={} #contains tbt columns and their respective field labels
test_case_result=[]
test_failed_reason=[]
mandatory_test_reasons=[]
mandatory_test_results=[]
lr_reasons=[]
lr_test_results=[]
for col in input_cols:
    col_keywords=col.split("_")
    if "when" == col_keywords[0]:
        when_cols[col]=' '.join(col_keywords[1:])
    elif "tbt" == col_keywords[0]:
        tbt_cols[col]=' '.join(col_keywords[1:])
for _i,row in input_df.iterrows():
    #set when conditions
    test_case_result.append("Success")
    test_failed_reason.append("")
    mandatory_test_reasons.append("")
    mandatory_test_results.append("")
    lr_test_results.append("")
    lr_reasons.append("")
    test_case_ready=True
    print_log("Test case no:"+str(_i))
    for when_c in when_cols.keys():
        when_c_val=row[when_c]
        when_c_label=when_cols[when_c]
        if when_c_val=="" or pd.isna(when_c_val):
            #don't set anything if the value is NA or empty
            set_value_in_drop_down(driver,when_c_label,"-None-")
            continue
        ret=set_value_in_drop_down(driver,when_c_label,when_c_val.strip())
        time.sleep(0.2)
        if ret==-1:
            #condition could not be set for running the test case
            #write log, make the test case failure
            #append the reason in test case failed list
            test_failed_reason[_i]+="Input condition failed: Could not set the value:"+when_c_val+" in the field: "+when_c_label+"\n"
            print_log(test_failed_reason[_i])
            if(test_case_ready):
                test_case_ready=False
            pass
        if ret==-2:
            test_failed_reason[_i]+="Input condtion failed: Could not get the api name for: "+when_c_label+"\n"
            print_log(test_failed_reason[_i])
            if(test_case_ready):
                test_case_ready=False
    #when all conditions are set and test case is still true
    if test_case_ready:
        #check all the map dependencies of the tbt columns
        for field in tbt_cols.keys():
            col_name=field
            field_name=tbt_cols[field]
            drop_values=row[col_name]
            if drop_values=="" or pd.isna(drop_values):
                continue
            total_values=get_available_fields(field_name,picklist_values_df)
            resp=check_values_in_drop_down(driver,field_name,[d.strip().lower() for d in drop_values.split(",") if not pd.isna(d)],[t.strip().lower() for t in total_values if not pd.isna(t)],test_failed_reason[_i])
            if(not resp['respCode']):
                test_case_result[_i]="Failure"
                test_failed_reason[_i]+=resp['comment']
                print_log(resp['comment'])
        pass
        #layout rules testing
        if not pd.isna(row["Fields to be shown"]):
            fields_to_be_shown=row["Fields to be shown"].split(",")
            test_case_success=True
            for field in fields_to_be_shown:
                if field=='':
                    continue
                shown=checkFieldVisibility(driver,field.strip())
                if(not shown):
                    test_case_success=False
                    lr_reasons[_i]+=", cf:{0} is not visible".format(field)
        if test_case_success:
            lr_test_results[_i]="Success"
        else:
            lr_test_results[_i]="Failure"
        
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
                    mandatory_test_reasons[_i]+=", cf:{0} is not mandatory".format(field)
        if mandatory_test_case_success:
            mandatory_test_results[_i]="Success"
        else:
            mandatory_test_results[_i]="Failure"
        #End of testing
    else:
        test_case_result[_i]="Failure"   
    print_log("Result: "+test_case_result[_i])   
input_df["Field Dependency Test Result"]=test_case_result
input_df["Field Dependency Test Failed Reason"]=test_failed_reason
input_df["Layout Rule Test Result"]=lr_test_results
input_df["Layout Rule Test Failed Reason"]=lr_reasons
input_df["Mandatory Fields Test Result"]=mandatory_test_results
input_df["Mandatory Fields Test Failed Reason"]=mandatory_test_reasons
input_df.to_excel("Field_dependency_result.xlsx")
driver.close()
out_log()

        
