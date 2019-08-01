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
