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
                        if '-f' not in args or '-c' not in args or '-t' not in args:
                                print('Required Parameters (-f,-c,-t) not Provided By User')
                                print("""Usage: %s -f FILE_Path -c CHANGE_No -t API_Token"""%args[0])
                                exit()
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

def deployment_info(servers_list, headers):
        deployment_hash={}
        ## Loop over number of machines
        #print("Server ID %s Server Name %s\n" %('\t' * 5, '\t' * 3))
        for servers in servers_list:
                #print('------------- %s -------------' %servers)
                base_url=f'{cas_url}/deployment/api/deployments?$filter=(name%20eq%20%27{servers}%27)'
                #name%20eq%20%27{servers}%%%27)'
                url=base_url

                ## Fetch Machine id, projectId and orgId
                try:
                        deployment_list=requests.get(url, headers=headers)
                        deployment_list.raise_for_status()
                except requests.exceptions.Timeout as t:
                        print(servers, '\n_________')
                        print(SystemExit(t))
                        continue
                except requests.exceptions.HTTPError as e:
                        print(servers, '\n_________')
                        #print('Server %s not found in CAS' %(servers))
                        print(SystemExit(e))
                        continue

                ## Storing id, projectId and organizationId in Variables
                #print(json.loads(deployment_list.content))
                deployment_array=json.loads(deployment_list.content)

                if len(deployment_array['content']) == 0:
                        print('\nNO VM AVAILABLE BY NAME ', servers)
                        continue
                else:
                        deployment_id=deployment_array['content'][0]['id']
                        deployment_name=deployment_array['content'][0]['name']

                        ##Fetching Resource ID for Machine
                        resources_url=f'{cas_url}/deployment/api/deployments/{deployment_id}/resources'
                        #print(resources_url)
                        resources_list=requests.get(resources_url, headers=headers)
                        is_onboarded=json.loads(resources_list.content)['content'][0]['properties']
                        for ok,ov in is_onboarded.items():
                            if ok == 'ihsmCustomVMOnboard':
                                print(f'{deployment_name}:')
                                print(f'\t Is Onboarded : {is_onboarded[ok]}'.strip("\n"))
                                print(f"\t environmentName: {is_onboarded['environmentName']}")
                        resources_json_list=json.loads(resources_list.content)
                        resc_id=resources_json_list['content'][0]['id']

                #print("%s %s %s" %(deployment_id, '\t'*2, deployment_name))
                deployment_hash[deployment_name]={}
                deployment_hash[deployment_name]['id']=deployment_id
                deployment_hash[deployment_name]['resc_id']=resc_id
        exit()
        return deployment_hash


def create_snapshot(deployment_hash,headers,change_no):
        snapshot_status_requests={}
        description=f'As Per {change_no}'
        data= {
                "actionId": "Cloud.vSphere.Machine.Snapshot.Create",
                "inputs": {
                        "snapshotMemory": False,
                        "description": description,
                        "name": f'{change_no}'
                }
        }

        print('\n\nInitiating Snapshot for Following Servers: ')
        for server in deployment_hash.keys():
                deployment_id=deployment_hash[server]['id']
                resource_id=deployment_hash[server]['resc_id']

                snapshot_url=f'{cas_url}/deployment/api/deployments/{deployment_id}/resources/{resource_id}/requests?apiVersion=2019-01-15'
                print('%s\n\tSnapshot URL: - %s' %(server,snapshot_url))

                ## Request for Snapshot Creation
                try:
                        take_snapshot=requests.post(snapshot_url, data=json.dumps(data), headers=headers)
                        snapshot_output=json.loads(take_snapshot.content)
                        take_snapshot.raise_for_status()
                        time.sleep(3)
                        if take_snapshot.status_code not in [200, 202, 301, 302, 409, 404]:
                                print('Error while Communicating to API URL %s' % response.content)
                                continue

                except requests.exceptions.Timeout as t:
                        print(server, '\n_________')
                        print(SystemExit(t))
                        continue
                except requests.exceptions.HTTPError as e:
                        if take_snapshot.status_code == 409:
                                print('\n**************Snapshot Create/Delete Request Already Running %s******************\n' % take_snapshot.content)
                                continue
                        print(server, '\n_________')
                        print(SystemExit(e))
                        continue

                snapshot_status_requests[server]={}
                snapshot_status_requests[server]['id']=deployment_id
                snapshot_status_requests[server]['resc_id']=resource_id
                snapshot_status_requests[server]['request_id']=snapshot_output['id']
        
        return snapshot_status_requests

