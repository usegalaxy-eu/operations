# Quotas and Access
See [How to create new OAuth credentials for Google Drive](../runbooks/oauth-google-drive-credentials.md) for the credential procedure.
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
