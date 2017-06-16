#Script details

#Script will collect Fan,Disk and over all health status from ILO using multiprocessing.

# usages
#------------
# python .py <cloud-name> [ tested with dal2 ]
import json
import pdb
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
    
    def __init__(self,hosts,queue,cloud_name):
        self.hosts = hosts
        self.username = "walmart"
        self.password = "Ch@ngeM@y2017"
        self.prefix = "/redfish/v1"
        self.queue = queue
        self.cloud_name = cloud_name
        global failed_data

    def create_process(self):
        data_dict=[]
        cloud_data = []
        f_data = []
        failed_host = []
        completed_host = []
        failed_data = {}
        print len(self.hosts)
        ex = futures.ThreadPoolExecutor(max_workers=len(self.hosts))
        for i in self.hosts:           
            f_data.append(ex.submit(self.getredfishobject,i,data_dict,failed_host,completed_host))
        for k in f_data:
            try:
                k.result(timeout=20)
            except TimeoutError:
                print("timeout for the host %s"%(threading.current_thread().name))
                out = [x for x in f_data if x.running()]
                print("getting the ruuning threads %s"%(len(out)))
        print("started shutdown process")
        print len(data_dict)
        print len(failed_host)
        diff = list(set(self.hosts) - set(completed_host))
        tmp_failed_host = [v.get('host') for v in failed_host]
        timeout_host = list(set(diff) - set(tmp_failed_host))
        d = {}
        d['system_health'] = {"cloud_name":self.cloud_name,"data":data_dict}
        cloud_json = self.cloud_name+'.json'
        json.dump(d, file('/app/monitor/ilo_scripts/phase2/output_json/'+cloud_json, 'w'))
        failed_data['hosts'] = {"cloud_name":self.cloud_name,"data":failed_host}
        json.dump(failed_data, file('/app/monitor/ilo_scripts/phase2/failed_host/'+cloud_json, 'w'))   
        json.dump(timeout_host, file('/app/monitor/ilo_scripts/phase2/failed_host/'+'timeout_'+cloud_json, 'w'))   
        pid= os.getpid()
        ex.shutdown(wait=False)
        os.kill(pid, signal.SIGHUP)

    def getting_failed_host(self,host,reason,failed_host):
        try:
            data = {}
            data = {"host":host,"reason":str(reason)}
            failed_host.append(data)
            #print("failed_host........%s"%(failed_host))
            
        except:
            print("failed to get the host")  
    def getredfishobject(self,hostname,data_dict,failed_host,completed_host):
        try:
            print("getting object for hostanme %s"%(hostname))
            threading.current_thread().setName(hostname)
            redfishobject = redfish.redfish_client(base_url=hostname,username=self.username,password=self.password, 
                                            default_prefix=self.prefix)
            if redfishobject:
                redfishobject.login(auth="session")
                print("Got redfish handler for hostname %s"%(hostname))
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

    def getdiskhealth(self,redfishobject,hostname,disk_type=None):
        
        response = redfishobject.get("/redfish/v1/Systems/1/SmartStorage/ArrayControllers/", None)
        if response.dict['Members@odata.count'] == 0:
            print("no disk found for the host",hostname)
            return False
        else:
            output = response.dict['Members']
            for i in output:
                array_control = i['@odata.id']
                print("getting disk for hostname %s under %s"%(array_control,hostname)) 
                res = redfishobject.get(array_control)
                drive_data = res.dict
                if disk_type == 'physical':
                    physical_drive = redfishobject.get(drive_data['Links']['PhysicalDrives']['@odata.id'])
                    physical_data  = physical_drive.dict
                    disk_data = self.parse_data(physical_data,hostname,redfishobject,disk_type="physical")
                elif disk_type == 'logical':
                    logical_drive = redfishobject.get(drive_data['Links']['LogicalDrives']['@odata.id'])
                    logical_data = logical_drive.dict
                    disk_data = self.parse_data(logical_data,hostname,redfishobject,disk_type="logical")
                else:
                    print(" no drive found")

            return disk_data

    def parse_data(self,disk_data,hostname,redfishobject,disk_type):
        disk_dict = {}
        disk_f = {} 
        disk_result = []
        for y in xrange(0,len(disk_data['Members'])):

            data = redfishobject.get(disk_data['Members'][y]['@odata.id'])
            if disk_type == 'logical':
                disk_dict[data.dict['Name']+str(data.dict['Id'])] = {'disk_drive_count':data.dict.get('Id'),'drive_status':data.dict.get('Status'),
                      'capacity(GB)':data.dict.get('CapacityMiB')/1024,'Raid':data.dict.get('Raid'),'Logical Drive_number':data.dict.get('LogicalDriveNumber')}
            
            elif disk_type == 'physical':
                disk_dict[data.dict['Name']+str(data.dict['Id'])] = {'disk_drive_count':data.dict.get('Id'),'drive_status':data.dict.get('Status'),
                      'media_type':data.dict.get('MediaType'),'capacity(GB)':data.dict.get('CapacityMiB')/1024,'Disk_location':data.dict.get('Location')}
            else:
                print("no disk found")

        disk_result.append(disk_dict)
        return disk_result


    def getsystemhealth(self,redfishobject,res,hostname,failed_host):
        output = []
        data = {}
        try:
         
            system_data = redfishobject.get(res[0])
            system_data_dict = system_data.dict
            firmware_version = redfishobject.get("/redfish/v1/Systems/1/FirmwareInventory/", None)
            thermal_data = redfishobject.get("/redfish/v1/Chassis/1/Thermal/")
            
            if not system_data_dict['HostName']:
                                                          #if hostname is missing from ilo
                t_hostname = ""
                tmp_hostname = hostname.lstrip('https://')
                t_hostname = tmp_hostname.rstrip('-ilo.prod.walmart.com')
                #data[t_hostname] = {"Bios_version":system_data_dict['BiosVersion'],"Power_state":system_data_dict['PowerState'],"Processors":[system_data_dict['ProcessorSummary']],"manufacturer":system_data_dict['Manufacturer'],"model":system_data_dict['Model'],"health":system_data_dict['Status'],"Memory_status":system_data_dict['MemorySummary'],"Fans":thermal_data.dict['Fans'],"ilo_version":firmware_version.dict["Current"]["SystemBMC"][0]["VersionString"],"Disk_Health":{"physical_disk":self.getdiskhealth(redfishobject,t_hostname,disk_type="physical"),"logical_disk":self.getdiskhealth(redfishobject,t_hostname,disk_type="logical")}}
                try:
                         
                    data[t_hostname] = {"Bios_version":system_data_dict.get('BiosVersion'),"Power_state":system_data_dict.get('PowerState'),
                                        "Processors":[system_data_dict.get('ProcessorSummary')],"manufacturer":system_data_dict.get('Manufacturer'),
                                        "model":system_data_dict.get('Model'),"health":system_data_dict.get('Status'),"Memory_status":system_data_dict.get('MemorySummary'),
                                        "Fans":thermal_data.dict.get('Fans'),"ilo_version":firmware_version.dict["Current"]["SystemBMC"][0]["VersionString"],
                                        "Disk_Health":{"physical_disk":self.getdiskhealth(redfishobject,t_hostname,disk_type="physical"),
                                        "logical_disk":self.getdiskhealth(redfishobject,t_hostname,disk_type="logical")}}        
                except ValueError,ex:
                    print("host %s not having exact info %s"%(t_hostname,ex))
                    self.getting_failed_host(t_hostname,"ValueError",failed_host)
                    return data            

            else:
                   
                #data[system_data_dict['HostName']] = {"Bios_version":system_data_dict['BiosVersion'],"Power_state":system_data_dict['PowerState'],"Processors":[system_data_dict['ProcessorSummary']],"manufacturer":system_data_dict['Manufacturer'],"model":system_data_dict['Model'],"health":system_data_dict['Status'],"Memory_status":system_data_dict['MemorySummary'],"Fans":thermal_data.dict['Fans'],"ilo_version":firmware_version.dict["Current"]["SystemBMC"][0]["VersionString"],"Disk_Health":{"physical_disk":self.getdiskhealth(redfishobject,system_data_dict['HostName'],disk_type="physical"),"logical_disk":self.getdiskhealth(redfishobject,system_data_dict['HostName'],disk_type="logical")}}
                try:
                    
                    data[system_data_dict['HostName']] = {"Bios_version":system_data_dict.get('BiosVersion'),"Power_state":system_data_dict.get('PowerState'),
                                                          "Processors":[system_data_dict.get('ProcessorSummary')],"manufacturer":system_data_dict.get('Manufacturer'),
                                                          "model":system_data_dict.get('Model'),"health":system_data_dict.get('Status'),"Memory_status":system_data_dict.get('MemorySummary'),
                                                          "Fans":thermal_data.dict.get('Fans'),"ilo_version":firmware_version.dict["Current"]["SystemBMC"][0]["VersionString"],
                                                          "Disk_Health":{"physical_disk":self.getdiskhealth(redfishobject,system_data_dict['HostName'],disk_type="physical"),
                                                          "logical_disk":self.getdiskhealth(redfishobject,system_data_dict['HostName'],disk_type="logical")}}  
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
    cloud_name = sys.argv[1]
    with open("/app/monitor/ilo_scripts/hvs/hvs-"+cloud_name+".json") as f:
        get_hv = json.load(f)
        hosts = get_hv.get('hypervisors').get('hvs')
        pdb.set_trace()
        #host_list = ["https://dal-appblx113-30-ilo.prod.walmart.com","https://dal-appblx056-08-ilo.prod.walmart.com","https://dal-appblx058-08-ilo.prod.walmart.com","https://dal-appblx113-21-ilo.prod.walmart.com","https://dal-appblx017-09-ilo.prod.walmart.com"]
        cloud = get_hv.get('hypervisors').get('cloud')
        hard = Hardware(hosts,queue,cloud)
        #hard = Hardware(host_list,queue,cloud)
        hard.create_process()
