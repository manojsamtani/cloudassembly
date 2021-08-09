import re, os, sys, time, json, requests, getopt
from datetime import date
from requests.exceptions import HTTPError
import collections

cas_url='https://api.mgmt.cloud.vmware.com'
login_url=f'{cas_url}/iaas/api/login?2020-08-25'

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

#        servers_list=[slist.strip() for slist in sparams['servers_list']]
        api_token = sys.argv[1]
        print(api_token)
        ## Set headers including temporary bearer token
        bearer = "Bearer "
        bearer_token=bearer + temp_token(api_token, cas_url)
        print(bearer_token)