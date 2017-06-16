#Script details

#Script will collect Fan,Disk and over all health status from ILO using multiprocessing.

# usages
#------------
# python .py <cloud-name> [ tested with dal2 ]
import pdb
import json
import redfish
import sys
import requests
from redfish.rest.v1 import InvalidCredentialsError
import logging
import multiprocessing
from cred import *        # file for importing cloud related information( auth_url,username,password, .etc)
from concurrent import futures
from concurrent import *
from concurrent.futures import TimeoutError,wait,as_completed

def get_token(cloud_name):
    cloud_endpoint = get_endpoint(cloud_name)
    pdb.set_trace()
    auth={ "auth": {"identity": {"methods": ["password"],"password": {"user":{"name":cloud_endpoint['username'], "domain":{ "id": "default"},"password": cloud_endpoint['password']}}}}}

    auth_url = cloud_endpoint['auth_url'].replace('v3','v3/auth/tokens')

    headers = {'Accept': 'application/json','Content-Type':'application/json'}
    token = requests.post(auth_url,data=json.dumps(auth),headers=headers)
    token_data = json.loads(token.text)
    token = token.headers.get('X-Subject-Token')
    tenant_id = token_data['token']['project']['id']
    return cloud_endpoint['auth_url'],tenant_id,token

def get_hvs(cloud_name):
    result = []
    clouds= {}
    auth_url,tenant_id,token = get_token(cloud_name)
    nova_url = auth_url.replace('5000','8774')
    nova_url = nova_url.replace('v3','v2/')
    nova_url = nova_url + tenant_id + "/os-hypervisors"
    headers = {'Accept': 'application/json','X-Auth-Token':token,'Content-Type':'application/json'}
    get_hostagg = requests.get(nova_url,headers=headers)
    host_aggregate = json.loads(get_hostagg.text)
    for i in host_aggregate['hypervisors']:
        data = i.get('hypervisor_hostname')
        result.append('https://'+ str(data).replace('.prod.walmart.com','-ilo.prod.walmart.com'))
    clouds[cloud_name] = {'hypervisor':result}
    return clouds[cloud_name]['hypervisor'][1:3]

class Hardware(object):
    
    def __init__(self,hosts,queue,cloud_name):
        self.hosts = hosts
        self.username = "walmart"
        self.password = "Ch@nge0ct2016"
        self.prefix = "/redfish/v1"
        self.queue = queue
        self.cloud_name = cloud_name
        global return_out
        

    def create_process(self):
        jobs = []
        return_out = []
        data_dict=[]
        cloud_data = []
        f_data = []
        print len(self.hosts)
        with futures.ThreadPoolExecutor(max_workers=len(self.hosts)) as executor:
            for i in self.hosts:           
                f_data.append(executor.submit(self.getredfishobject,i,data_dict))
            for k in as_completed(f_data):
                print k.result(timeout=15)
            
        print len(data_dict)
         
        d = {}
        d['system_health'] = {"cloud_name":self.cloud_name,"data":data_dict}
        cloud_json = self.cloud_name+'.json'
        json.dump(d, file(cloud_json, 'w'))
     
    
    def getredfishobject(self,hostname,data_dict):
        
        try:
            
            print("getting object for hostanme %s"%(hostname))
            redfishobject = redfish.redfish_client(base_url=hostname,username=self.username,password=self.password, 
                                            default_prefix=self.prefix)
            if redfishobject:
                redfishobject.login(auth="session")
                print("Got redfish handler for hostname %s"%(hostname))
                resources = self.getresources(redfishobject)
                res = self.searchfortype(redfishobject,resources,res_type="ComputerSystem.")
                system_result = self.getsystemhealth(redfishobject,res,hostname)
                data_dict.append(system_result)
                redfishobject.logout()
            else:
                print("error with multiprocess") 
          
        except InvalidCredentialsError:
            print("inavlid credentials for host %s"%(hostname))
             
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


    def getsystemhealth(self,redfishobject,res,hostname):
        output = []
        system_data = redfishobject.get(res[0])
        system_data_dict = system_data.dict
        data = {}
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
                return data
  
        return data

    def getresources(self,redfishobject):
        response = redfishobject.get("/redfish/v1/resourcedirectory/", None)
        resources = response.dict["Instances"]
        return resources

    def searchfortype(self,redfishobject,resources,res_type):
        data = []
        
        for x in resources:
            if '@odata.type' in x and 'ComputerSystem.' in x['@odata.type']:
                data.append(x.get('@odata.id'))
                
        return data

if __name__ == "__main__":
    multiprocessing.log_to_stderr()
    logger = multiprocessing.get_logger()
    logger.setLevel(logging.INFO)
    queue = multiprocessing.Queue()
    hosts = get_hvs(sys.argv[1])
    hard = Hardware(hosts,queue,sys.argv[1])
    hard.create_process()
