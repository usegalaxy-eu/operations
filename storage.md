---
title: UseGalaxy.EU storage
---
# AutoFS

Our storage mounts are controlled everywhere with autofs.

In VGCN machines it's defined in the [userdata.yml](https://github.com/usegalaxy-eu/vgcn-infrastructure/blob/master/userdata.yaml)
file while in other machines it is controlled by [usegalaxy-eu.autofs](https://github.com/usegalaxy-eu/ansible-autofs) ansible role and
some variables like in [group_vars/sn09.yml](https://github.com/usegalaxy-eu/infrastructure-playbook/blob/be8d196b26f46852bc593a0d8a64e66dedde69c5/group_vars/sn09/sn09.yml#L16)

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

# Different kinds of storage

* managed iSilon storage (NFS)
* managed NetApp storage (NFS, S3 possible)
* zfs1: Big machine (>200TB) with spinning disks and SSD cache frontend (self-build)
* ssds1: SSD-only machine (24x1.8TB) (self-build)

# Group-based storage

It is possible to assign storage to dedicated Galaxy user groups. For example, the above storage `dp01` is dedicated to the DataPLANT project
and can be only used by researchers associated with the `dataplant` Galaxy group.
This works via our dynamic job submission system ([total-perspective-vortex](https://github.com/galaxyproject/total-perspective-vortex/)).
All jobs are going through these rules and we added a special one for the `dataplant`
group. The drawback is that you cannot easily assign multiple storage backends
to one group or different weights at the moment.

# Sync

We have `/usr/bin/galaxy-sync-to-nfs`, created by this [Ansible role](https://github.com/usegalaxy-eu/infrastructure-playbook/blob/master/roles/usegalaxy-eu.rsync-to-nfs/tasks/main.yml), on sn04 that takes care of synchronizing Galaxy data from sn04 to the storage into the computational cluster.

Currently, the script is invoked:

* by the [handler](https://github.com/usegalaxy-eu/infrastructure-playbook/blob/be8d196b26f46852bc593a0d8a64e66dedde69c5/sn09.yml#L75) in the Galaxy playbook.
* by Jenkins, as a downstream project at the end of tools installation. See [install_tools](https://build.galaxyproject.eu/job/usegalaxy-eu/job/install-tools/)

# Cluster and Mounts (WIP)

Adding new storage/mount points to galaxy is not trivial, since there are many machines involved.

After adding a DNS-A-Record to the [infrastructure/dns.tf](https://github.com/mira-miracoli/infrastructure/blob/main/dns.tf),

it is sufficient for most machines to add the mount point to [infrastucture-playbook/group_vats/all.yml](https://github.com/usegalaxy-eu/infrastructure-playbook/blob/master/group_vars/all.yml) in the `autofs_conf_files` section.

**HOWEVER** for

* **VGCN**, you have to add the mountpoint to [vgcn-infrastructure/userdata.yaml](https://github.com/usegalaxy-eu/vgcn-infrastructure/blob/main/userdata.yaml)
* **incoming (FTP)**, add it to its own [group_vars/incoming.yml](https://github.com/usegalaxy-eu/infrastructure-playbook/blob/master/group_vars/incoming.yml)

# Steps to add a new data (_dnbXX_) share
1. Request the storage team (RZ) for a new data share (_dnbXX_)
2. Once the new mount point is made available, mount it and test if the new mount point actually works and is reachable (pick a worker node and try it).
3. The following places must be updated to roll out the new data share and to migrate from the previous share
   1. Add the new mount point to the [mounts repository](https://github.com/usegalaxy-eu/mounts). An example PR can be found [here](https://github.com/usegalaxy-eu/mounts/pull/4)
   2. Update the currently running `vgcnbwc-worker-*` nodes with the new mount using `pssh`.
      ``` bash
      pssh -h /etc/pssh/cloud -l centos -i 'sudo su -c "echo \"dnb09    -rw,hard,nosuid,nconnect=2      denbi.svm.bwsfs.uni-freiburg.de:/dnb09\" >> /etc/auto.data"'
      ````
   3. Verify that the mount is successful
      ```bash
      pssh -h /etc/pssh/cloud -l centos -i 'ls -l /data/dnb09/'
      ```
   4. Then, update the `object_store_conf.xml`, for example like [see here](https://github.com/usegalaxy-eu/infrastructure-playbook/pull/800)
   5. Once everything is merged, run the Jenkins job (`sn09` playbook project) to deploy the new data share
   6. Monitor the changes and the handler logs to make sure that there are no errors.

# NFS export policies
* Export rules are

```bash
fr1-cl2::> export-policy rule show -vserver denbi -fields protocol,clientmatch,rorule,rwrule,superuser -policyname denbi
vserver policyname ruleindex protocol clientmatch     rorule rwrule superuser
------- ---------- --------- -------- --------------- ------ ------ ---------
denbi   denbi      1         nfs3     132.230.223.238 sys    sys    any
denbi   denbi      1         nfs3     132.230.223.239 sys    sys    any
denbi   denbi      3         nfs3     10.5.68.0/24    sys    sys    any
2 entries were displayed.

fr1-cl2::> export-policy rule show -vserver denbi -fields protocol,clientmatch,rorule,rwrule,superuser -policyname denbi-svc
vserver policyname ruleindex protocol clientmatch     rorule rwrule superuser
------- ---------- --------- -------- --------------- ------ ------ ---------
denbi   denbi-svc  1         nfs3     132.230.180.148 sys    sys    sys

fr1-cl2::> export-policy rule show -vserver denbi -fields protocol,clientmatch,rorule,rwrule,superuser -policyname denbi-ws
vserver policyname ruleindex protocol clientmatch     rorule rwrule superuser
------- ---------- --------- -------- --------------- ------ ------ ---------
denbi   denbi-ws   1         nfs3     132.230.223.238 sys    sys    any
denbi   denbi-ws   1         nfs3     132.230.223.239 sys    sys    any
denbi   denbi-ws   3         nfs3     10.5.68.0/24    sys    sys    any
denbi   denbi-ws   4         nfs3     132.230.223.213 sys    sys    none
3 entries were displayed.

fr1-cl2::> export-policy rule show -vserver denbi -fields protocol,clientmatch,rorule,rwrule,superuser -policyname birna
vserver policyname ruleindex protocol clientmatch      rorule rwrule superuser
------- ---------- --------- -------- ---------------- ------ ------ ---------
denbi   birna      1         nfs3     132.230.153.0/28 sys    sys    any
denbi   birna      2         nfs3     10.5.68.0/24     sys    sys    none
2 entries were displayed.
```

* INFO:
    * policyname _denbi_ is used for all `dnbXX` volumes, policyname _denbi-svc_ is used for the `svc01` volume, policyname _denbi-ws_ is used for the `galaxy_sync`, `ws01`, `ws02` volumes and policyname _birna_ is used for the `birna01` volume.
    * `superuser` means `no_root_squash` in this case. This means that the `root` account on the maschine with ip 132.230.223.239 and the machines within the subnet 10.5.68.0/24 can access (read and write) the volumes.
    * **Do not use shares (`jwd`, and `jwd03f`) exported via `ws01` and `ws02`. These shares will be removed soonish (as of: 14.06.2023)**

The following table shall give an overview of the different mount points and where they are used:


| Mountpoint       | Physicalmachine                                               | Export                                                                   | Purpose                             | sn05               | sn09               | sn07               | incoming           | celery             | VGCN               |
| :----------------- | --------------------------------------------------------------- | -------------------------------------------------------------------------- | ------------------------------------- | -------------------- | :------------------- | -------------------- | -------------------- | -------------------- | -------------------- |
| /data/jwd        | NetApp 400                                                    | denbi.svm.bwsfs.uni-freiburg.de:/ws01/&                                  | job working dir                     | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: |
| /data/jwd01      | Spinning Disks with SSD cache (self-build)                    | zfs1.galaxyproject.eu:/export/&                                          | job working dir                     | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: |
| /data/jwd02f     | Full SSD (self-build)                                         | zfs2f.galaxyproject.eu:/export/&                                         | job working dir (full-flash)        | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: |                    | :heavy_check_mark: | :heavy_check_mark: |
| /data/jwd03f     | NetApp A400 flash                                             | denbi.svm.bwsfs.uni-freiburg.de:/ws02/&                                  | job working dir (full-flash)        | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: |                    | :heavy_check_mark: | :heavy_check_mark: |
| /data/jwd04      | Full SSD (self-build)<br />(from here no f for flash in name) | zfs3f.galaxyproject.eu:/export/&                                         | job working dir (full-flash)        | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: |                    | :heavy_check_mark: | :heavy_check_mark: |
| /data/jwd05e      | Full SSD (self-build)<br />(from here no f for flash in name)<br />_**e**: encrypted_ | zfs3f.galaxyproject.eu:/export/&                                         | job working dir (full-flash)        | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: |                    |                    | :heavy_check_mark: |
| /opt/galaxy      | NetApp A400                                                   | denbi.svm.bwsfs.uni-freiburg.de:/ws01/galaxy-sync/main                   | galaxy root                         |                    |                    |                    |                    | :heavy_check_mark: | :heavy_check_mark: |
| /usr/local/tools | NetApp A400                                                   | denbi.svm.bwsfs.uni-freiburg.de:/dnb01/tools                             | tool dir                            |                    | :heavy_check_mark: | :heavy_check_mark: |                    |                    | :heavy_check_mark: |
| /data/gxtst      | NetApp A400                                                   | denbi.svm.bwsfs.uni-freiburg.de:/ws01/galaxy-sync/test                   |                                     | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: |                    | :heavy_check_mark: |                    |
| /data/gxkey      | NetApp A400                                                   | denbi.svm.bwsfs.uni-freiburg.de:/ws01/galaxy-sync/main                   |                                     | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: |                    | :heavy_check_mark: |                    |
| /data/galaxy-sync    | NetApp A400                                                   | denbi.svm.bwsfs.uni-freiburg.de:/galaxy-sync/main                   | Galaxy root (galaxy's codebase)      | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: |                    |                    |                    |
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
| /data/dnb08      | NetApp A400                                                   | denbi.svm.bwsfs.uni-freiburg.de:/dnb08                                   | currently used                      | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: |                    | :heavy_check_mark: | :heavy_check_mark: |
| /data/dnb09      | NetApp A400                                                   | denbi.svm.bwsfs.uni-freiburg.de:/dnb09                                   | unused                              | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: |                    | :heavy_check_mark: | :heavy_check_mark: |
| /data/dp01       | NetApp A400                                                   | denbi.svm.bwsfs.uni-freiburg.de:/dataplant01                             | special storage for DataPLANT group | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: |                    | :heavy_check_mark: | :heavy_check_mark: |

"old" means in this case, the storage is still used to read old datasets, but not to write new ones.

# S3 polices for our storage

K. will add more documentation.

```json
{
  "Statement": [
    {
      "Sid": "AllowObjectOperations",
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:GetObjectAcl",
        "s3:GetObjectVersion",
        "s3:DeleteObject",
        "s3:AbortMultipartUpload",
        "s3:ListMultipartUploadParts"
      ],
      "Resource": [
        "arn:aws:s3:::fr-galaxy-scratch-*/*"
      ]
    },
    {
      "Sid": "AllowBucketOperations",
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket",
        "s3:ListBucketVersions",
        "s3:GetBucketVersioning",
        "s3:GetLifecycleConfiguration",
        "s3:ListBucketMultipartUploads"
      ],
      "Resource": [
        "arn:aws:s3:::fr-galaxy-scratch-*"
      ]
    }
  ]
}
```


# Migrating storage

Galaxy has for every storage backend, defined in `config/object_store_conf.xml|yml, an ID specified. This ID ends up in the `datasets` table of Galaxy SQL database.

If we want to migrate old storages from `/data/0/galaxy_db/files/` to `/data/1/galaxy_db/files/` the following steps worked well:

```bash
rclone copy -v -P --transfers 8 /data/0/galaxy_db/files/ /data/1/galaxy_db/files/
rsync -auvi --stats --progress /data/0/galaxy_db/files/ /data/1/galaxy_db/files/
```

Using `rclone` before `rsync` can speed up the file-transfer. `Rclone` can copy data in parallel and `rsync` fixes up the permission or symlinks etc when needed.

When the data is copied, we need to update the `object_store_id` in the DB and then we can delete the data on the old storage.
```sql
UPDATE dataset SET object_store_id = 'files1' WHERE object_store_id = 'files0';
```


