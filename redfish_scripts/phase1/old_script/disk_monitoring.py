#!/usr/bin/env python
#title           :hardware.py
#description     :Handling redfish objects using multiprocessing
#author          :Keerthivasan Selvaraj
#email           :Keerthivasan.Selvaraj@walmart.com
#date            :25/12/2016
#version         :0.2
#usage           :python hardware.py
#notes           :Handling redfish objects using multiprocessing for getting disk status
#python_version  :2.7.12
#==============================================================================
import redfish
from redfish.rest.v1 import InvalidCredentialsError
import logging
import multiprocessing
import json
from multiprocessing.dummy import Pool as ThreadPool
import time

class Hardware(object):
    
    def __init__(self,hosts,queue):
        self.hosts = hosts
        self.username = "*************************"
        self.password = "**************************"
        self.prefix = "/redfish/v1"
        self.queue = queue

    def create_process(self):
        jobs = []
        return_out = []
        pool = ThreadPool(40)
        data = pool.map_async(self.getredfishobject,self.hosts)
        pool.close()
        pool.join()
        while not self.queue.empty():
            return_out.append(self.queue.get())
        d = {}
        d['system_health'] = return_out
        json.dump(d, file('hv_data.json', 'w'))
 
    def getredfishobject(self,hostname):
        
        try:
            print("getting object for hostanme %s"%(hostname))
            redfishobject = redfish.redfish_client(base_url=hostname,username=self.username,password=self.password, default_prefix=self.prefix)
            if redfishobject:
                redfishobject.login(auth="session")
                print("Got redfish handler for hostname %s"%(hostname))
                resources = self.getresources(redfishobject)
                res = self.searchfortype(redfishobject,resources,res_type="ComputerSystem.")
                system_result = self.getsystemhealth(redfishobject,res,hostname)
                self.queue.put(system_result)
                redfishobject.logout()
          
        except InvalidCredentialsError:
            print("inavlid credentials for host %s"%(hostname))
         
    ### Snippet for getting Disk health both logical and physical.
    def getdiskhealth(self,redfishobject,hostname,disk_type=None):
        response = redfishobject.get("/redfish/v1/Systems/1/SmartStorage/ArrayControllers/", None)
        output = response.dict['Members']
        for i in output:
            array_control = i['@odata.id']
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
                disk_dict[data.dict['Name']+str(data.dict['Id'])] = {'disk_drive_count':data.dict['Id'],'drive_status':data.dict['Status'],
                             'capacity(GB)':data.dict['CapacityMiB']/1024,'Raid':data.dict['Raid'],
                             'Logical Drive_number':data.dict['LogicalDriveNumber']}
            elif disk_type == 'physical':
                disk_dict[data.dict['Name']+str(data.dict['Id'])] = {'disk_drive_count':data.dict['Id'],'drive_status':data.dict['Status'],
                             'media_type':data.dict['MediaType'],'capacity(GB)':data.dict['CapacityMiB']/1024,'Disk_location':data.dict['Location']}
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
        data[system_data_dict['HostName']] = {"Bios_version":system_data_dict['BiosVersion'],"Power_state":system_data_dict['PowerState'],
                     "Processors":[system_data_dict['ProcessorSummary']],"manufacturer":system_data_dict['Manufacturer'],"model":system_data_dict['Model'],
                     "health":system_data_dict['Status'],"Memory_status":system_data_dict['MemorySummary'],"Fans":thermal_data.dict['Fans'],
                     "ilo_version":firmware_version.dict["Current"]["SystemBMC"][0]["VersionString"],
                     "Disk_Health":{"physical_disk":self.getdiskhealth(redfishobject,system_data_dict['HostName'],disk_type="physical"),"logical_disk":self.getdiskhealth(redfishobject,system_data_dict['HostName'],disk_type="logical")}}   
  
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
    fh=open('hosts.txt','r')
    hosts = []
    for host in fh:
        hosts.append(host.rstrip('\n'))
    fh.close()
    queue = multiprocessing.Queue()
    hard = Hardware(hosts,queue)
    hard.create_process()
