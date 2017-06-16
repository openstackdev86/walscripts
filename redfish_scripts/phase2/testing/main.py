import pdb
import threading
import time
from subprocess import Popen
import signal
import os
import sys
import redfish
from redfish.rest.v1 import InvalidCredentialsError,ServerDownOrUnreachableError,RetriesExhaustedError
import logging
from concurrent import futures
from concurrent import *
from concurrent.futures import TimeoutError,wait,as_completed
import concurrent.futures

class Timeout():
    """Timeout class using ALARM signal."""
    class Timeout(Exception):
        pass
 
    def __init__(self, sec):
        self.sec = sec
 
    def __enter__(self):
        signal.signal(signal.SIGALRM, self.raise_timeout)
        signal.alarm(self.sec)
 
    def __exit__(self, *args):
        signal.alarm(0)    # disable alarm
 
    def raise_timeout(self, *args):
        raise Timeout.Timeout()

def get_ilo(host):
    try:

        print(host)
        REST_OBJ = redfish.redfish_client(base_url=host,username="walmart",password="Ch@ngeM@y2017", default_prefix='/redfish/v1')
        if REST_OBJ:
    
            REST_OBJ.login(auth="session")
            print("got handler for host %s"%(host))
            response = REST_OBJ.get("/redfish/v1/Systems/1/FirmwareInventory/", None)
            output = response.dict['Members']
            pdb.set_trace()
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
            REST_OBJ.logout()
    
        else:
            print("error with multiprocess")
    except RetriesExhaustedError:
        print("Retries trid for the host...%s"%(host))
    except InvalidCredentialsError:
        print("inavlid credentials for host %s"%(hostname))
    except ServerDownOrUnreachableError:
        print("server down %s"%(hostname))

def get_ilo_metrics():
    iLO_host = ["https://dal-appblx072-16-ilo.prod.walmart.com"]
    #iLO_host = ["https://dal-appblx063-25-ilo.prod.walmart.com","https://dal-appblx089-25-ilo.prod.walmart.com","https://dal-appblx089-26-ilo.prod.walmart.com", "https://dal-appblx051-26-ilo.prod.walmart.com", "https://dal-appblx051-27-ilo.prod.walmart.com", "https://dal-appblx090-27-ilo.prod.walmart.com", "https://dal-appblx090-26-ilo.prod.walmart.com", "https://dal-appblx090-25-ilo.prod.walmart.com", "https://dal-appblx072-27-ilo.prod.walmart.com", "https://dal-appblx072-25-ilo.prod.walmart.com", "https://dal-appblx072-26-ilo.prod.walmart.com","https://dal-appblx113-30-ilo.prod.walmart.com"]
    #iLO_host = ["https://dfw-appblx075-12-ilo.prod.walmart.com"]
    login_account = "walmart"
    login_password = "Ch@ngeM@y2017"
    final_result = []
    fail_disk = []
    global ok_disk
    global fail_disk
    ok_disk= []
    task_list = []
    global REST_OBJ
    global output
    ex = futures.ThreadPoolExecutor(max_workers=2)
    for i in iLO_host:
        task_list.append(ex.submit(get_ilo,i))
        print("thread_name...%s"%(threading.current_thread().name))         
    for k in task_list:
        try:
            k.result(timeout=20)
        except TimeoutError:
            print("timeout for the host %s"%(i))
            print("getting the ruuning threads")
            out = [x for x in task_list if x.running()]
            print len(out)
            k.set_exception("TimeoutError")
            k.cancel()
                
        #    print k.result(timeout=10)
    #for n in iLO_host:
    #    print("getting handler for %s"%(n)) 
    #    REST_OBJ = redfish.redfish_client(base_url=n,username=login_account,password=login_password, default_prefix='/redfish/v1')
    #    REST_OBJ.login(auth="session")
    #    response = REST_OBJ.get("/redfish/v1/Systems/1/SmartStorage/ArrayControllers/", None)
    #    output = response.dict['Members']
    #    for i in output:
    #    
    #        array_control = i['@odata.id']
    #        res = REST_OBJ.get(array_control)
    #        drive_data = res.dict
    #         
    #        physical_drive = REST_OBJ.get(drive_data['Links']['LogicalDrives']['@odata.id'])
    #        physical_data  = physical_drive.dict
    #        for k in range(0,len(physical_data['Members'])):
    #   
    #            data = physical_data['Members'][k]
    #            data = REST_OBJ.get(data['@odata.id'])
    #            data = data.dict
    #            if data['Status']['Health']=='Critical':
    #                disk_data = {}
    #                disk_data[n] = {'Logical_drive_no':data['LogicalDriveNumber'],'disk_health':data['Status']['Health']}   
    #                fail_disk.append(disk_data)
    #            elif data['Status']['Health']=='OK':
    #                ok_disk.append(data['LogicalDriveNumber'])  
    #print fail_disk
    #print ok_disk         
    #          
    #        

    #count =0
    #REST_OBJ.logout()

def main():
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    logger.debug("script started")
    #password = getpass.getpass(prompt="Enter password") 
    #get_os_info()    
    get_ilo_metrics()



if __name__ == "__main__":
    main()

