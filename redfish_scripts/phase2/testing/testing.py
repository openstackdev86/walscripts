import pdb
import sys
import redfish
import logging

def get_ilo_metrics():
    #iLO_host = "https://dfw-appblx089-25-ilo.prod.walmart.com"
    iLO_host = ["https://dfw-appblx018-27-ilo.prod.walmart.com"]#"https://dfw-appblx089-25-ilo.prod.walmart.com"]
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
        response = REST_OBJ.get("/redfish/v1/Systems/1/SmartStorage/ArrayControllers/", None)
        pdb.set_trace()
        output = response.dict['Members']
        for i in output:

            array_control = i['@odata.id']
            res = REST_OBJ.get(array_control)
            drive_data = res.dict

            physical_drive = REST_OBJ.get(drive_data['Links']['LogicalDrives']['@odata.id'])
            physical_data  = physical_drive.dict
            for k in range(0,len(physical_data['Members'])):

                data = physical_data['Members'][k]
                data = REST_OBJ.get(data['@odata.id'])
                data = data.dict
                if data['Status']['Health']=='Critical':
                    disk_data = {}
                    disk_data[n] = {'Logical_drive_no':data['LogicalDriveNumber'],'disk_health':data['Status']['Health']}
                    fail_disk.append(disk_data)
                elif data['Status']['Health']=='OK':
                    ok_disk.append(data['LogicalDriveNumber'])
    print fail_disk
    print ok_disk



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

