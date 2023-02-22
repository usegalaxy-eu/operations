# [Infrastructure Playbook repository](https://github.com/usegalaxy-eu/infrastructure-playbook)

## Generic introduction
* This repository contains the [Ansible](https://www.ansible.com/) playbooks, roles, etc for the European Galaxy server. It is used to deploy the infrastructure for the European Galaxy server through [Jenkins](https://build.galaxyproject.eu/job/usegalaxy-eu/). All configurational changes related to the [Galaxy EU](https://usegalaxy.eu) are made through this repository.
* Galaxy EU compute infrastructure is run on the [BW OpenStack cloud](https://portal.bw-cloud.org/). At the time of writing (21/02/2023) our cloud is of size 8488 VCPUs, 44.6 TB RAM, 162.6 TB storage. Additionally, a few petabytes of [storage](https://github.com/usegalaxy-eu/operations/blob/main/storage.md) is also mounted (NFS) in the cloud.
* The compute infrastructure (cloud cluster) is configured through [VGCN infrastructure repo](https://github.com/usegalaxy-eu/vgcn-infrastructure) where we define what [cloud images](https://github.com/usegalaxy-eu/vgcn) should be used, the size of the cloud cluster, the number of VMs, the cloud network, the cloud security groups, etc.
* The cloud is configured through this [infrastructure repo](https://github.com/usegalaxy-eu/infrastructure) using [Terraform](https://www.terraform.io/). The underlying cloud hardware, storage, network, etc are managed by the compute center of the University of Freiburg. For DNS records we use [Amazon's Route53](https://aws.amazon.com/route53/).
* Some documentation related to [services](https://github.com/usegalaxy-eu/operations/blob/main/cloud/services.md) and IT operations are available in this [operations repo](https://github.com/usegalaxy-eu/operations)
* For Galaxy Admin training you can refer [here](https://training.galaxyproject.org/training-material/topics/admin/)
* For monitoring of the Galaxy EU infrastructure we use [Grafana](https://grafana.com/). The dashboards are available [here](https://stats.galaxyproject.eu/)

## Ansible
* [Ansible](https://www.ansible.com/) is an open-source software provisioning, configuration management, and application-deployment tool enabling infrastructure as code.
* The basic components of Ansible can be found [here](https://docs.ansible.com/ansible/latest/network/getting_started/basic_concepts.html). Understanding this is important to understand this repo.

## Our repo structure
* [files](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/files): contains files/configs that are used by the playbooks/roles
* [group_vars](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/group_vars) and [host_vars](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/host_vars): contains variables that are used by the playbooks specific to certain host/group defined in the [inventory file](https://github.com/usegalaxy-eu/infrastructure-playbook/blob/master/hosts). For every playbook we have an associated group_vars/host_vars file where we define the variables that are used by the playbook and the roles that are included/imported in the playbook.
* [roles](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles): contains the roles that are included/imported in the playbooks. The roles contain a set of tasks to configure a host to serve a certain purpose like configuring a service.
* [secret_group_vars](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/secret_group_vars): This is our vault. It contains the passwords and other sensitive information that is used by the playbooks/roles. The files are encrypted using [Ansible Vault](https://docs.ansible.com/ansible/latest/user_guide/vault.html).
* [templates](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/templates): contains the templates that are used by the playbooks/roles. The templates are used to generate the final configuration files that are used by the services. The templates are written in [Jinja2](https://jinja.palletsprojects.com/en/3.0.x/) syntax.
ansible.cfg: contains the configuration of Ansible. This is used to define the location of the inventory file, the vault password file, etc.
* [hosts](https://github.com/usegalaxy-eu/infrastructure-playbook/blob/master/hosts): contains the inventory of the hosts that are managed by Ansible.

## Playbooks
The playbooks are located in the [root directory](https://github.com/usegalaxy-eu/infrastructure-playbook) of the repo.

The playbooks are:

  * [apollo.yml](https://github.com/usegalaxy-eu/infrastructure-playbook/blob/master/apollo.yml): [Apollo](https://genomearchitect.readthedocs.io/en/latest/) is a genome annotation web-based editor. This can be accessed through Galaxy to view, edit, and annotate genomes. Uses Tomcat, therefore run on a separate server. Additional information can be found [here](https://github.com/usegalaxy-eu/operations/blob/f8062472110116a4ddf3035c3d43374443ec235e/cloud/services.md#apollo)
  * [beacon.yml](https://github.com/usegalaxy-eu/infrastructure-playbook/blob/master/beacon.yml): [Beacon](https://beacon-project.io/) is a service that allows to query for the presence of specific variants in a given dataset. We provide this service as part of our Galaxy EU instance. This is run on a [VM](https://github.com/usegalaxy-eu/infrastructure/blob/main/instance_dedicated_beacon.tf) on the cloud.
  * [build.yml](https://github.com/usegalaxy-eu/infrastructure-playbook/blob/master/build.yml): This playbook is used to setup our [Jenkins server](https://build.galaxyproject.eu/).
  * [celery.yml](https://github.com/usegalaxy-eu/infrastructure-playbook/blob/master/celery.yml): This playbook is used to setup the [Celery](https://docs.celeryq.dev/en/stable/) node(s) that are used by Galaxy for running various jobs. For more information refer to this [doc](https://github.com/usegalaxy-eu/operations/blob/main/celery.md) and our [training material](https://training.galaxyproject.org/training-material/topics/admin/tutorials/celery/slides.html#1)
  * [cvmfs.yml](https://github.com/usegalaxy-eu/infrastructure-playbook/blob/master/cvmfs.yml): This playbook is used to setup the [CernVM-FS](https://cvmfs.readthedocs.io/en/stable/cpt-repo.html) server that is used by Galaxy to serve the reference data. Refer to these training materials for more information: [Reference Data with CVMFS](https://training.galaxyproject.org/training-material/topics/admin/tutorials/cvmfs/tutorial.html), and [Reference Data with CVMFS without Ansible](https://training.galaxyproject.org/training-material/topics/admin/tutorials/cvmfs-manual/tutorial.html)
  * [galaxy-test.yml](https://github.com/usegalaxy-eu/infrastructure-playbook/blob/master/galaxy-test.yml): This playbook is used to setup the Galaxy test instance. This is used to perform tests on the Galaxy codebase before deploying it to the main Galaxy instance.
  * [grafana.yml](https://github.com/usegalaxy-eu/infrastructure-playbook/blob/master/grafana.yml): This playbook is used to setup the [Grafana](https://grafana.com/) server that is used to [monitor our Galaxy instance](https://stats.galaxyproject.eu/). Refer to this [doc](https://github.com/usegalaxy-eu/operations/blob/f8062472110116a4ddf3035c3d43374443ec235e/cloud/services.md#grafana) and here is the training material [Galaxy Monitoring with Telegraf and Grafana](https://training.galaxyproject.org/training-material/topics/admin/tutorials/monitoring/tutorial.html)
  * [incoming.yml](https://github.com/usegalaxy-eu/infrastructure-playbook/blob/master/incoming.yml): This playbook is used to setup our [incoming FTP server](https://incoming.galaxyproject.eu/) through which users can upload their data to Galaxy. _Though this service is not retired, now we use [tus.io](https://tus.io/) for uploading data to Galaxy_. Our training materials on: [TUS](https://training.galaxyproject.org/training-material/topics/admin/tutorials/tus/tutorial.html) and [FTP](https://training.galaxyproject.org/training-material/topics/admin/tutorials/ftp/tutorial.html).
  * [influxdb.yml](https://github.com/usegalaxy-eu/infrastructure-playbook/blob/master/influxdb.yml): This playbook is used to setup the [InfluxDB](https://www.influxdata.com/) server that is used to store the metrics that are collected by Telegraf. Refer to [this](https://github.com/usegalaxy-eu/operations/blob/main/influxdb.md) and [this](https://github.com/usegalaxy-eu/operations/blob/main/cloud/services.md#influxdb) doc. Here is the [training material](https://training.galaxyproject.org/training-material/topics/admin/tutorials/monitoring/tutorial.html#influxdb)
  * [mq.yml](https://github.com/usegalaxy-eu/infrastructure-playbook/blob/master/mq.yml): This playbook is used to setup the [RabbitMQ](https://www.rabbitmq.com/) server that is used by Galaxy. Refer [here](https://github.com/usegalaxy-eu/operations/blob/f8062472110116a4ddf3035c3d43374443ec235e/cloud/services.md#rabbitmq) and [here](https://github.com/usegalaxy-eu/operations/blob/main/celery.md#chapter-one-down-the-rabbit-hole) for details.
  * [plausible.yml](https://github.com/usegalaxy-eu/infrastructure-playbook/blob/master/plausible.yml): This playbook is used to setup the [Plausible](https://plausible.io/) server that is used to collect the [analytics](https://stats.galaxyproject.eu/) for our Galaxy instance.
  * [sn05.yml](https://github.com/usegalaxy-eu/infrastructure-playbook/blob/master/sn05.yml): This playbook is used to setup the Galaxy PostgreSQL database server and also the [HTCondor](https://htcondor.org/) cluster manager.
  * [sn06.yml](https://github.com/usegalaxy-eu/infrastructure-playbook/blob/master/sn06.yml): This playbook configures the [Galaxy server](https://usegalaxy.eu). This is the main Galaxy server that is used by the users. This we denote as `headnode 1`. Refer to this [training material](https://training.galaxyproject.org/training-material/topics/admin/tutorials/ansible-galaxy/tutorial.html) to set up Galaxy.
  * [sn07.yml](https://github.com/usegalaxy-eu/infrastructure-playbook/blob/master/sn07.yml): This playbook also configures the `galaxy server` but this is not in production (for now 22/02/2023). This we denote as `headnode 2`. Refer to this [training material](https://training.galaxyproject.org/training-material/topics/admin/tutorials/ansible-galaxy/tutorial.html) to set up Galaxy.
  * [syn-to-nfs.yml](https://github.com/usegalaxy-eu/infrastructure-playbook/blob/master/sync-to-nfs.yml): This playbook is used to sync the data of the Galaxy codebase on `headnode 1 (sn06)` to a NFS server. This is then synced to all nodes that needs the up-to-date Galaxy codebase and configuration files.
  * [upload.yml](https://github.com/usegalaxy-eu/infrastructure-playbook/blob/master/upload.yml): This playbook sets up the [TUS](https://tus.io/) server that is used to upload data to Galaxy. Refer to this [training material](https://training.galaxyproject.org/training-material/topics/admin/tutorials/tus/tutorial.html) to set up TUS.

  ## Roles
Our locally maintained Ansible roles are located in the [roles directory](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles). Also, we maintain several other roles and all of them are in their own github repositories and can be found in our [organization](https://github.com/orgs/usegalaxy-eu/repositories). Most of these roles are published on [Ansible Galaxy](https://galaxy.ansible.com/usegalaxy_eu). In addition to our roles we also use roles from the [galaxyproject (Galaxy USA instance)](https://galaxy.ansible.com/galaxyproject) All the roles we use are listed in our [requirements.yaml](https://github.com/usegalaxy-eu/infrastructure-playbook/blob/master/requirements.yaml) file. These roles can be installed by running the following command:

    ansible-galaxy install -r requirements.yaml

### [Local roles](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles)
* _Separate repo: Whether the role has its own repo or is it a local role located and available only in the [infrastructure_playbook](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles) repo_
* _Still being used: Whether the role is included/imported in any of the above listed playbooks_

| Roles | Separate repo | Still being used | Description |
| :--- | :---: | :---: | :--- |
| [devops.tomcat7](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/devops.tomcat7) |  | :heavy_check_mark: | Installs Tomcat 7 on RedHat/CentOS Linux servers |
| [dj-wasabi.telegraf](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/dj-wasabi.telegraf) |  | :heavy_check_mark: | Installs and configures [telegraf](https://www.influxdata.com/time-series-platform/telegraf/) |
| [docker](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/docker) |  |  | Installs and configures docker; sets up SSL certs |
| [galaxyprojectdotorg.proftpd](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/galaxyprojectdotorg.proftpd) |  | :heavy_check_mark: | Installs, configures and manges [proftpd](http://www.proftpd.org/) (FTP) server.|
| [geerlingguy.haproxy](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/geerlingguy.haproxy) |  |  | Installs [HAProxy](https://www.haproxy.org/) |
| [geerlingguy.nginx](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/geerlingguy.nginx) |  |  | Installs and configures Nginx |
| [hostname](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/hostname) |  | :heavy_check_mark: | Set's system's hostname |
| [htcondor](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/htcondor) |  |  | Installs and configures HTCondor |
| [hxr.admin-tools](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/hxr.admin-tools) |  |  |
| [hxr.api-check](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/hxr.api-check) |  |  |
| [hxr.apollo](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/hxr.apollo) |  |  |
| [hxr.autofs](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/hxr.autofs) |  |  |
| [hxr.autofs-format-n-mount](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/hxr.autofs-format-n-mount) |  |  |
| [hxr.aws-cli](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/hxr.aws-cli) |  |  |
| [hxr.dns](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/hxr.dns) |  |  |
| [hxr.docker-ssl](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/hxr.docker-ssl) |  |  |
| [hxr.docker-ssl-client](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/hxr.docker-ssl-client) |  |  |
| [hxr.exclude-repo](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/hxr.exclude-repo) |  |  |
| [hxr.galaxy-cron](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/hxr.galaxy-cron) |  |  |
| [hxr.galaxy-echo-tool](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/hxr.galaxy-echo-tool) |  |  |
| [hxr.galaxy-log-dir](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/hxr.galaxy-log-dir) |  |  |
| [hxr.galaxy-nonreproducible-tools](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/hxr.galaxy-nonreproducible-tools) |  |  |
| [hxr.grafana-gitter-bridge](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/hxr.grafana-gitter-bridge) |  |  |
| [hxr.gx-cookie-proxy](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/hxr.gx-cookie-proxy) |  |  |
| [hxr.haproxy-error-pages](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/hxr.haproxy-error-pages) |  |  |
| [hxr.install-to-venv](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/hxr.install-to-venv) |  |  |
| [hxr.monitor-cluster](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/hxr.monitor-cluster) |  |  |
| [hxr.monitor-cvmfs](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/hxr.monitor-cvmfs) |  |  |
| [hxr.monitor-email](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/hxr.monitor-email) |  |  |
| [hxr.monitor-galaxy](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/hxr.monitor-galaxy) |  |  |
| [hxr.monitor-galaxy-journalctl](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/hxr.monitor-galaxy-journalctl) |  |  |
| [hxr.monitor-galaxy-queue](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/hxr.monitor-galaxy-queue) |  |  |
| [hxr.monitor-squid](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/hxr.monitor-squid) |  |  |
| [hxr.monitor-ssl](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/hxr.monitor-ssl) |  |  |
| [hxr.postgres-connection](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/hxr.postgres-connection) |  |  |
| [hxr.remap-user](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/hxr.remap-user) |  |  |
| [hxr.replace-galaxy-user](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/hxr.replace-galaxy-user) |  |  |
| [hxr.sentry](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/hxr.sentry) |  |  |
| [hxr.simple-nagios](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/hxr.simple-nagios) |  |  |
| [hxr.zfs-monit](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/hxr.zfs-monit) |  |  |
| [jasonroyle.rabbitmq](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/jasonroyle.rabbitmq) |  |  |
| [linuxhq.yum_cron](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/linuxhq.yum_cron) |  |  |
| [matterircd](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/matterircd) |  |  |
| [multinic](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/multinic) |  |  |
| [multinic-old](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/multinic-old) |  |  |
| [pgs](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/pgs) |  |  |
| [sentry](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/sentry) |  |  |
| [ssh-host-resign](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/ssh-host-resign) |  |  |
| [ssh-host-sign](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/ssh-host-sign) |  |  |
| [usegalaxy-eu.bashrc](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/usegalaxy-eu.bashrc) |  |  |
| [usegalaxy-eu.create-user](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/usegalaxy-eu.create-user) |  |  |
| [usegalaxy-eu.error-pages](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/usegalaxy-eu.error-pages) |  |  |
| [usegalaxy-eu.fix-ancient-ftp-data](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/usegalaxy-eu.fix-ancient-ftp-data) |  |  |
| [usegalaxy-eu.fix-failing-to-fail-jobs](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/usegalaxy-eu.fix-failing-to-fail-jobs) |  |  |
| [usegalaxy-eu.fix-galaxy-server-dir](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/usegalaxy-eu.fix-galaxy-server-dir) |  |  |
| [usegalaxy-eu.fix-missing-api-keys](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/usegalaxy-eu.fix-missing-api-keys) |  |  |
| [usegalaxy-eu.fix-oidc](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/usegalaxy-eu.fix-oidc) |  |  |
| [usegalaxy-eu.fix-stop-ITs](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/usegalaxy-eu.fix-stop-ITs) |  |  |
| [usegalaxy-eu.fix-stuck-handlers](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/usegalaxy-eu.fix-stuck-handlers) |  |  |
| [usegalaxy-eu.fix-unscheduled-jobs](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/usegalaxy-eu.fix-unscheduled-jobs) |  |  |
| [usegalaxy-eu.fix-unscheduled-workflows](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/usegalaxy-eu.fix-unscheduled-workflows) |  |  |
| [usegalaxy-eu.fix-user-quotas](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/usegalaxy-eu.fix-user-quotas) |  |  |
| [usegalaxy-eu.galactic-radio-telescope](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/usegalaxy-eu.galactic-radio-telescope) |  |  |
| [usegalaxy-eu.galaxy-cleanup](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/usegalaxy-eu.galaxy-cleanup) |  |  |
| [usegalaxy-eu.galaxy-procstat](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/usegalaxy-eu.galaxy-procstat) |  |  |
| [usegalaxy-eu.galaxy-slurp](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/usegalaxy-eu.galaxy-slurp) |  |  |
| [usegalaxy-eu.gapars-galaxy](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/usegalaxy-eu.gapars-galaxy) |  |  |
| [usegalaxy-eu.gie-deployer](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/usegalaxy-eu.gie-deployer) |  |  |
| [usegalaxy-eu.gie-node-proxy](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/usegalaxy-eu.gie-node-proxy) |  |  |
| [usegalaxy-eu.google-verification](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/usegalaxy-eu.google-verification) |  |  |
| [usegalaxy-eu.grt-client](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/usegalaxy-eu.grt-client) |  |  |
| [usegalaxy-eu.grt-export](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/usegalaxy-eu.grt-export) |  |  |
| [usegalaxy-eu.htcondor_release](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/usegalaxy-eu.htcondor_release) |  |  |
| [usegalaxy-eu.jenkins-ssh-key](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/usegalaxy-eu.jenkins-ssh-key) |  |  |
| [usegalaxy-eu.log-cleaner](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/usegalaxy-eu.log-cleaner) |  |  |
| [usegalaxy-eu.logrotate](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/usegalaxy-eu.logrotate) |  |  |
| [usegalaxy-eu.monitoring](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/usegalaxy-eu.monitoring) |  |  |
| [usegalaxy-eu.plausible](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/usegalaxy-eu.plausible) |  |  |
| [usegalaxy-eu.remap-user](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/usegalaxy-eu.remap-user) |  |  |
| [usegalaxy-eu.rsync-to-nfs](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/usegalaxy-eu.rsync-to-nfs) |  |  |
| [usegalaxy-eu.subdomain-themes](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/usegalaxy-eu.subdomain-themes) |  |  |
| [usegalaxy-eu.tours](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/usegalaxy-eu.tours) |  |  |
| [usegalaxy-eu.webhooks](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/usegalaxy-eu.webhooks) |  |  |