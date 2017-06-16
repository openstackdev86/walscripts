import json
import pdb
import requests
import glob

def check_health(k,v,cloud):
    error_component = {}
    hv_name = ""
    if 'health' in v.keys():
        if (v['health']['Health'] == 'Critical') or (v['health']['Health'] == 'Warning'):
            cloud_name = cloud.upper()
            if 'prod.walmart.com' not in k:
                hv_name = k+'.prod.walmart.com'

                error_component = {'cloud':str(cloud_name),'hvname':str(hv_name),'hvhealth':str(v['health']['Health'])}
            else:
                error_component = {'cloud':str(cloud_name),'hvname':str(k),'hvhealth':str(v['health']['Health'])}
    
    else:
        print("no information found for health")
    return error_component             

def main():
    disk = []
    api_key='MzI2OGM3NGI0NjkwZjkxMzAzNzNhZjUxYjhiZTMzMDE3YTVjNDc3MGY4YzE5MjA0NDQ3M2VmMDhhMTliMzljMg'
    st2_url='http://10.65.72.106:9101/v1/webhooks/'
    st2_header={'Accept': 'application/json','St2-Api-Key':api_key,'Content-Type':'application/json'}
    json_file = [x for x in glob.glob('/app/monitor/ilo_scripts/phase1/output_json/*.json')]
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
    print disk
    result['data'] = disk
    for data in result.get('data'):
        # ST2 execution
        if data.get('hvhealth') == 'Critical':
            url=st2_url+'hvilo'
            st2_fire = requests.post(url,data=json.dumps(data),headers=st2_header)
        elif data.get('hvhealth') == 'Warning':
            url=st2_url+'hvilodegraded'
            st2_fire = requests.post(url,data=json.dumps(data),headers=st2_header)
        else:
            print("not able to find any Hv with Critical/Warning state")   

if __name__ == '__main__':
    main()
