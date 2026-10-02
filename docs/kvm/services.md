---
title: Galaxy Europe Services
---
# TIaaS

- [Admin web interface](https://usegalaxy.eu/tiaas/admin/login/?next=/tiaas/admin/)
- service lives on [sn09](https://github.com/usegalaxy-eu/infrastructure-playbook/blob/master/sn09.yml)
- Deployed with the [usegalaxy_eu.tiaas2](https://github.com/galaxyproject/ansible-tiaas2) Ansible role using this [vars](https://github.com/usegalaxy-eu/infrastructure-playbook/blob/master/group_vars/tiaas.yml)

# Grafana

- lives on stats.galaxyproject.eu
- [VM definition](https://github.com/usegalaxy-eu/kvm-infrastructure/blob/master/vms.tf)
- [playbook](https://github.com/usegalaxy-eu/infrastructure-playbook/blob/master/grafana.yml)
- [Grafana dashboards](https://github.com/usegalaxy-eu/grafana-dashboards)
- Open issues: [244](https://github.com/usegalaxy-eu/infrastructure-playbook/issues/244), [245](https://github.com/usegalaxy-eu/infrastructure-playbook/issues/245)

# [InfluxDB](../databases/influxdb.md)

- lives in influxdb.galaxyproject.eu
- [VM definition](https://github.com/usegalaxy-eu/kvm-infrastructure/blob/master/vms.tf)
- [playbook](https://github.com/usegalaxy-eu/infrastructure-playbook/blob/master/influxdb.yml)
- It's a docker container

# RabbitMQ

- lives in mq.galaxyproject.eu
- [VM definition](https://github.com/usegalaxy-eu/kvm-infrastructure/blob/master/vms.tf)
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
- lives on apollo.bi.privat
- [VM definition](https://github.com/usegalaxy-eu/kvm-infrastructure/blob/master/vms.tf)
- [playbook](https://github.com/usegalaxy-eu/infrastructure-playbook/blob/master/apollo.yml)
- [playbook job](https://build.galaxyproject.eu/job/usegalaxy-eu/job/playbooks/job/apollo/)
- requires the apollo.war file on https://usegalaxy.eu/static/vgcn/
    - which is built/uploaded by [this job](https://build.galaxyproject.eu/job/usegalaxy-eu/job/apollo-builder/)

# CVMFS stratum 0

- managed by [Nate Corar](https://github.com/natefoo)
- lives on cvmfs-stratum0.galaxyproject.eu
- [VM definition](https://github.com/usegalaxy-eu/kvm-infrastructure/blob/master/vms.tf)
- It hosts Singularity images and rsync's them every hour to the CVMFS from [depot](https://depot.galaxyproject.org/singularity/)
- Ansible Playbook: https://github.com/galaxyproject/infrastructure-playbook/tree/main/host_vars/cvmfs-stratum0.galaxyproject.eu
- Status dashboard: https://stats.galaxyproject.org/d/VdSc7u54z/cvmfs

# Jenkins

The Jenkins master runs on the bare metal node `sn12.galaxyproject.eu` (the same host that
runs the [KVM infrastructure](./README.md)). Build jobs run on the `worker-0-kvm-build`
VM (`worker-0-kvm-build.bi.privat`), defined in the
[VM definitions](https://github.com/usegalaxy-eu/kvm-infrastructure/blob/master/vms.tf).

- [Jenkins master](https://build.galaxyproject.eu/)
- [playbook](https://github.com/usegalaxy-eu/infrastructure-playbook/blob/master/dnbd3_libvirt_jenkins.yml)
