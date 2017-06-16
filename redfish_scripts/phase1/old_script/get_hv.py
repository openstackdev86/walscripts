import pdb
import subprocess
import os
import json
from string import Template
    
def main():

    print("test")
    username="testu"
    password="testp"
     
    #token='***************************'
    st2_url='http://10.65.72.106:9101/v1/executions'
    token='fd81fb9c203349c4ad59ff465db5e9a2'
    data = {"token":token,"cloud":"DALIAAS1"}
    pdb.set_trace()
    #cmd = '''curl -X POST -H 'Accept-Encoding: gzip, deflate' -H 'Accept: */*' -H  'User-Agent: python-requests/2.8.1' -H 'Connection: keep-alive' -H 'X-Auth-Token: fd81fb9c203349c4ad59ff465db5e9a2' -H 'content-type: application/json' --data-binary '{"action": "default.action-test_gethvlist_webhook", "parameters": {"cloud": "DALIAAS1"}}' http://10.65.72.106:9101/v1/executions'''
    cmd = Template('''curl -X POST -H 'Accept-Encoding: gzip, deflate' -H 'Accept: */*' -H  'User-Agent: python-requests/2.8.1' -H 'Connection: keep-alive' -H 'X-Auth-Token: $token' -H 'content-type: application/json' --data-binary '{"action": "default.action-test_gethvlist_webhook", "parameters": {"cloud": $cloud}}' http://10.65.72.106:9101/v1/executions''')
    print cmd.substitute(data)
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
    pdb.set_trace()
    out = p.stdout.read()
    output = json.loads(out)
    exec_id = output.get('id')
    
    #st2_fire = requests.post(st2_url,auth=HTTPDigestAuth('testu', 'testp'),headers=headers)



if __name__ == '__main__':
    main()
