import re, os, sys, time, json, requests, getopt
import pymsteams
from datetime import date
from requests.exceptions import HTTPError
from cas_generate_temp_token import temp_token

cas_url='https://api.mgmt.cloud.vmware.com'
login_url=f'{cas_url}/iaas/api/login?2020-08-25'
teams_cas_url='https://infocorp365.webhook.office.com/webhookb2/def0327b-5783-40bb-857b-be063c6fb185@c1156c2f-a3bb-4fc4-ac07-3eab96da8d10/IncomingWebhook/66a5f9e8cc564b258e68d848fff58d8a/b4ed2d1f-598e-4742-98f0-fb4b27c503e7'

def send_to_teams(cloud_account_name,fail_status):
        myTeamsMessage = pymsteams.connectorcard(f"{teams_cas_url}")
        myTeamsMessage.title("FAILURE")
        myTeamsMessage.text(f"Cloud Account - {cloud_account_name}")
        
        count = 1
        for k,v in fail_status.items():
                if k == 'imageEnumerationTaskState':
                        section_imageEnumerationTaskState = pymsteams.cardsection()
                        section_imageEnumerationTaskState.text(f"Account\_Image\_State\_Sync - {v}")
                        myTeamsMessage.addSection(section_imageEnumerationTaskState)

                if k == 'enumerationTaskState':
                        section_enumerationTaskState = pymsteams.cardsection()
                        section_enumerationTaskState.text(f"Account\_Data\_State\_Sync - {v}")
                        myTeamsMessage.addSection(section_enumerationTaskState)

        myTeamsMessage.send()

def getCloudAccounts(headers):
        acc_list=requests.get(f"{cas_url}/iaas/api/cloud-accounts", headers = headers)
        cloud_accs=json.loads(acc_list.content)
        print(cloud_accs['content'])
        #print(f"Location \t\t Cloud_Account_User \t\t\t Account_Data_State_Sync \t\t\t Account_Image_State_Sync")
        per_cloud_acc={}
        print("{:<40} {:<40} {:<40} {:<40}".format("Cloud_Account_Name", "Cloud_Account_User", "Account_Data_State_Sync", "Account_Image_State_Sync"))
        
        for an in range(len(cloud_accs['content'])):
            fail_status={}
            cloud_accs_loop=cloud_accs['content'][an]
            cloud_account_name=cloud_accs['content'][an]['cloudAccountProperties'].get('sddcId', cloud_accs['content'][an]['name'])
            cloud_account_user_name=cloud_accs['content'][an]['cloudAccountProperties'].get('privateKeyId', 'Not Defined')
            cloud_account_data_sync_state=cloud_accs['content'][an]['customProperties']['enumerationTaskState']
            cloud_account_image_sync_state=cloud_accs['content'][an]['customProperties']['imageEnumerationTaskState']
            #print(json.loads(requests.get(f"{cas_url}/iaas/api/cloud-accounts/{cloud_accs['content'][an]['id']}", headers = headers).content))
            #exit()
            if cloud_account_image_sync_state not in ['STARTED', 'FINISHED']:
                fail_status['imageEnumerationTaskState']='failed'
                
            if cloud_account_data_sync_state not in ['STARTED', 'FINISHED']:
                fail_status['enumerationTaskState']='failed'

            if fail_status:
                print("\033[31m{:<40} {:<40} {:<40} {:<40}\033[39m".format(cloud_account_name,cloud_account_user_name,cloud_account_data_sync_state,cloud_account_image_sync_state))
                send_to_teams(cloud_account_name,fail_status)
            else:
                print("{:<40} {:<40} {:<40} {:<40}".format(cloud_account_name,cloud_account_user_name,cloud_account_data_sync_state,cloud_account_image_sync_state))

def getZones(headers):
        cas_zones_list=requests.get(f"{cas_url}/iaas/api/zones", headers = headers)
        cas_zones=json.loads(cas_zones_list.content)
        #print(cas_zones['content'])
        print("\n{:<45} {:<45}\n".format("Cloud_Zones", "Cloud_Zones_External_ID"))

        for an in range(len(cas_zones['content'])):
                print("{:<45} {:<45}".format(cas_zones['content'][an]['name'], cas_zones['content'][an]['externalRegionId']))
                #print(cas_zones['content'][an]['name'])

def getRegions(headers):
        cas_regions_list=requests.get(f"{cas_url}/iaas/api/regions", headers = headers)
        cas_regions=json.loads(cas_regions_list.content)
        #print(cas_regions['content'])

        print("\n{:<40} {:<40}\n".format("Cloud_Region", "Cloud_Region_External_ID"))
        for an in range(len(cas_regions['content'])):
                print("{:<40} {:<40}".format(cas_regions['content'][an]['name'], cas_regions['content'][an]['externalRegionId']))

def getAbx(headers):
        cas_abx_list=requests.get(f"{cas_url}/abx/api/resources/actions", headers = headers)
        cas_abx=json.loads(cas_abx_list.content)
        print(cas_abx['content'])

        for an in range(len(cas_abx['content'])):
                print(cas_abx['content'][an]['name'])

if __name__ == "__main__":
        ##Validate Params

        bearer = "Bearer "
        api_token = sys.argv[1]
        bearer_token = bearer + temp_token(api_token, cas_url)
        headers = {"Accept":"application/json", "Content-Type":"application/json", 'Authorization':bearer_token}

        sparams=params(sys.argv)
        api_token=sparams['token']

        ## Set headers including temporary bearer token
        bearer = "Bearer "
        bearer_token=bearer + temp_token(api_token, cas_url)
        headers = {"Accept":"application/json", "Content-Type":"application/json", 'Authorization':bearer_token}
        getCloudAccounts(headers)
        exit()
        getAbx(headers)
        getZones(headers)
        getRegions(headers)
        getCloudAccounts(headers)
