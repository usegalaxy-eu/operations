# Tailscale
We use it e.g. for making dashboards accessible that are hosted on machines in our private network which is not accessible from the university network.

## Install
~~~
curl -fsSL https://tailscale.com/install.sh | sh

tailscale up
~~~
Click on the authentication link and choose GitHub.
## Add user
Go to https://login.tailscale.com/admin/acls/visual/groups and add the new user to the usegalaxy-eu-admins group by using their GitHub handle. 
## Dashboards
### Celery / Flower
http://celery-0.springhare-dinosaur.ts.net:5555/ or http://100.66.201.21:5555/workers 
Credentials in the vault or in /etc/flower/flowerconf.py on the celery host.
### Traefik
https://traefik.springhare-dinosaur.ts.net/dashboard/#/
