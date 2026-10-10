# Apps / Dokku (Host apps.bi.privat)

[Dokku](https://dokku.com/docs/getting-started/installation/) is like Heroku, a Platform as a Service (PaaS), but selfhosted.
We use it to deploy smalls services (called 'apps'), like the street science community game [DNAnalyzer](https://github.com/StreetScienceCommunity/DNAnalyzer),
but also apps we rely on like ptdk, the Planemo Training Development Kit [(ptdk)](https://github.com/galaxyproject/ptdk/tree/main) and [Oembed](https://github.com/galaxyproject/oembed).

To deploy a service ('app') to Dokku, you first define it and then (git) push the code to the Dokku Deamon which then creates a container with your service.
Additionally you can manage domains/routing (internally uses NGINX), add a database server, environment variables etc.

## How do I interact with the Dokku Daemon

We have deployed Dokku in a container, because it is not available for RPM based distros anymore.
To interact with it, login to apps.bi.privat and start a container shell using `docker exec -it dokku /bin/bash`.  

Now you can use the CLI like described in the [official docs](https://dokku.com/docs/getting-started/installation/)

Eg. you can list deployed services
~~~
dokku apps
~~~

## How do I add a service to Dokku?

The apps are deployed in two steps, the router is added in traefik;
1. Ansible [infrastructure-playbook/dokku.yml](https://github.com/usegalaxy-eu/infrastructure-playbook/blob/master/dokku.yml) here the apps are defined in the `group_vars/dokku.yml` in a list called `apps`. This list is also used to define domains and related NGINX rules in dokku.
2. Once the app is defined, you can push code to it. This happens in GitHub Actions in the respective app's source repository. E.g. for ptdk [here](https://github.com/galaxyproject/ptdk/blob/main/.github/workflows/deploy.yml).
3. The traefik route for the apps are handled in a [template](https://github.com/usegalaxy-eu/infrastructure-playbook/blob/master/files/traefik/rules/template-apps-router.yml). To add a app, add a line at the end like `{{template "apps" "my-new-app"}}` where `my-new-app` is the 2. level subdomain. A router for `my-new-app.apps.galaxyproject.eu` will be created and the requests directed to dokku.bi.privat. (The reason this is not auto-created from the above mentioned `apps` list, is that the traefik rules are linted and the linter can not deal with jinja2 templates.)
4. Be sure to actually have a subdomain that is pointing to traefik, done in [infrastructure/dns.tf](https://github.com/usegalaxy-eu/infrastructure/blob/main/dns.tf)
