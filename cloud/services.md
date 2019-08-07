---
title: Galaxy Europe Services
---

# TIaaS

- [spreadsheet](https://docs.google.com/spreadsheets/d/17e8BYfvr54-mqi8pEUji_kxN4wEAyGV1JdWy-A80b20/edit)
- service lives on sn04
- https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/hxr.tiaas

# Grafana

- lives on stats.galaxyproject.eu
- [playbook](https://github.com/usegalaxy-eu/infrastructure-playbook/blob/master/grafana.yml)
- [VM definition](https://github.com/usegalaxy-eu/infrastructure/blob/master/instance_stats.tf)

# usegalaxy-eu-bot

- Admin permisisons on usegalaxy-eu
- username + password in [github.yml](https://github.com/usegalaxy-eu/infrastructure-playbook/blob/master/secret_group_vars/github.yml)
- mostly jenkins using this account to comment things or pull code
- there is a grafana-gitter-bridge running on [grafana](#grafana) host

# Apollo

- lives on apollo.internal.galaxyproject.eu
- [vm definition](https://github.com/usegalaxy-eu/infrastructure/blob/master/instance_apollo.tf)
- [playbook](https://github.com/usegalaxy-eu/infrastructure-playbook/blob/master/apollo.yml)
- [playbook job](https://build.galaxyproject.eu/job/usegalaxy-eu/job/playbooks/job/apollo/)
- requires the apollo.war file on https://usegalaxy.eu/static/vgcn/
	- which is built/uploaded by [this job](https://build.galaxyproject.eu/job/usegalaxy-eu/job/apollo-builder/)

