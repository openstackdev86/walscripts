import pdb
import sys
import redfish
#from redfish.rest.v1 import U
import json
import logging

def get_ilo_metrics():
    #iLO_host = "https://dfw-appblx089-25-ilo.prod.walmart.com"
    iLO_host = ["https://dfw-bz-37-conblx-002-27-ilo.prod.walmart.com"]#"https://dfw-appblx089-25-ilo.prod.walmart.com"]
    #iLO_host = ["https://10.65.123.226"]#"https://dfw-appblx089-25-ilo.prod.walmart.com"]
    login_account = "iaasadmin"
    login_password = "1lo@dmin"
    final_result = []
    fail_disk = []
    ok_disk= []
    global REST_OBJ
    global output
    for n in iLO_host:
        print("getting handler for %s"%(n))
        REST_OBJ = redfish.redfish_client(base_url=n,username=login_account,password=login_password, default_prefix='/redfish/v1')
        REST_OBJ.login(auth="session")
        pdb.set_trace()
        #response = REST_OBJ.get("/redfish/v1/Systems/1/Actions/ComputerSystem.Reset", None)
        body = dict()
       # body['ResetType']= "Off"
        #body = {"Action":"Reset","ResetType":"Off"}
        resources = REST_OBJ.get('/redfish/v1/resourcedirectory/')
        res = resources.dict.get('Instances')
        res_data = searchfortype(REST_OBJ,res,res_type='AccountService.')
        """
        setting one time boot option
        """
        #body['Boot'] = {"BootSourceOverrideTarget": "Pxe"}
        #body['Boot'] = {"BootSourceOverrideTarget": "Hdd"}
        #change = REST_OBJ.patch(path="/redfish/v1/Systems/1/",body=body)
        """
        changeing the boot order
        """
        #change_boot = REST_OBJ.get('/redfish/v1/systems/1/bios/Boot/Settings')
        #boot = ['HD.Emb.3.1', 'HD.Emb.4.1', 'HD.Emb.5.1', 'HD.Emb.6.1', 'HD.Emb.7.1', 'HD.Emb.8.1', 'IC.LOM.1.1.IPv4', 'NIC.LOM.1.1.IPv6', 'NIC.Slot.2.1.IPv4', 'NIC.Slot.2.1.IPv6']
        #body["PersistentBootConfigOrder"] = boot
        #boot_res = REST_OBJ.patch(path='/redfish/v1/systems/1/bios/Boot/Settings', body=body)
        """
        CRUD ILO account
        """

        # adding_user 
        #delete_ilo_account(REST_OBJ,res_data)
        add_user = add_ilo_account(REST_OBJ,res_data)
        #power_data = power(REST_OBJ,res,res_type='ComputerSystem.')
         
        #    if "@odata.type" in item and 'Manager.' in item["@odata.type"].lower():
        #        print item["@odata.id"]
        #bios = REST_OBJ.get('/redfish/v1/systems/1/bios/')
        
        pdb.set_trace()
        #body["Action"] = "Reset"
        #body["ResetType"] = "PushPowerButton"
        #bo = {"BaseConfig": "default"}
        body["RestoreManufacturingDefaults"] = "Yes" 
        #response = REST_OBJ.patch(path="/redfish/v1/systems/1/BIOS/settings", body=body)
        #response = REST_OBJ.post(path="/redfish/v1/Managers/1", body=body)

    count =0
    REST_OBJ.logout()

def searchfortype(obj,resources,res_type):
        data = []
        try:

            for x in resources:
                if '@odata.type' in x and res_type in x['@odata.type']:
                    data.append(x.get('@odata.id'))
        except TypeError,ex:
            self.getting_failed_host(hostname,"TypeError",failed_host)

        return data

def ilo_reset():
    body = {}
    body["Action"] = "Reset"
    response = REST_OBJ.post(path="/redfish/v1/Managers/1", body=body)

def power(REST_OBJ,res,res_type):
    pdb.set_trace()
    data = searchfortype(REST_OBJ,res,res_type)
    body = {}
    body["Action"] = "Reset"
    #body["ResetType"] = "ForceOff"
    #body["ResetType"] = "ForceRestart"
    #body["ResetType"] = "PushPowerButton"
    body["ResetType"] = "On"
    res = REST_OBJ.post(path=data[0],body=body)
    #print data

def check_existing_user(obj,res_data,del_user):
    get_user_accounts = obj.get(res_data).dict
    for user in get_user_accounts.get("Members"):
        get_user = obj.get(user.get('@odata.id')).dict.get('Oem').get('Hp')['LoginName']
        if get_user == del_user:
            obj.delete(path=resp.dict["Accounts"]["@odata.id"])
            return False
        else:
            return True
        
def delete_ilo_account(obj,res_data):
    pdb.set_trace()
    resp = REST_OBJ.get(res_data[0])
    del_user = REST_OBJ.get('/redfish/v1/AccountService/Accounts/').dict
    for user in del_user.get("Members"):
        get_user = obj.get(user.get('@odata.id')).dict.get('Oem').get('Hp')['LoginName']
        if get_user == "testing":
            obj.delete(path=user.get('@odata.id'))
    #check_existing_user(obj,resp,"testing") 
     
def add_ilo_account(obj,res_data):
    try:
        resp = REST_OBJ.get(res_data[0])
        body = {"UserName":"testing","Password":"testing123","Oem": {}}
        OemHpDict = {}
        OemHpDict["LoginName"] = "testing"
        OemHpDict["Privileges"] = {}
        OemHpDict["Privileges"]["RemoteConsolePriv"] = True
        OemHpDict["Privileges"]["iLOConfigPriv"] = True
        OemHpDict["Privileges"]["VirtualMediaPriv"] = True
        OemHpDict["Privileges"]["UserConfigPriv"] = True
        OemHpDict["Privileges"]["VirtualPowerAndResetPriv"] = True
        body["Oem"]["Hp"] = OemHpDict
        pdb.set_trace()
        #check_user = check_existing_user(REST_OBJ,resp.dict["Accounts"]["@odata.id"],"testing")
        add_user = REST_OBJ.post(path=resp.dict["Accounts"]["@odata.id"],body=body)
        if add_user == 201:
            print("User created successfull")
    except Exception,e:
        raise e  
    
    
def main():
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    logger.debug("script started")
    #password = getpass.getpass(prompt="Enter password")
    #get_os_info()
    get_ilo_metrics()


if __name__ == "__main__":
    main()

