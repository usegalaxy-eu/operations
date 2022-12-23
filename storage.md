---
title: UseGalaxy.EU storage
---
# AutoFS

Our storage mounts are controlled everywhere with autofs.

In VGCN machines it's defined in the [userdata.yml](https://github.com/usegalaxy-eu/vgcn-infrastructure/blob/master/userdata.yaml)
file while in other machines it is controlled by [usegalaxy-eu.autofs](https://github.com/usegalaxy-eu/ansible-autofs) ansible role and
some variables like in [group_vars/sno6.yml](https://github.com/usegalaxy-eu/infrastructure-playbook/blob/4e6121da8af500dfe878c312243be49807ac5f48/group_vars/sn06.yml#L18)

## How it works

`/etc/auto.master.d/data.autofs` has a line like:

```
/data           /etc/auto.data          nfsvers=3
```

Note that the above autofs conf is VERY sensitive to spaces. Do not retab unless you need to. `/etc/auto.data` looks like:

```
#name   options                         source
#
0       -rw,hard,nosuid      denbi.svm.bwsfs.uni-freiburg.de:/dnb01/depot/&
1       -rw,hard,nosuid      denbi.svm.bwsfs.uni-freiburg.de:/dnb01/depot/&
2       -rw,hard,nosuid      denbi.svm.bwsfs.uni-freiburg.de:/dnb01/depot/&
3       -rw,hard,nosuid      denbi.svm.bwsfs.uni-freiburg.de:/dnb01/depot/&
4       -rw,hard,nosuid      denbi.svm.bwsfs.uni-freiburg.de:/dnb01/depot/&
5       -rw,hard,nosuid      denbi.svm.bwsfs.uni-freiburg.de:/dnb01/depot/&
6       -rw,hard,nosuid      denbi.svm.bwsfs.uni-freiburg.de:/dnb01/depot/&
7       -rw,hard,nosuid      denbi.svm.bwsfs.uni-freiburg.de:/dnb01/depot/&
dp01    -rw,hard,nosuid      denbi.svm.bwsfs.uni-freiburg.de:/dataplant01
dnb01   -rw,hard,nosuid      ufr-dyn.isi1.public.ads.uni-freiburg.de:/ifs/isi1/ufr/bronze/nfs/denbi/&
dnb02   -rw,hard,nosuid      ufr-dyn.isi1.public.ads.uni-freiburg.de:/ifs/isi1/ufr/bronze/nfs/denbi/&
dnb03   -rw,hard,nosuid      ufr-dyn.isi1.public.ads.uni-freiburg.de:/ifs/isi1/ufr/bronze/nfs/denbi/&
dnb04   -rw,hard,nosuid      ufr-dyn.isi1.public.ads.uni-freiburg.de:/ifs/isi1/ufr/bronze/nfs/denbi/&
dnb05   -rw,hard,nosuid      denbi.svm.bwsfs.uni-freiburg.de:/dnb01/&
dnb06   -rw,hard,nosuid      denbi.svm.bwsfs.uni-freiburg.de:/dnb06
dnb07   -rw,hard,nosuid      denbi.svm.bwsfs.uni-freiburg.de:/dnb07
dnb08   -rw,hard,nosuid      denbi.svm.bwsfs.uni-freiburg.de:/dnb08
db      -rw,hard,nosuid      ufr-dyn.isi1.public.ads.uni-freiburg.de:/ifs/isi1/ufr/bronze/nfs/denbi/&
gxtst   -rw,hard,nosuid      denbi.svm.bwsfs.uni-freiburg.de:/ws01/galaxy-sync/test
gxkey   -rw,hard,nosuid      denbi.svm.bwsfs.uni-freiburg.de:/ws01/galaxy-sync/main
jwd     -rw,hard,nosuid      denbi.svm.bwsfs.uni-freiburg.de:/ws01/&
```

So dnb01 will be available under /data/dnb01

# Different kind of storages

* managed iSilon storage (NFS)
* managed NetApp storage (NFS, S3 possible)
* zfs1: Big machine (>200TB) with spinning disks and SSD cache frontend (self-build)
* ssds1: SSD-only machine (24x1.8TB) (self-build)

# Group based storage

It is possible to assign storage to dedicated Galaxy users groups. For example the above storage `dp01` is dedicated for the DataPLANT project
and can be only used by researchers associated with the `dataplant` Galaxy group.
This works via our dynamic job submission system (sorting-hat). All jobs are going through this rules and we added a special one for the `dataplant`
group. See the code [here](https://github.com/usegalaxy-eu/sorting-hat/pull/9/files#diff-383169e44c84e4fdd975aa09423aa5152bd87e5fc2fd7482acad1caa071d131aR149). The drawback is that you can not easily assign multiple storage backends
to one group or different weights at the moment.

# Sync

We have `/usr/bin/galaxy-sync-to-nfs`, created by this [Ansible role](https://github.com/usegalaxy-eu/infrastructure-playbook/blob/master/roles/usegalaxy-eu.rsync-to-nfs/tasks/main.yml), on sn04 that takes care of synchronizing Galaxy data from sn04 to the storage into the computational cluster.

Currently, the script is invoked:

* by the [handler](https://github.com/usegalaxy-eu/infrastructure-playbook/blob/4e6121da8af500dfe878c312243be49807ac5f48/sn06.yml#L57) in the Galaxy playbook.
* by Jenkins, as a downstream project at the end of tools installation. See [install_tools](https://build.galaxyproject.eu/job/usegalaxy-eu/job/install-tools/)

# Cluster and Mounts (WIP)

Adding new storage/mount points to galaxy is not trivial, since there are many machines involved.

After adding a DNS-A-Record to the [infrastructure/dns.tf](https://github.com/mira-miracoli/infrastructure/blob/main/dns.tf),

it issufficiant for most machines to add the mount point to [infrastucture-playbook/group_vats/all.yml](https://github.com/usegalaxy-eu/infrastructure-playbook/blob/master/group_vars/all.yml) in the `autofs_conf_files` section.

**HOWEVER** for

* **VGCN**, you have to add the mountpoint to [vgcn-infrastructure/userdata.yaml](https://github.com/usegalaxy-eu/vgcn-infrastructure/blob/main/userdata.yaml)
* **incoming (FTP)**, add it to its own [group_vars/incoming.yml](https://github.com/usegalaxy-eu/infrastructure-playbook/blob/master/group_vars/incoming.yml)

The following table shall give an overview of the different mount points and where they are used:


| Mountpoint       | Physicalmachine                                               | Export                                                                   | Purpose                             | sn05               | sn06               | sn07               | incoming           | celery             | VGCN               |
| :----------------- | --------------------------------------------------------------- | -------------------------------------------------------------------------- | ------------------------------------- | -------------------- | :------------------- | -------------------- | -------------------- | -------------------- | -------------------- |
| /data/jwd        | NetApp 400                                                    | denbi.svm.bwsfs.uni-freiburg.de:/ws01/&                                  | job working dir                     | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: |
| /data/jwd01      | Spinning Disks with SSD cache (self-build)                    | zfs1.galaxyproject.eu:/export/&                                          | job working dir                     | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: |
| /data/jwd02f     | Full SSD (self-build)                                         | zfs2f.galaxyproject.eu:/export/&                                         | job working dir (full-flash)        | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: |                    | :heavy_check_mark: | :heavy_check_mark: |
| /data/jwd03f     | NetApp A400 flash                                             | denbi.svm.bwsfs.uni-freiburg.de:/ws02/&                                  | job working dir (full-flash)        | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: |                    | :heavy_check_mark: | :heavy_check_mark: |
| /data/jwd04      | Full SSD (self-build)<br />(from here no f for flash in name) | zfs3f.galaxyproject.eu:/export/&                                         | job working dir (full-flash)        | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: |                    | :heavy_check_mark: | :heavy_check_mark: |
| /opt/galaxy      | NetApp A400                                                   | denbi.svm.bwsfs.uni-freiburg.de:/ws01/galaxy-sync/main                   | galaxy root                         |                    |                    |                    |                    | :heavy_check_mark: | :heavy_check_mark: |
| /usr/local/tools | NetApp A400                                                   | denbi.svm.bwsfs.uni-freiburg.de:/dnb01/tools                             | tool dir                            |                    | :heavy_check_mark: | :heavy_check_mark: |                    |                    | :heavy_check_mark: |
| /data/gxtst      | NetApp A400                                                   | denbi.svm.bwsfs.uni-freiburg.de:/ws01/galaxy-sync/test                   |                                     | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: |                    | :heavy_check_mark: |                    |
| /data/gxkey      | NetApp A400                                                   | denbi.svm.bwsfs.uni-freiburg.de:/ws01/galaxy-sync/main                   |                                     | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: |                    | :heavy_check_mark: |                    |
| /data/db         | iSilon                                                        | ufr-dyn.isi1.public.ads.uni-freiburg.de:/ifs/isi1/ufr/bronze/nfs/denbi/& |                                     | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: |                    | :heavy_check_mark: | :heavy_check_mark: |
| /data/0          | NetApp A400                                                   | denbi.svm.bwsfs.uni-freiburg.de:/dnb01/depot/&                           | storage (old)                       | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: |                    | :heavy_check_mark: | :heavy_check_mark: |
| /data/1          | NetApp A400                                                   | denbi.svm.bwsfs.uni-freiburg.de:/dnb01/depot/&                           | storage (old)                       | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: |                    | :heavy_check_mark: | :heavy_check_mark: |
| /data/2          | NetApp A400                                                   | denbi.svm.bwsfs.uni-freiburg.de:/dnb01/depot/&                           | storage (old)                       | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: |                    | :heavy_check_mark: | :heavy_check_mark: |
| /data/3          | NetApp A400                                                   | denbi.svm.bwsfs.uni-freiburg.de:/dnb01/depot/&                           | storage (old)                       | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: |                    | :heavy_check_mark: | :heavy_check_mark: |
| /data/4          | NetApp A400                                                   | denbi.svm.bwsfs.uni-freiburg.de:/dnb01/depot/&                           | storage (old)                       | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: |                    | :heavy_check_mark: | :heavy_check_mark: |
| /data/5          | NetApp A400                                                   | denbi.svm.bwsfs.uni-freiburg.de:/dnb01/depot/&                           | storage (old)                       | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: |                    | :heavy_check_mark: | :heavy_check_mark: |
| /data/6          | NetApp A400                                                   | denbi.svm.bwsfs.uni-freiburg.de:/dnb01/depot/&                           | storage (old)                       | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: |                    | :heavy_check_mark: | :heavy_check_mark: |
| /data/7          | NetApp A400                                                   | denbi.svm.bwsfs.uni-freiburg.de:/dnb01/depot/&                           | storage (old)                       | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: |                    | :heavy_check_mark: | :heavy_check_mark: |
| /data/dnb01      | NetApp A400 /future iSilon                                    | ufr-dyn.isi1.public.ads.uni-freiburg.de:/ifs/isi1/ufr/bronze/nfs/denbi/& | storage (old)                       | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: |                    | :heavy_check_mark: | :heavy_check_mark: |
| /data/dnb02      | NetApp A400 /future iSilon                                    | ufr-dyn.isi1.public.ads.uni-freiburg.de:/ifs/isi1/ufr/bronze/nfs/denbi/& | storage (old)                       | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: |                    | :heavy_check_mark: | :heavy_check_mark: |
| /data/dnb03      | iSilon                                                        | ufr-dyn.isi1.public.ads.uni-freiburg.de:/ifs/isi1/ufr/bronze/nfs/denbi/& | storage (old)                       | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: |                    | :heavy_check_mark: | :heavy_check_mark: |
| /data/dnb04      | iSilon                                                        | ufr-dyn.isi1.public.ads.uni-freiburg.de:/ifs/isi1/ufr/bronze/nfs/denbi/& | storage (old)                       | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: |                    | :heavy_check_mark: | :heavy_check_mark: |
| /data/dnb05      | NetApp A400                                                   | denbi.svm.bwsfs.uni-freiburg.de:/dnb01/&                                 | storage (old)                       | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: |                    | :heavy_check_mark: | :heavy_check_mark: |
| /data/dnb06      | NetApp A400                                                   | denbi.svm.bwsfs.uni-freiburg.de:/dnb06                                   | storage (old)                       | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: |                    | :heavy_check_mark: | :heavy_check_mark: |
| /data/dnb07      | NetApp A400                                                   | denbi.svm.bwsfs.uni-freiburg.de:/dnb07                                   | currently used                      | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: |                    | :heavy_check_mark: | :heavy_check_mark: |
| /data/dnb08      | NetApp A400                                                   | denbi.svm.bwsfs.uni-freiburg.de:/dnb08                                   | unused                              | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: |                    | :heavy_check_mark: | :heavy_check_mark: |
| /data/dp01       | NetApp A400                                                   | denbi.svm.bwsfs.uni-freiburg.de:/dataplant01                             | special storage for DataPLANT group | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: |                    | :heavy_check_mark: | :heavy_check_mark: |

"old" means in this case, the storage is still used to read old datasets, but not to write new ones.