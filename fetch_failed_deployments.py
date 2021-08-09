import requests, os, sys, json
from datetime import date
from requests.exceptions import HTTPError
from cas_generate_temp_token import temp_token

cas_url='https://api.mgmt.cloud.vmware.com'
login_url=f'{cas_url}/iaas/api/login?2020-08-25'

bearer = "Bearer "
api_token = sys.argv[1]
bearer_token = bearer + temp_token(api_token, cas_url)
headers = {"Accept":"application/json", "Content-Type":"application/json", 'Authorization':bearer_token}

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
    print('Moving to next page number %d..............................' % (pn+1))

    for an in range(len(pp_ffd_content['content'])):
      print("{:<45} {:<45}".format(fr_counter, pp_ffd_content['content'][an]['name']))
      fr_counter+=1
