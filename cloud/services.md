---
title: Galaxy Europe Services
---

# TIaaS

- [Admin web interface](https://usegalaxy.eu/tiaas/admin/login/?next=/tiaas/admin/)
- service lives on [sn06](https://github.com/usegalaxy-eu/infrastructure-playbook/blob/4e6121da8af500dfe878c312243be49807ac5f48/sn06.yml#L152)
- Deployed with the [usegalaxy_eu.tiaas2](https://github.com/galaxyproject/ansible-tiaas2) Ansible role using this [vars](https://github.com/usegalaxy-eu/infrastructure-playbook/blob/master/group_vars/tiaas.yml)

# Grafana

- lives on stats.galaxyproject.eu
- [playbook](https://github.com/usegalaxy-eu/infrastructure-playbook/blob/master/grafana.yml)
- [VM definition](https://github.com/usegalaxy-eu/infrastructure/blob/main/instance_core_stats.tf)
- [Grafana dashboards](https://github.com/usegalaxy-eu/grafana-dashboards)
- Open issues: [244](https://github.com/usegalaxy-eu/infrastructure-playbook/issues/244), [245](https://github.com/usegalaxy-eu/infrastructure-playbook/issues/245)

# InfluxDB

- lives in influxdb.galaxyproject.eu
- [VM definition](https://github.com/usegalaxy-eu/infrastructure/blob/main/instance_core_influxdb.tf)
- [playbook](https://github.com/usegalaxy-eu/infrastructure-playbook/blob/master/influxdb.yml)
- It's a docker container

# RabbitMQ

- lives in mq.galaxyproject.eu
- [VM definition](https://github.com/usegalaxy-eu/infrastructure/blob/main/instance_core_mq.tf)
- [playbook](https://github.com/usegalaxy-eu/infrastructure-playbook/blob/master/mq.yml)
- [Admin web interface](https://mq.galaxyproject.eu/)
- It's a docker container


# usegalaxy-eu-bot

- Admin permisisons on usegalaxy-eu
- username + password in [github.yml](https://github.com/usegalaxy-eu/infrastructure-playbook/blob/master/secret_group_vars/github.yml)
- mostly jenkins using this account to comment things or pull code
- there is a grafana-gitter-bridge running on [grafana](#grafana) host

# Apollo

- managed by [Helena Rasche](https://github.com/hexylena)
- lives on apollo.internal.galaxyproject.eu
- [VM definition](https://github.com/usegalaxy-eu/infrastructure/blob/main/)
- [playbook](https://github.com/usegalaxy-eu/infrastructure-playbook/blob/master/apollo.yml)
- [playbook job](https://build.galaxyproject.eu/job/usegalaxy-eu/job/playbooks/job/apollo/)
- requires the apollo.war file on https://usegalaxy.eu/static/vgcn/
    - which is built/uploaded by [this job](https://build.galaxyproject.eu/job/usegalaxy-eu/job/apollo-builder/)

# CVMFS stratum 0

- managed by [Nate Corar](https://github.com/natefoo)
- lives on cvmfs-stratum0.galaxyproject.eu
- [VM definition](https://github.com/usegalaxy-eu/infrastructure/blob/main/instance_core_cvmfs0_eu.tf)

# Jenkins workers

There are 2 cluster nodes (Gold and Silver) managing Jenkins jobs. There is only one node per cluster at the moment but, more can be easily added [here](https://github.com/usegalaxy-eu/infrastructure/blob/5eb41f7847367c2fdf8cd6c653f8471fb421ac05/instance_core_jenkins-worker-gold.tf#L1)
and [here](https://github.com/usegalaxy-eu/infrastructure/blob/5eb41f7847367c2fdf8cd6c653f8471fb421ac05/instance_core_jenkins-worker-silver.tf#L1).
They are 2 clusters because if you need to operate/destroy/rebuild one of them, the other can continue to serve jenkins without interruptions.

- [VM definition Gold cluster](https://github.com/usegalaxy-eu/infrastructure/blob/main/instance_core_jenkins-worker-gold.tf)
- [VM definition Silver cluster](https://github.com/usegalaxy-eu/infrastructure/blob/main/instance_core_jenkins-worker-silver.tf#L1)

Both of them are established into the `private` network, so they can reach internal services.
