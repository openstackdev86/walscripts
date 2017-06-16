#Script details

#Script will collect Fan,Disk and over all health status from ILO using multiprocessing.

# usages
#------------
# python .py <cloud-name> [ tested with dal2 ]
import json
import redfish
import sys
import requests
import threading
import os
import signal
from redfish.rest.v1 import InvalidCredentialsError,ServerDownOrUnreachableError,RetriesExhaustedError
import logging
import multiprocessing
from concurrent import futures
from concurrent import *
from concurrent.futures import TimeoutError,wait,as_completed

class Hardware(object):
    
    def __init__(self,hosts,queue):
        self.hosts = hosts
        self.username = "walmart"
        self.password = "Ch@ngeM@y2017"
        self.prefix = "/redfish/v1"
        self.queue = queue
        global failed_data

    def create_process(self):
        data_dict=[]
        cloud_data = []
        f_data = []
        failed_host = []
        completed_host = []
        failed_data = {}
        ex = futures.ThreadPoolExecutor(max_workers=len(self.hosts))
        for i in self.hosts:           
            f_data.append(ex.submit(self.getredfishobject,i,data_dict,failed_host,completed_host))
        for k in f_data:
            try:
                k.result(timeout=30)
            except TimeoutError:
                print("timeout for the host %s"%(threading.current_thread().name))
                out = [x for x in f_data if x.running()]
                print("getting the ruuning threads %s"%(len(out)))
        diff = list(set(self.hosts) - set(completed_host))
        tmp_failed_host = [v.get('host') for v in failed_host]
        timeout_host = list(set(diff) - set(tmp_failed_host))
        d = {}
        d['system_health'] = {"data":data_dict}
        failed_data['hosts'] = {"data":failed_host}
        json.dump(failed_data, file('/app/monitor/ilo_scripts/precheck_scripts/failed_hosts/failed_host.json', 'w'))   
        json.dump(timeout_host, file('/app/monitor/ilo_scripts/precheck_scripts/failed_hosts/timeout_host.json', 'w'))
        self.parse_json(d.get('system_health').get('data'))
        pid= os.getpid()
        ex.shutdown(wait=False)
        os.kill(pid, signal.SIGHUP)

    def parse_json(self,data):
        good_hv=[]
        failed_hv=[]
        for i in data:
            for k,v in i.items():
                if i.get(k).get('health').get('Health') != 'OK':
                    hv_data = {"hostname":k,"details":v}
                    failed_hv.append(hv_data)
                else:
                    hv_data = {"hostname":k,"details":v}
                    good_hv.append(hv_data)

        if len(failed_hv) >=1:
            print"----------Hardware Health summary----------"
            print failed_hv
        else:
            print"----------Hardware Health summary----------"
            print good_hv

    def getting_failed_host(self,host,reason,failed_host):
        try:
            data = {}
            data = {"host":host,"reason":str(reason)}
            failed_host.append(data)
            
        except:
            print("failed to get the host")  
    def getredfishobject(self,hostname,data_dict,failed_host,completed_host):
        try:
            threading.current_thread().setName(hostname)
            redfishobject = redfish.redfish_client(base_url=hostname,username=self.username,password=self.password, 
                                            default_prefix=self.prefix)
            if redfishobject:
                redfishobject.login(auth="session")
                resources = self.getresources(redfishobject,hostname,failed_host)
                res = self.searchfortype(redfishobject,resources,hostname,failed_host,res_type="ComputerSystem.")
                system_result = self.getsystemhealth(redfishobject,res,hostname,failed_host)
                data_dict.append(system_result)
                if system_result:
                    completed_host.append(hostname)
                redfishobject.logout()
            else:
                print("error with multiprocess")
                tmp_error="error with multiprocess"
                self.getting_failed_host(hostname,tmp_error,failed_host)
        
        except RetriesExhaustedError,ex:
            print("Retries exhausted...for hostname %s"%(hostname))
            self.getting_failed_host(hostname,"RetriesExhaustedError",failed_host)
        except InvalidCredentialsError,ex:
            print("inavlid credentials for host %s"%(hostname))
            self.getting_failed_host(hostname,"InvalidCredentialsError",failed_host)
        except ServerDownOrUnreachableError,ex:
            print("server down %s"%(hostname))
            self.getting_failed_host(hostname,"ServerDownOrUnreachableError",failed_host)

    def getdiskhealth(self,redfishobject,hostname):
        disk_health = []
        response = redfishobject.get("/redfish/v1/Systems/1/SmartStorage/ArrayControllers/", None)
        if response.dict['Members@odata.count'] == 0:
            print("no disk found for the host",hostname)
            return False
        else:
            output = response.dict['Members']
            for i in output:
                array_control = i['@odata.id']
                res = redfishobject.get(array_control)
                drive_data = res.dict
                disk_health.append(drive_data.get('Status'))
                
            return disk_health


    def getsystemhealth(self,redfishobject,res,hostname,failed_host):
        output = []
        data = {}
        t_hostname= ""
        try:
         
            system_data = redfishobject.get(res[0])
            system_data_dict = system_data.dict
            
            if not system_data_dict['HostName']:
                                                          #if hostname is missing from ilo
                t_hostname = ""
                tmp_hostname = hostname.lstrip('https://')
                t_hostname = tmp_hostname.rstrip('-ilo.prod.walmart.com')
                try:
                         
                    data[t_hostname] = {"Power_state":system_data_dict.get('PowerState'),"health":system_data_dict.get('Status'),
                                        "Disk_Health":self.getdiskhealth(redfishobject,t_hostname)}
                except ValueError,ex:
                    print("host %s not having exact info %s"%(t_hostname,ex))
                    self.getting_failed_host(t_hostname,"ValueError",failed_host)
                    return data            

            else:
                   
                try:
                    data[system_data_dict['HostName']] = {"Power_state":system_data_dict.get('PowerState'),"health":system_data_dict.get('Status'),
                                        "Disk_Health":self.getdiskhealth(redfishobject,t_hostname)}
                except ValueError,ex:

                    print("host %s not having exact info %s"%(system_data_dict['HostName'],ex))
                    self.getting_failed_host(system_data_dict['HostName'],"ValueError",failed_host)
                    return data
        except IndexError,ex:
            print("index erroe for the hostname %s"%(hostname))
            self.getting_failed_host(hostname,"IndexError",failed_host)
  
        return data

    def getresources(self,redfishobject,hostname,failed_host):
        resources=None
        response = redfishobject.get("/redfish/v1/resourcedirectory/", None)
        try:
          
            resources = response.dict["Instances"]
        except KeyError,ex:
            self.getting_failed_host(hostname,"KeyError",failed_host)
        return resources

    def searchfortype(self,redfishobject,resources,hostname,failed_host,res_type):
        data = []
        try:

            for x in resources:
                if '@odata.type' in x and 'ComputerSystem.' in x['@odata.type']:
                    data.append(x.get('@odata.id'))
        except TypeError,ex:
            self.getting_failed_host(hostname,"TypeError",failed_host)
                
        return data

if __name__ == "__main__":
    multiprocessing.log_to_stderr()
    logger = multiprocessing.get_logger()
    logger.setLevel(logging.INFO)
    queue = multiprocessing.Queue()
    host_list=[]
    if len(sys.argv) > 1:
        sys.argv.remove('health_check.py')
        for i in sys.argv:
            tmp_host = "https://"+i
            host_list.append(tmp_host)
        hard = Hardware(host_list,queue)
        hard.create_process()
        print("no input from the user")
    else:
        host_list = ["https://dal-appblx112-12-ilo.prod.walmart.com","https://dal-appblx112-13-ilo.prod.walmart.com"]
        hard = Hardware(host_list,queue)
        hard.create_process()
