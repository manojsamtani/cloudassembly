import re, os, sys, time, json, requests, getopt
from datetime import date
from requests.exceptions import HTTPError
import collections

cas_url='https://api.mgmt.cloud.vmware.com'
login_url=f'{cas_url}/iaas/api/login?2020-08-25'

def params(args):
        if len(args) != 1:
                try:
                        print('Arguments Passed To Script ', args[1:])
                        if '-t' not in args:
                                print('-t not found in params')
                        #if '-f' not in args or '-c' not in args or '-t' not in args:
                        #        print('Required Parameters (-f,-c,-t) not Provided By User')
                        #        print("""Usage: %s -f FILE_Path -c CHANGE_No -t API_Token"""%args[0])
                        #        exit()
                        else:
                                options, remainder = getopt.gnu_getopt(args[1:], 'f:c:t:')
                                cred_hash={}
                                for opt, arg in options:
                                        if opt in ('-f', '--file'):
                                                file_path=arg
                                                if os.path.exists(file_path) and os.path.isfile(file_path):
                                                        print('GIVEN HOSTS FILE EXISTS, PROCEEDING WITH PROGRAM......')
                                                        file=open(file_path)
                                                        cred_hash['servers_list']=file.read().split("\n")
                                                        #for line in open(file_path, 'r'):
                                                        #       cred_hash['servers_list'].append(line.rstrip('\n'))
                                                else:
                                                        print('Given Hosts File %s Does Not Exists, please specify correct path' %file_path)
                                                        exit()
                                        elif opt in ('-c', '--change'):
                                                cred_hash['change_no']=arg
                                        elif opt in ('-t', '--token'):
                                                cred_hash['token']=arg

                except getopt.error as msg:
                        sys.stdout = sys.stderr
                        print(msg)
                        print("""Usage: %s -f FILE_Path -c CHANGE_No -t API_Token"""%args[0])
                        exit()
        else:
                print("""Usage: %s -f FILE_Path -c CHANGE_No -t API_Token"""%args[0])
                exit()

        return cred_hash

def temp_token(api_token, cas_url):
        try:
                response = requests.post(login_url, json={'refreshToken': f'{api_token}'})
                print(response.status_code)
                print(json.loads(response.content))
                if response.status_code not in [200, 202, 301, 302]:
                        print('Error while Communicating to API URL %s' % response.content)
                        exit()

        except requests.exceptions.ConnectionError as c:
                raise SystemExit(c)
        except requests.exceptions.Timeout as t:
                raise SystemExit(t)
        except requests.exceptions.HTTPError as h:
                print("Could not login due to API Token Error....")
                raise SystemExit(h)
        
        return response.json()['token']

if __name__ == "__main__":
        ##Validate Params
        sparams=params(sys.argv)

        #change_no=sparams['change_no']
        #servers_list=[slist.strip() for slist in sparams['servers_list']]
        api_token=sparams['token']

        ## Set headers including temporary bearer token
        bearer = "Bearer "
        bearer_token=bearer + temp_token(api_token, cas_url)
        headers = {"Accept":"application/json", "Content-Type":"application/json", 'Authorization':bearer_token}
        network_list=requests.get(f"{cas_url}/iaas/api/network-profiles", headers = headers)
        network_hash=json.loads(network_list.content)

        for np in range(len(network_hash['content']) - 1):
                #print(network_hash['content'][1]['_links']['fabric-networks'])
                if network_hash['content'][np]['name'] == 'NJ4-PD-VM-VDS':
                    print(network_hash['content'][np]['name'])
                    for fn in network_hash['content'][np]['_links']['fabric-networks']['hrefs']:
                        fabric_network=requests.get(f'{cas_url}{fn}', headers = headers)
                        fabric_network_hash=collections.defaultdict(lambda : 'Not Found')
                        fabric_network_hash=json.loads(fabric_network.content)
                        print(f"\t{fabric_network_hash['name']} - {fabric_network_hash.get('cidr')} - \t{fabric_network_hash.get('tags')}")
        exit()
