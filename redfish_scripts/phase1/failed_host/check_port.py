import socket
import sys
import json
import glob
import pdb

def get_hosts(cloud):
    host_portclosed = []
    global host_port
    host_port = {}
    host = [x for x in glob.glob('/app/monitor/ilo_scripts/phase1/failed_host/failed_'+cloud+'.json')]
    for i in range(0,len(host)):
        print host[i]
        with open(host[i]) as f:
            data = json.load(f)
            host_data = data.get('hosts')['data']
            for h in host_data:
                host_name = h.get('host').lstrip('https://')
                if not isOpen(host_name):
                    host_port = {"host":host_name,"port":"CLOSED"}
                    host_portclosed.append(host_port)
                else:
                    host_port = {"host":host_name,"port":"OPEN"}
                    host_portclosed.append(host_port)

        return host_portclosed

def isOpen(ip):
   s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
   s.settimeout(2)
   try:
      print("checking the hostname %s"%ip)
      s.connect((ip, int(443)))
      s.shutdown(2)
      return True
   except:
      return False


if __name__ == '__main__':
    #print isOpen("dal-appblx051-18-ilo.prod.walmart.com",443)
    cloud = sys.argv[1]
    out = get_hosts(cloud)
    temp = [x.get('host') for x in out if x.get('port') == 'CLOSED']
    for i in temp:
        print i
