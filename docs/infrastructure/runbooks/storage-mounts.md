# Cluster and Mounts

Adding new storage/mount points to galaxy is not trivial, since there are many machines involved.

Mount points are centrally maintained in the [mounts repository](https://github.com/usegalaxy-eu/mounts). After adding a DNS-A-Record to the [infrastructure/dns.tf](https://github.com/usegalaxy-eu/infrastructure/blob/master/dns.tf):

1. Add the new mount point to [mountpoints.yml](https://github.com/usegalaxy-eu/mounts/blob/master/mountpoints.yml) in the appropriate section
2. The `all.yml` playbook in the mounts repository templates it into `dest/all.yml` (the `autofs_conf_files` variable), which is consumed by the infrastructure-playbook as `mounts/dest/all.yml`
3. If it is a new section, add that section to the `autofs_mount_points` variable of the hosts that should mount it (in their group_vars)

**HOWEVER** for

* **VGCN**, the mounts repository is included as a git [submodule](https://github.com/usegalaxy-eu/vgcn-infrastructure) and the mount points are templated directly into `/etc/auto.data` via [userdata.yaml.j2](https://github.com/usegalaxy-eu/vgcn-infrastructure/blob/main/userdata.yaml.j2)
* **incoming (FTP)**, add the section to its `autofs_mount_points` in [group_vars/incoming.yml](https://github.com/usegalaxy-eu/infrastructure-playbook/blob/master/group_vars/incoming.yml)

See the [storage reference](../reference/storage.md) for the mount inventory and [Add a new data share](storage-add-data-share.md) for object-store rollout.
