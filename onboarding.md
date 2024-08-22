# Things to remember when onboarding admins
## Jenkins
Access for the `playbooks` folder is not inherited or set by roles, indeed it is configured to **NOT** inherit any other ACL.  
Instead you have to set the permissions in the particular folder explicitly by adding the new user and giving the permissions in the table.  
![image](https://github.com/usegalaxy-eu/operations/assets/86979912/eb5dc1a0-fffd-4c15-b062-92ed4cb3670f)

## Grafana
For onboarding to Oncall and make someone an admin in Grafana see [monitoring.md](github.com/usegalaxy-eu/operations/blob/main/monitoring.md#how-to-onboard-a-new-user-to-oncall).
