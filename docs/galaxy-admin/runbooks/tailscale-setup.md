# Tailscale
See [Tailscale dashboard endpoints](../reference/tailscale-endpoints.md) for the dashboards reachable via Tailscale.
We use it e.g. for making dashboards accessible that are hosted on machines in our private network which is not accessible from the university network.

## Install
~~~
curl -fsSL https://tailscale.com/install.sh | sh

tailscale up
~~~
Click on the authentication link and choose GitHub.
## Add user
Go to https://login.tailscale.com/admin/acls/visual/groups and add the new user to the usegalaxy-eu-admins group by using their GitHub handle. 
