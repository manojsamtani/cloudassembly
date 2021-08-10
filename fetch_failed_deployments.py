import requests, os, sys, json
from datetime import date
from requests.exceptions import HTTPError
from cas_generate_temp_token import temp_token
from fetch_common_data import getCloudAccounts

cas_url='https://api.mgmt.cloud.vmware.com'
login_url=f'{cas_url}/iaas/api/login?2020-08-25'

def deployment_cloud_acc_info(depid, headers):
    deployment_info_url = f'{cas_url}/deployment/api/deployments/{depid}/resources'
    print(deployment_info_url)
    fetch_dep_info = requests.get(deployment_info_url, headers = headers)
    cloud_acc_name = json.loads(fetch_dep_info.content)['content'][0]['properties']['resourceGroupName']
    return cloud_acc_name.split('/')[0]

def fetch_failed(headers):
    base_url=f'{cas_url}/deployment/api/deployments?status=DELETE_FAILED'
    ffd = requests.get(base_url, headers = headers)
    ffd_content = json.loads(ffd.content)
    total_pages = ffd_content['totalPages']
    print('Total Number Of Pages -> ', total_pages)

    fr_counter=1
    for pn in range(total_pages):
        pp_fail_records = requests.get(f'{base_url}&page={pn}', headers = headers)
        #print('Page {:<45}'.format(pn))
        pp_ffd_content = json.loads(pp_fail_records.content)
        print('Next page number %d...................................' % (pn+1))
        #if pn == 1:
            #print(pp_ffd_content['content'][an])
            #cloud_acc_name = deployment_cloud_acc_info(pp_ffd_content['content'][an]['id'], headers)
            #exit()

        for an in range(len(pp_ffd_content['content'])):
            print("{:<45} {:<45} {:<45}".format(fr_counter, pp_ffd_content['content'][an]['name'],  pp_ffd_content['content'][an]['id']))
            print(pp_ffd_content['content'][an]['id'])
            cloud_acc_name = deployment_cloud_acc_info(pp_ffd_content['content'][an]['id'], headers)

            print('In fetch_failed.... :-> ', cloud_acc_name)

            #cloud_startswith = pp_ffd_content['content'][an]['name'][0:4]
            #getCloudAccounts(cloud_acc_name, headers)
            exit()

            fr_counter+=1



if __name__ == "__main__":
    bearer = "Bearer "
    api_token = sys.argv[1]
    bearer_token = bearer + temp_token(api_token, cas_url)
    headers = {"Accept":"application/json", "Content-Type":"application/json", 'Authorization':bearer_token}

    fetch_failed(headers)
