import json
import requests
import glob
import argparse

def check_health(k,v,cloud,args):
    error_component = {}
    disk_status = []
    fandata = []
    if 'health' in v.keys():
        if v['health']['Health'] == 'Critical':
            error_component = {'cloud':str(cloud),'hvname':str(k),'hvhealth':str(v['health']['Health'])}
            if args.disk or args.all:
                physical = v['Disk_Health']['physical_disk'][0]
                for disk in physical:
                    if physical.get(disk)['drive_status']['Health'] == 'Critical':

                        critical_disk = {'physical_disk':{'disk_no':str(disk),'disk_health':str(physical.get(disk)['drive_status']['Health'])}}
                        disk_status.append(critical_disk)

                logical = v['Disk_Health']['logical_disk'][0]
                for l_disk in logical:

                    if logical.get(l_disk)['drive_status']['Health'] == 'Critical':
                        critical_disk = {'logical_disk':{'disk_no':str(l_disk),'disk_health':str(logical.get(l_disk)['drive_status']['Health'])}}
                        disk_status.append(critical_disk)
                error_component = {'cloud':str(cloud),'hvname':str(k),'hvhealth':str(v['health']['Health']),'diskhealth':disk_status}
            else:
                pass 
            if args.fan or args.all:
                for fan in v['Fans']:
                    if fan.get('Status')['Health'] == 'Critical':
                        fan_data={}
                        fan_data = {'Fan_name':str(fan.get('FanName')),'fan_health':str(fan.get('Status')['Health'])}
                        fandata.append(fan_data)
                error_component = {'cloud':str(cloud),'hvname':str(k),'hvhealth':str(v['health']['Health']),'fanhealth':fandata}
            if args.all:

                error_component = {'cloud':str(cloud),'hvname':str(k),'hvhealth':str(v['health']['Health']),'fanhealth':fandata, 'diskhealth':disk_status}      
            

    else:
        print("no information found for health")
    return error_component
    

def main():
    disk = []
    json_file = [x for x in glob.glob('*.json')]
    json_file.remove('parse.json')
    for i in range(0,len(json_file)):
        with open(json_file[i]) as f:
            parser = argparse.ArgumentParser()
            parser.add_argument("--h","--health",help="shows the basic health information",action="store_true",dest="health")
            parser.add_argument("--all","--all",help="shows all critical information",action="store_true",dest="all")
            parser.add_argument("--d","--disk",help="shows the critical disk health status",action="store_true",dest="disk")
            parser.add_argument("--f","--fan",help="shows the critical fan health status",action="store_true",dest="fan")
            args = parser.parse_args()
            data = json.load(f)
            output = data.get('system_health').get('data')
            cloud_name = data.get('system_health').get('cloud_name')
            result = {}
            for i in output:
                for k,v in i.items():
                    # Checking HV health 
                    error = check_health(k,v,cloud_name,args)
                    if error:
                        disk.append(error)
    print disk
    #result['data'] = disk
    #for j in result.get('data'):
    #      # ST2 execution
    #    token='***************************'
    #    st2_url='http://******:9101/v1/webhooks/test'
    #    headers = {'Accept': 'application/json','X-Auth-Token':token,'Content-Type':'application/json'}
    #    st2_fire = requests.post(st2_url,data=json.dumps(j),headers=headers)
   
if __name__ == '__main__':
    main() 
