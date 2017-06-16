import pdb
import json
import sys
import redfish
import logging

def get_ilo_metrics(hosts):
    iLO_host = ["https://dal-appblx064-27-ilo.prod.walmart.com"]
    #iLO_host = ["https://dfw-appblx034-02-ilo.prod.walmart.com/"]#"https://dfw-appblx089-25-ilo.prod.walmart.com"]
    login_account = "iaasadmin"
    login_password = "1lo@dmin"
    pdb.set_trace()
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

def get_racks(data):
    rack_hvs = []
    rack_list = [x[18:21] for x in data]
    rack_list = sorted(set(rack_list))
    for rack in rack_list:
        rack_host = sorted(filter(lambda x: rack in x,data))
        #rack_hvs.append(rack_host[::len(rack_host)-1])
        rack_hvs.append(rack_host[0])
        rack_hvs.append(rack_host[-1])
    return rack_hvs    
    
def main():
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    logger.debug("script started")
    cloud_name = sys.argv[1]
    final_hosts = []
    with open("/app/monitor/ilo_scripts/hvs/hvs-"+cloud_name+".json") as f:
        get_hv = json.load(f)
        hosts = get_hv.get('hypervisors').get('hvs')
        rack_hv = get_racks(hosts)
        print len(rack_hv)
        print rack_hv
        
    #password = getpass.getpass(prompt="Enter password")
    #get_os_info()
    
        get_ilo_metrics(rack_hv)


if __name__ == "__main__":
    main()

