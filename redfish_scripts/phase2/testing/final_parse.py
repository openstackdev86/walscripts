import json
import requests
import glob
import pdb

def check_health(k,v,cloud_name):
    error_component = {}
    failure_compnent = {}
    global critical_disk
    critical_disk = {}
    disk_status = []
    fandata = []
    if 'health' in v.keys():
        if v['health']['Health'] == 'Critical':
            pdb.set_trace()
            print("host %s overall health is %s"%(k,v['health']['Health']))
            if 'Disk_Health' in v.keys():
                if v.get('Disk_Health').get('basic')['diskhealth'][0].get('Health') == 'Critical':
                    failure_compnent["disk"]  = {v.get('Disk_Health').get('basic')['diskhealth'][0].get('Health')}
                 
            elif 'Memory_status' in v.keys():
                failure_compnent["Memory_status"]  = {v.get('Memory_status')['Status']['HealthRollup']}

            elif 'Processors' in v.keys():
                failure_compnent["Processors"]  = {v.get('Processors')[0]['Status']['HealthRollup']}
                
            if 'Fans' in v.keys():
                fan_flag = 0
                for fan in v['Fans']:
                    if fan.get('Status')['Health'] == 'Critical':
                        fan_flag = 1

                if fan_flag != 0:
                    failure_compnent["fan"] = {"Critical"}
        else:
            print("health ok")


                                         
    return failure_compnent

def main():
    disk = []
    json_file = [x for x in glob.glob('*.json')]
    json_file.remove('parse.json')
    pdb.set_trace()
    for i in range(0,len(json_file)):
        with open(json_file[i]) as f:
            data = json.load(f)
            output = data.get('system_health').get('data')
            cloud_name = data.get('system_health').get('cloud_name')
            result = {}
            for i in output:
                for k,v in i.items():
                    # Checking HV health
                    error = check_health(k,v,cloud_name)
                    if error:
                        disk.append(error)
    print disk

if __name__ == '__main__':
    main()