def status_snapshot(snapshot_hash,headers,change_no):
        snapshot_status_file=f'{change_no}.txt'
        fopen=open(snapshot_status_file, 'w+')
        
        for server_name in snapshot_hash.keys():
                time.sleep(1)
                deployment_id=snapshot_hash[server_name]['id']
                request_id=snapshot_hash[server_name]['request_id']
                ##Snapshot URL
                snapshot_status_url=f"{cas_url}/deployment/api/deployments/{deployment_id}/requests/{request_id}"

                try:
                        #Get Snapshot Status
                        show_request_status=requests.get(snapshot_status_url, headers=headers)
                        show_request_status.raise_for_status()
                        snapshot_output=json.loads(show_request_status.content)
                        print('%s\tSnapshot Status\t%s\n' %(server_name,snapshot_output['status']))

                        #Write Snapshot Status In File
                        fopen.write(f"{server_name}\t{snapshot_output['status']}\n")
                        #servers_snapshot_success[server_name]={}
                        #servers_snapshot_success[server_name]['status']=snapshot_output['status']

                except requests.exceptions.ConnectionError as c:
                        print(servers, '\n_________')
                        print(SystemExit(c))
                        continue
                except requests.exceptions.Timeout as t:
                        print(servers, '\n_________')
                        print(SystemExit(t))
                        continue
                except requests.exceptions.HTTPError as e:
                        print(servers, '\n_________')
                        print(SystemExit(e))
                        continue

        fopen.close()
        print(f'\nSnapshot Status Updated In File {snapshot_status_file}')

if __name__ == "__main__":
        ##Validate Params
        sparams=params(sys.argv)

        change_no=sparams['change_no']
        servers_list=[slist.strip() for slist in sparams['servers_list']]
        api_token=sparams['token']

        ## Set headers including temporary bearer token
        bearer = "Bearer "
        bearer_token=bearer + temp_token(api_token, cas_url)
        headers = {"Accept":"application/json", "Content-Type":"application/json", 'Authorization':bearer_token}
        network_list=requests.get(f"{cas_url}/iaas/api/network-profiles", headers = headers)
        network_hash=json.loads(network_list.content)

        for np in range(len(network_hash['content']) - 1):
                print(network_hash['content'][np]['name'])
                #print(network_hash['content'][1]['_links']['fabric-networks'])
                for fn in network_hash['content'][np]['_links']['fabric-networks']['hrefs']:
                        fabric_network=requests.get(f'{cas_url}{fn}', headers = headers)
                        fabric_network_hash=collections.defaultdict(lambda : 'Not Found')
                        fabric_network_hash=json.loads(fabric_network.content)
                        print(f"\t{fabric_network_hash['name']} - {fabric_network_hash.get('cidr')} - {fabric_network_hash.get('tags')}")
        exit()

        deployments_hash=deployment_info(servers_list, headers)
        if len(deployments_hash) == 0:
                print('deployments_hash hash is empty')
                exit()
        else:
                print('\nFinal Servers Hash \n')
                for server_name in deployments_hash.keys():
                        print('%s :' %server_name)
                        for key, value in deployments_hash[server_name].items():
                                print('\t%s: %s' %(key,value))

                print('\nNumber of Servers Found -> %d, %s' %(len(deployments_hash),list(deployments_hash.keys())))