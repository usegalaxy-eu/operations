# Quotas and Access
This file covers documentation about the automated updating for user's disk quota and GPU access.

## Disk Quota Increase
Users can request more disk space using this [GoogleForm](https://usegalaxy.eu/quota-increase).
The responses are automatically collected in a GoogleSheet and we need to approve them manually by adding the date of approval to the corresponding line.  
The results sheet is then automatically processed by a [Jenkins job](https://build.galaxyproject.eu/job/usegalaxy-eu/job/quota-sync/) using this [repo](https://github.com/usegalaxy-eu/quota-sync).
It basically fetches the GoogleSheet and then uses the `process.py` script to request the disk quota via Galaxy's API.
For this to work the following things are needed:
1. A Google Account with access to the sheet
2. A Google `Oauth token`, `OAuth secret` and the account's email stored in corresponding json files. The correct files are created from Jenkins secrets.
2. A valid Galaxy API key
### How to create new OAuth credentials for Google Drive
1. Go to [https://console.cloud.google.com/apis/dashboard](https://console.cloud.google.com/apis/dashboard) and create a new `project`.
2. Click on `activated APIs and services` and search for `google drive`. Activate it.
3. Go to `OAuth-Consent-Screen` and create a new (external) service. Add the required fields, make sure to click on `add or remove areas` and add a `Drive API` ending with `/auth/drive.readonly`. Make sure to also add your Google account to the `test users` section.
4. Now create the `OAuth client ID` under `Login data`. Select `Create Credentials`/`OAuth Client ID` then select `Desktop client`.
5. Now we need to finally authorize this `OAuth Client` using the [gdrive tool](https://github.com/glotlabs/gdrive) (on your laptop). Follow the instructions in the [readme](https://github.com/glotlabs/gdrive?tab=readme-ov-file#add-google-account-to-gdrive). When you were successful, it should have created the 3 files under `~/.config/gdrive/`. Create new secrets for them in Jenkins and change the corresponding secrets in the project. Delete the `~/.config/gdrive/` directory on the Jenkins worker to ensure your credentials are copied and used.