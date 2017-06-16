import pdb
import sys
import redfish
import json
import logging

def get_ilo_metrics():
    #iLO_host = "https://dfw-appblx089-25-ilo.prod.walmart.com"
    iLO_host = ["https://dfw-bz-37-conblx-002-29-ilo.prod.walmart.com"]#"https://dfw-appblx089-25-ilo.prod.walmart.com"]
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
        pdb.set_trace()
        
        response = REST_OBJ.post(path="/redfish/v1/Systems/1/Actions/ComputerSystem.Reset", body=body)
        #response = REST_OBJ.post(path="/redfish/v1/Systems/1", body=body)
        
        


    count =0
    REST_OBJ.logout()

def main():
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    logger.debug("script started")
    #password = getpass.getpass(prompt="Enter password")
    #get_os_info()
    get_ilo_metrics()


if __name__ == "__main__":
    main()

