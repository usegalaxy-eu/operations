## Ansible roles in the [infrastructure-playbook](https://github.com/usegalaxy-eu/infrastructure-playbook) repository

* The following are the roles that are currently being installed on the head and maintenance nodes via the [sn06 playbook](https://github.com/usegalaxy-eu/infrastructure-playbook/blob/master/sn06.yml), [sn07 playbook](https://github.com/usegalaxy-eu/infrastructure-playbook/blob/master/sn07.yml), and [maintenance node playbook](https://github.com/usegalaxy-eu/infrastructure-playbook/blob/master/maintenance.yml)
* The roles are classified as either head node only, maintenance node only, or both
* Head nodes: are the nodes that are running the Galaxy web server, the Galaxy job handlers, and the Galaxy workflow schedulers. As of 15/02/2023 `sn06.galaxyproject.eu`, and `sn07.galaxyproject.eu` are the two head nodes. Only `sn06` is in production.
* Maintenance node: runs cron jobs, contains Galaxy codebase, config, etc, pushes data to influxdb, performs cleanup tasks, syncs Galaxy codebase to NFS, etc.


| Roles  | Head node(s) only | Maintenance node only | Both | Adds cronjob? | Comments | Separate repo |
| :------------- | :-------------: | :-------------: | :-------------: | :-------------: | :-------------: | :-------------: |
| [usegalaxy_eu.htcondor](https://galaxy.ansible.com/usegalaxy_eu/htcondor) |   |   | :heavy_check_mark: |   |   | :heavy_check_mark: |
| [ssh_hardening](https://galaxy.ansible.com/devsec/hardening) |   |   | :heavy_check_mark: |   |   | :heavy_check_mark: |
| [galaxyproject.gxadmin](https://galaxy.ansible.com/galaxyproject/gxadmin) |   |   | :heavy_check_mark: |   |   | :heavy_check_mark: |
| [ssh-host-sign](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/ssh-host-sign) |   |   | :heavy_check_mark: |   |   |   |
| [usegalaxy-eu.dynmotd](https://github.com/usegalaxy-eu/ansible-dynmotd) |   |   | :heavy_check_mark: |   |   |  |
| [usegalaxy-eu.autofs](https://github.com/usegalaxy-eu/ansible-autofs) |   |   | :heavy_check_mark: |   |   | :heavy_check_mark: |
| [influxdata.chrony](https://github.com/usegalaxy-eu/ansible-chrony) |   |   | :heavy_check_mark: |   |   | :heavy_check_mark: |
| [usegalaxy-eu.autoupdates](https://github.com/usegalaxy-eu/ansible-autoupdates) |   |   | :heavy_check_mark: |   |   | :heavy_check_mark: |
| [galaxyproject.miniconda](https://galaxy.ansible.com/galaxyproject/miniconda) |   |   | :heavy_check_mark: |   |   | :heavy_check_mark: |
| [geerlingguy.repo-epel](https://galaxy.ansible.com/geerlingguy/repo-epel) |   |   | :heavy_check_mark: |   |   | :heavy_check_mark: |
| [usegalaxy_eu.handy.os_setup](https://galaxy.ansible.com/usegalaxy_eu/handy) |   |   | :heavy_check_mark: |   |   | :heavy_check_mark: |
| [usegalaxy-eu.logrotate](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/usegalaxy-eu.logrotate) |   |   | :heavy_check_mark: |   |   |  |
| [dj-wasabi.telegraf](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/dj-wasabi.telegraf) |   |   | :heavy_check_mark: |   | `listen_galaxy_routes` (statsd), and `galaxy_active_users` (uses `/var/log/nginx/`) should be enabled only on the head nodes via the variable `telegraf_plugins_extra` |  |
| [usegalaxy_eu.fs_maintenance](https://galaxy.ansible.com/usegalaxy_eu/fs_maintenance) |   |   | :heavy_check_mark: | :heavy_check_mark:  | All tasks (htcondor cron tasks, adding htcondor scripts, etc) except the `fsm_cron_tasks` can run on the maintenance node because the `gxadmin` tasks in `fsm_cron_tasks` uses the galaxy's log directory `/var/log/galaxy` for cleanup  | :heavy_check_mark: |
| [usegalaxy-eu.fix-stuck-handlers](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/usegalaxy-eu.fix-stuck-handlers) |  |  | :heavy_check_mark: |  :heavy_check_mark:  | Cron jobs for handlers, schedulers, and gunicorn. Also, sync to nfs (this should be removed and added to maintenance only node and the rest of them can run on both the head nodes)  |  |
| [galaxyproject.cvmfs](https://galaxy.ansible.com/galaxyproject/cvmfs) | :heavy_check_mark:  |   |  |   |   | :heavy_check_mark: |
| [hxr.monitor-galaxy-journalctl](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/hxr.monitor-galaxy-journalctl/) | :heavy_check_mark:  |   |  |   |   |  |
| [geerlingguy.docker](https://galaxy.ansible.com/geerlingguy/docker) | :heavy_check_mark:  |   |  |   |   | :heavy_check_mark: |
| [hxr.aws-cli](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/hxr.aws-cli) | :heavy_check_mark:  |   |  |   |   |  |
| [galaxyproject.tiaas2](https://galaxy.ansible.com/galaxyproject/tiaas2) | :heavy_check_mark:  |   |  |   |   | :heavy_check_mark: |
| [usegalaxy-eu.nginx](https://github.com/usegalaxy-eu/ansible-nginx) | :heavy_check_mark:  |   |  |   |   | :heavy_check_mark: |
| [usegalaxy_eu.ansible_nginx_upload_module](https://galaxy.ansible.com/usegalaxy_eu/ansible_nginx_upload_module) | :heavy_check_mark:  |   |  |   |   | :heavy_check_mark: |
| [usegalaxy-eu.gapars-galaxy](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/usegalaxy-eu.gapars-galaxy) | :heavy_check_mark:  |   |  |   |   |  |
| [usegalaxy_eu.galaxy_systemd](https://galaxy.ansible.com/usegalaxy_eu/galaxy_systemd) | :heavy_check_mark:  |   |  |   |   | :heavy_check_mark: |
| [usegalaxy-eu.subdomain-themes](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/usegalaxy-eu.subdomain-themes) | :heavy_check_mark:  |   |  |   |   |  |
| [usegalaxy-eu.log-cleaner](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/usegalaxy-eu.log-cleaner) | :heavy_check_mark:  |   |  |   |   |  |
| [usegalaxy-eu.error-pages](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/usegalaxy-eu.error-pages) | :heavy_check_mark:  |   |  |   |   |  |
| [usegalaxy-eu.fix-unscheduled-jobs](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/usegalaxy-eu.fix-unscheduled-jobs) | :heavy_check_mark:  |   |  | :heavy_check_mark:  | runs journalctl on galaxy-handler and then runs gxadmin mutate and creates a cron job |  |
| [usegalaxy-eu.galaxy-procstat](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/usegalaxy-eu.galaxy-procstat) | :heavy_check_mark:  |   |  |   |   |  |
| [usegalaxy-eu.update-hosts](https://github.com/usegalaxy-eu/ansible-update-hosts) | :heavy_check_mark:  |   |  | :heavy_check_mark:  | 1. Uses condor, 2. Updates the computing nodes list on the head nodes to a file /etc/genders, so this needs to be run only on the head nodes  | :heavy_check_mark: |
| [galaxyproject.galaxy](https://galaxy.ansible.com/galaxyproject/galaxy) |  | :heavy_check_mark: |  |   |   | :heavy_check_mark: |
| [usegalaxy-eu.fix-galaxy-server-dir](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/usegalaxy-eu.fix-galaxy-server-dir) |  | :heavy_check_mark: |  |   |   |  |
| [hxr.install-to-venv](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/hxr.install-to-venv) |  | :heavy_check_mark: |  |   |   |  |
| [usegalaxy_eu.gie_proxy](https://galaxy.ansible.com/usegalaxy_eu/gie_proxy) |  | :heavy_check_mark: |  |   |   | :heavy_check_mark: |
| [usegalaxy-eu.fix-ancient-ftp-data](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/usegalaxy-eu.fix-ancient-ftp-data) |  | :heavy_check_mark: |  | :heavy_check_mark:  |   |  |
| [usegalaxy-eu.fix-missing-api-keys](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/usegalaxy-eu.fix-missing-api-keys) |  | :heavy_check_mark: |  | :heavy_check_mark:  |   |  |
| [usegalaxy-eu.fix-user-quotas](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/usegalaxy-eu.fix-user-quotas) |  | :heavy_check_mark: |  |:heavy_check_mark:  |   |  |
| [usegalaxy_eu.tpv_auto_lint](https://galaxy.ansible.com/usegalaxy_eu/tpv_auto_lint) |  | :heavy_check_mark: |  |   |   | :heavy_check_mark: |
| [usegalaxy-eu.galaxy-slurp](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/usegalaxy-eu.galaxy-slurp) |  | :heavy_check_mark: |  | :heavy_check_mark:  |   |  |
| [hxr.postgres-connection](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/hxr.postgres-connection) |  | :heavy_check_mark: |  |   |   |  |
| [usegalaxy-eu.tours](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/usegalaxy-eu.tours) |  | :heavy_check_mark: |  |   |   |  |
| [usegalaxy-eu.webhooks](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/usegalaxy-eu.webhooks) |  | :heavy_check_mark: |  |   |   |  |
| [usegalaxy-eu.rsync-to-nfs](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/usegalaxy-eu.rsync-to-nfs) |  | :heavy_check_mark: |  |   |   |  |
| [hxr.galaxy-nonreproducible-tools](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/hxr.galaxy-nonreproducible-tools) |  | :heavy_check_mark: |  |   |   |  |
| [usegalaxy-eu.bashrc](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/usegalaxy-eu.bashrc) |  | :heavy_check_mark: |  |   |   |  |
| [usegalaxy-eu.monitoring](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/usegalaxy-eu.monitoring) |  | :heavy_check_mark: |  |   |   |  |
| [hxr.monitor-email](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/hxr.monitor-email) |  | :heavy_check_mark: |  |   |   |  |
| [hxr.monitor-cluster](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/hxr.monitor-cluster) |  | :heavy_check_mark: |  |   |   |  |
| [usegalaxy-eu.htcondor_release](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/usegalaxy-eu.htcondor_release) |  | :heavy_check_mark: |  | :heavy_check_mark:  | condor release held jobs as cron task |  |
| [usegalaxy-eu.fix-unscheduled-workflows](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/usegalaxy-eu.fix-unscheduled-workflows/tasks) |  | :heavy_check_mark: |  | :heavy_check_mark:  |   |  |
| [usegalaxy-eu.fix-stop-ITs](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/usegalaxy-eu.fix-stop-ITs) |  | :heavy_check_mark: |  | :heavy_check_mark:  |   |  |
| [usegalaxy-eu.vgcn-monitoring](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles/usegalaxy-eu.vgcn-monitoring) |  | :heavy_check_mark: |  |  |  |  |

_Separate repo: Whether the role has its own repo or is it a local role located and available only in the [infrastructure_playbook](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/roles) repo_
