import redfish 
import multiprocessing
from multiprocessing.dummy import Pool as ThreadPool
import time
import logging

class Hardware(object):
    
    def __init__(self,hosts,queue):
        self.hosts = hosts
        self.username = "xxxx"
        self.password = "xxxx"
        self.prefix = "/redfish/v1"
        self.queue = queue

    def create_process(self):
        jobs = []
        #Initialize 30 threads
        pool = ThreadPool(30)
        data = pool.map(self.getredfishobject,self.hosts)
        pool.close()
        pool.join()
        while not self.queue.empty():

            print self.queue.get()
       
 
    def getredfishobject(self,hostname):
        
#        print("getting object for hostanme %s"%(hostname))
        redfishobject = redfish.redfish_client(base_url='https://'+hostname,username=self.username,password=self.password, default_prefix=self.prefix)
        if redfishobject:
            redfishobject.login(auth="session")
            
#            print("Got redfish handler for hostname %s"%(hostname))
            #response = redfishobject.get("/redfish/v1/resourcedirectory/", None)
            #self.queue.put(response)
            resources = self.getresources(redfishobject)
            #self.queue.put(resources)
            res = self.searchfortype(redfishobject,resources,res_type="ComputerSystem.")
            system_result = self.getsystemhealth(redfishobject,res,hostname)
              
            self.queue.put(system_result)
            redfishobject.logout()
            
        else:
            print("error in getting handler") 
             
            
    def getsystemhealth(self,redfishobject,res,hostname):
        output = []
        system_data = redfishobject.get(res[0])
        system_data_dict = system_data.dict
        data = {}
        data['hostname'] = hostname
        data['powerstate'] = system_data_dict['PowerState']
        data['cpu_info'] = system_data_dict['ProcessorSummary']
        # Getting firmware version 
        firmware_version = redfishobject.get("/redfish/v1/Systems/1/FirmwareInventory/", None)
        data['firmware_version'] = firmware_version.dict['Current']['SPSFirmwareVersionData']
        # Getting thermal data
        fan_data = redfishobject.get("/redfish/v1/Chassis/1/Thermal/")
        fan = {}
        data['total_fan'] = fan_data.dict['Fans']
        output.append(data)
  
        return output

    def getresources(self,redfishobject):
        response = redfishobject.get("/redfish/v1/resourcedirectory/", None)
        resources = response.dict["Instances"]
        return resources

    def searchfortype(self,redfishobject,resources,res_type):
        data = []
        #output = resources.dict['Instances']
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

