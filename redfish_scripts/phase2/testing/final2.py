import json
import pdb
import requests
import glob

def check_critical(data):
    
    if (data != 'OK'):
        return True
    else:
        return False

def check_health(k,v,cloud):
    error_component = {}
    failure_str = ""
    hv_name = ""
    if 'health' in v.keys():
        if (v['health']['Health'] == 'Critical') or (v['health']['Health'] == 'Warning'):
            cloud_name = cloud.upper()
            pdb.set_trace()
            if 'Disk_Health' in v.keys():
                
                #failure_compnent["disk"]  = check_critical(v.get('Disk_Health').get('basic')['diskhealth'][0].get('Health'))
                if check_critical(v.get('Disk_Health').get('basic')['diskhealth'][0].get('Health')):
                    failure_str = "Disk"

            if 'Memory_status' in v.keys():
                #failure_compnent["Memory_status"]  = v.get('Memory_status')['Status']['HealthRollup']
                if check_critical(v.get('Memory_status')['Status']['HealthRollup']):
                    failure_str += "&Memory"
            if 'Processors' in v.keys():
                #failure_compnent["Processors"]  = v.get('Processors')[0]['Status']['HealthRollup']
                if check_critical(v.get('Processors')[0]['Status']['HealthRollup']):
                    failure_str += "&Processors"
            if 'Fans' in v.keys():
                fan_flag = 0
                for fan in v['Fans']:
                    if fan.get('Status')['Health'] != 'OK':
                        fan_flag = 1

                if fan_flag != 0:
                    failure_str += "&Fan"

            if 'prod.walmart.com' not in k:
                hv_name = k+'.prod.walmart.com'
                
                error_component = {'cloud':str(cloud_name),'hvname':str(hv_name),'hvhealth':str(v['health']['Health']),'critical_component':failure_str}
            else:
                error_component = {'cloud':str(cloud_name),'hvname':str(k),'hvhealth':str(v['health']['Health']),'critical_component':failure_str}

    else:
        print("no information found for health")
    return error_component

def main():
    disk = []
    api_key='MzI2OGM3NGI0NjkwZjkxMzAzNzNhZjUxYjhiZTMzMDE3YTVjNDc3MGY4YzE5MjA0NDQ3M2VmMDhhMTliMzljMg'
    st2_url='http://10.65.72.106:9101/v1/webhooks/'
    st2_header={'Accept': 'application/json','St2-Api-Key':api_key,'Content-Type':'application/json'}
    #json_file = [x for x in glob.glob('/app/monitor/ilo_scripts/phase1/output_json/*.json')]
    json_file = [x for x in glob.glob('dalstg2.json')]
    for i in range(0,len(json_file)):
        print(json_file[i])
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
    pdb.set_trace()
    print disk
    result['data'] = disk
    for data in result.get('data'):
        # ST2 execution
        if data.get('hvhealth') == 'Critical':
            url=st2_url+'hvilo'
            #st2_fire = requests.post(url,data=json.dumps(data),headers=st2_header)
        elif data.get('hvhealth') == 'Warning':
            url=st2_url+'hvilodegraded'
            #st2_fire = requests.post(url,data=json.dumps(data),headers=st2_header)
        else:
            print("not able to find any Hv with Critical/Warning state")

if __name__ == '__main__':
    main()
