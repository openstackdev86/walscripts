import json
import requests
import glob

def check_health(k,v,cloud):
    error_component = {}
    if 'health' in v.keys():
        if v['health']['Health'] == 'Critical':
            error_component = {'cloud':str(cloud),'hvname':str(k),'hvhealth':str(v['health']['Health'])}
    else:
        print("no information found for health")
    return error_component             

for filename in glob.glob('*.json'):
    with open(filename) as f:
        data = json.load(f)
        output = data.get('system_health').get('data')
        cloud_name = data.get('system_health').get('cloud_name')
        disk = []
        result = {}
        for i in output:
            for k,v in i.items():
                # Checking HV health 
                error = check_health(k,v,cloud_name)
                if error:
                    disk.append(error)
        print disk
        result['data'] = disk
        for j in result.get('data'):
            # ST2 execution
            token='***************************'
            st2_url='http://******:9101/v1/webhooks/test'
            headers = {'Accept': 'application/json','X-Auth-Token':token,'Content-Type':'application/json'}
            st2_fire = requests.post(st2_url,data=json.dumps(j),headers=headers)
    
