# How it works internally

See [Custom Galaxy Subdomain](../runbooks/subdomains.md) for the setup procedure.
There is a [nginx location directive](https://github.com/usegalaxy-eu/infrastructure-playbook/blob/d14a9497cdaeab1fabda723083fb79340cc6c7ec/templates/nginx/galaxy-main.j2#L130) that redirects the front page request from the `subdomain/welcome.html` to the file `/opt/multisite-css/$host.html`, hosted locally into the Galaxy server.

This mechanism rely on the default value of the [welcome_url](https://github.com/galaxyproject/galaxy/blob/ae89745bfc1646ae231dfd8a42b6f20ae2399f80/lib/galaxy/config/sample/galaxy.yml.sample#L1034) variable in the Galaxy configuration. If you change it, then you have to modify the nginx location directive accordingly.
