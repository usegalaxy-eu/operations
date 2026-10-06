---
title: UseGalaxy.EU storage
---
Operational procedures: [Add a new data share](../runbooks/storage-add-data-share.md) · [Migrate storage](../runbooks/storage-migration.md) · [Recover data](../troubleshooting/storage-data-recovery.md)

# AutoFS

Our storage mounts are controlled everywhere with autofs.

The single source of truth for all mount points is the [mounts repository](https://github.com/usegalaxy-eu/mounts).
Mount points are defined in [mountpoints.yml](https://github.com/usegalaxy-eu/mounts/blob/master/mountpoints.yml) and
templated into `autofs_conf_files` ([templates/group-vars-all.yml.j2](https://github.com/usegalaxy-eu/mounts/blob/master/templates/group-vars-all.yml.j2),
rendered to [dest/all.yml](https://github.com/usegalaxy-eu/mounts/blob/master/dest/all.yml)), which is included by the
[infrastructure-playbook](https://github.com/usegalaxy-eu/infrastructure-playbook) as `mounts/dest/all.yml`.
Each host selects the sections it needs via the `autofs_mount_points` variable in its group_vars,
e.g. [group_vars/sn09/sn09.yml](https://github.com/usegalaxy-eu/infrastructure-playbook/blob/master/group_vars/sn09/sn09.yml).

In VGCN machines the autofs configuration is templated directly from the mounts repository, which is included as a
git submodule in [vgcn-infrastructure](https://github.com/usegalaxy-eu/vgcn-infrastructure) (see
[userdata.yaml.j2](https://github.com/usegalaxy-eu/vgcn-infrastructure/blob/main/userdata.yaml.j2)).

## How it works

`/etc/auto.master.d/data.autofs` has a line like:

```
/data           /etc/auto.data          nfsvers=3
```

Note that the above autofs conf is VERY sensitive to spaces. Do not retab unless you need to. `/etc/auto.data` looks like
(the sections rendered from the mounts repository, `data` and `jwd` shown here):

```
#name   options                         source
#
db      -rw,hard,nosuid,nconnect=2,vers=3       ufr-dyn.isi1.public.ads.uni-freiburg.de:/ifs/isi1/ufr/bronze/nfs/denbi/&
dp01    -rw,hard,nosuid,nconnect=2,vers=3       denbi.svm.bwsfs.uni-freiburg.de:/dataplant01
1       -rw,hard,nosuid,nconnect=2,vers=3       denbi.svm.bwsfs.uni-freiburg.de:/dnb01/depot/&
3       -rw,hard,nosuid,nconnect=2,vers=3       denbi.svm.bwsfs.uni-freiburg.de:/dnb01/depot/&
4       -rw,hard,nosuid,nconnect=2,vers=3       denbi.svm.bwsfs.uni-freiburg.de:/dnb01/depot/&
5       -rw,hard,nosuid,nconnect=2,vers=3       denbi.svm.bwsfs.uni-freiburg.de:/dnb01/depot/&
6       -rw,hard,nosuid,nconnect=2,vers=3       denbi.svm.bwsfs.uni-freiburg.de:/dnb01/depot/&
7       -rw,hard,nosuid,nconnect=2,vers=3       denbi.svm.bwsfs.uni-freiburg.de:/dnb01/depot/&
dnb-ds01 -rw,hard,nosuid,nconnect=2,nodev,vers=3 denbi.svm.bwsfs.uni-freiburg.de:/dnb01-legacy
dnb-ds02 -rw,hard,nosuid,nconnect=2,nodev,vers=3 denbi.svm.bwsfs.uni-freiburg.de:/dnb02-legacy
dnb-ds03 -rw,hard,nosuid,nconnect=2,nodev,vers=3 denbi.svm.bwsfs.uni-freiburg.de:/dnb03-legacy
dnb01   -rw,hard,nosuid,nconnect=2,nodev,vers=3 ufr-dyn.isi1.public.ads.uni-freiburg.de:/ifs/isi1/ufr/bronze/nfs/denbi/&
dnb02   -rw,hard,nosuid,nconnect=2,nodev,vers=3 ufr-dyn.isi1.public.ads.uni-freiburg.de:/ifs/isi1/ufr/bronze/nfs/denbi/&
dnb04   -rw,hard,nosuid,nconnect=2,nodev,vers=3 ufr-dyn.isi1.public.ads.uni-freiburg.de:/ifs/isi1/ufr/bronze/nfs/denbi/&
dnb05   -rw,hard,nosuid,nconnect=2,nodev,vers=3 denbi.svm.bwsfs.uni-freiburg.de:/dnb01/&
dnb06   -rw,hard,nosuid,nconnect=2,nodev,vers=3 denbi.svm.bwsfs.uni-freiburg.de:/dnb06
dnb07   -rw,hard,nosuid,nconnect=2,nodev,vers=3 denbi.svm.bwsfs.uni-freiburg.de:/dnb07
dnb08   -rw,hard,nosuid,nconnect=2,nodev,vers=3 denbi.svm.bwsfs.uni-freiburg.de:/dnb08
dnb09   -rw,hard,nosuid,nconnect=2,nodev,vers=3 denbi.svm.bwsfs.uni-freiburg.de:/dnb09
dnb10   -rw,hard,nosuid,nconnect=2,nodev,vers=3 denbi.svm.bwsfs.uni-freiburg.de:/dnb10
dnb11   -rw,hard,nosuid,nconnect=2,nodev,vers=3 denbi.svm.bwsfs.uni-freiburg.de:/dnb11
dnb12   -rw,hard,nosuid,nconnect=2,nodev,vers=3 denbi.svm.bwsfs.uni-freiburg.de:/dnb12
dnb13   -rw,hard,nosuid,nconnect=2,nodev,vers=3 denbi.svm.bwsfs.uni-freiburg.de:/dnb13
jwd     -rw,hard,nosuid,nconnect=2,vers=3       denbi.svm.bwsfs.uni-freiburg.de:/ws01/&
jwd01   -rw,hard,nosuid,vers=3                  noads1.svm.bwsfs.uni-freiburg.de:/galaxy-mwd01/
jwd03f  -rw,hard,nosuid,nconnect=2,vers=3       denbi.svm.bwsfs.uni-freiburg.de:/ws02/&
jwd06   -rw,hard,nosuid                         zfs06.bi.privat:/export/&
jwd07   -rw,hard,nosuid                         zfs07.bi.privat:/export/&
jwd08   -rw,hard,nosuid                         zfs08.bi.privat:/export/&
birna01 -rw,hard,nosuid,nodev,nconnect=2,vers=3 denbi.svm.bwsfs.uni-freiburg.de:/&
```

So dnb01 will be available under /data/dnb01

Additional sections (`gxtest`, `gxkey`, `usrlocal`, `cache`, `cvac`, `misc`) are templated similarly into
`/etc/auto.usrlocal`, etc. See [templates/group-vars-all.yml.j2](https://github.com/usegalaxy-eu/mounts/blob/master/templates/group-vars-all.yml.j2)
for the exact mapping.

# Different kinds of storage

* managed iSilon storage (NFS)
* managed NetApp storage (NFS, S3 possible)
* zfs1: Big machine (>200TB) with spinning disks and SSD cache frontend (self-build)
* zfs0f (formerly ssds1): SSD-only machine (24x1.8TB) (self-build)
* zfs2f, zfs3f: additional all-flash ZFS servers (self-build)
* zfs06, zfs07, zfs08: ZFS servers exported via NFSv4 (`zfs0X.bi.privat`), used for the `jwd06`-`jwd08`, `cache06`-`cache08`, `misc06`-`misc08` and `cvac08` mounts

# Group-based storage

It is possible to assign storage to dedicated Galaxy user groups. For example, the above storage `dp01` is dedicated to the DataPLANT project
and can be only used by researchers associated with the `dataplant` Galaxy group.
This works via our dynamic job submission system ([total-perspective-vortex](https://github.com/galaxyproject/total-perspective-vortex/)).
All jobs are going through these rules and we added a special one for the `dataplant`
group. The drawback is that you cannot easily assign multiple storage backends
to one group or different weights at the moment.

# Sync

We have `/usr/bin/galaxy-sync-to-nfs`, created by this [Ansible role](https://github.com/usegalaxy-eu/infrastructure-playbook/blob/master/roles/usegalaxy-eu.rsync-to-nfs/tasks/main.yml), on sn09 that takes care of synchronizing Galaxy data from the head node to the storage into the computational cluster.

Currently, the script is invoked:

* by the [handler](https://github.com/usegalaxy-eu/infrastructure-playbook/blob/master/sn09.yml) in the Galaxy playbook.
* by Jenkins, as a downstream project at the end of tools installation. See [install_tools](https://build.galaxyproject.eu/job/usegalaxy-eu/job/install-tools/)

# Cluster and Mounts

Adding new storage/mount points to galaxy is not trivial, since there are many machines involved.

Mount points are centrally maintained in the [mounts repository](https://github.com/usegalaxy-eu/mounts). After adding a DNS-A-Record to the [infrastructure/dns.tf](https://github.com/usegalaxy-eu/infrastructure/blob/master/dns.tf):

1. Add the new mount point to [mountpoints.yml](https://github.com/usegalaxy-eu/mounts/blob/master/mountpoints.yml) in the appropriate section
2. The `all.yml` playbook in the mounts repository templates it into `dest/all.yml` (the `autofs_conf_files` variable), which is consumed by the infrastructure-playbook as `mounts/dest/all.yml`
3. If it is a new section, add that section to the `autofs_mount_points` variable of the hosts that should mount it (in their group_vars)

**HOWEVER** for

* **VGCN**, the mounts repository is included as a git [submodule](https://github.com/usegalaxy-eu/vgcn-infrastructure) and the mount points are templated directly into `/etc/auto.data` via [userdata.yaml.j2](https://github.com/usegalaxy-eu/vgcn-infrastructure/blob/main/userdata.yaml.j2)
* **incoming (FTP)**, add the section to its `autofs_mount_points` in [group_vars/incoming.yml](https://github.com/usegalaxy-eu/infrastructure-playbook/blob/master/group_vars/incoming.yml)

# Which host mounts what

The `autofs_mount_points` selection per host group (from the infrastructure-playbook group_vars):

| Host group    | Sections mounted                                                              |
| :------------ | :---------------------------------------------------------------------------- |
| sn09          | `data`, `gxtest`, `gxkey`, `jwd`, `usrlocal`, `cache`, `misc`                  |
| sn11          | `data`, `gxtest`, `gxkey`, `jwd`                                               |
| maintenance   | `data`, `gxtest`, `gxkey`, `jwd`, `usrlocal`, `cache`, `misc` (+ `gxkey` at `/opt/galaxy`) |
| incoming (FTP)| `data`, `jwd`, `misc`                                                          |
| celery cluster| `gxkey` at `/opt/galaxy` (`usrlocal_celerycluster`)                            |
| VGCN          | `dnb`, `jwd`, `cache`, `misc` (`/etc/auto.data`) and `tools` + `gxkey` (`/etc/auto.usrlocal`), templated from the mounts submodule |


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

The following table is synced with the [mounts repository](https://github.com/usegalaxy-eu/mounts) ([mountpoints.yml](https://github.com/usegalaxy-eu/mounts/blob/master/mountpoints.yml)) and gives an overview of the different mount points:

| Mountpoint        | Section | Backend                                                      | Export                                                                   | NFS options                          | Purpose                             |
| :---------------- | :------ | :----------------------------------------------------------- | :----------------------------------------------------------------------- | :----------------------------------- | :---------------------------------- |
| /data/db          | dnb     | iSilon                                                       | ufr-dyn.isi1.public.ads.uni-freiburg.de:/ifs/isi1/ufr/bronze/nfs/denbi/& | hard,rw,nosuid,nconnect=2,vers=3     |                                     |
| /data/dp01        | dnb     | NetApp A400                                                  | denbi.svm.bwsfs.uni-freiburg.de:/dataplant01                             | hard,rw,nosuid,nconnect=2,vers=3     | special storage for DataPLANT group |
| /data/1           | dnb     | NetApp A400                                                  | denbi.svm.bwsfs.uni-freiburg.de:/dnb01/depot/&                           | hard,rw,nosuid,nconnect=2,vers=3     | storage (old)                       |
| /data/3           | dnb     | NetApp A400                                                  | denbi.svm.bwsfs.uni-freiburg.de:/dnb01/depot/&                           | hard,rw,nosuid,nconnect=2,vers=3     | storage (old)                       |
| /data/4           | dnb     | NetApp A400                                                  | denbi.svm.bwsfs.uni-freiburg.de:/dnb01/depot/&                           | hard,rw,nosuid,nconnect=2,vers=3     | storage (old)                       |
| /data/5           | dnb     | NetApp A400                                                  | denbi.svm.bwsfs.uni-freiburg.de:/dnb01/depot/&                           | hard,rw,nosuid,nconnect=2,vers=3     | storage (old)                       |
| /data/6           | dnb     | NetApp A400                                                  | denbi.svm.bwsfs.uni-freiburg.de:/dnb01/depot/&                           | hard,rw,nosuid,nconnect=2,vers=3     | storage (old)                       |
| /data/7           | dnb     | NetApp A400                                                  | denbi.svm.bwsfs.uni-freiburg.de:/dnb01/depot/&                           | hard,rw,nosuid,nconnect=2,vers=3     | storage (old)                       |
| /data/dnb-ds01    | dnb     | NetApp A400                                                  | denbi.svm.bwsfs.uni-freiburg.de:/dnb01-legacy                            | hard,rw,nosuid,nconnect=2,nodev,vers=3 | legacy                             |
| /data/dnb-ds02    | dnb     | NetApp A400                                                  | denbi.svm.bwsfs.uni-freiburg.de:/dnb02-legacy                            | hard,rw,nosuid,nconnect=2,nodev,vers=3 | legacy                             |
| /data/dnb-ds03    | dnb     | NetApp A400                                                  | denbi.svm.bwsfs.uni-freiburg.de:/dnb03-legacy                            | hard,rw,nosuid,nconnect=2,nodev,vers=3 | legacy                             |
| /data/dnb01       | dnb     | NetApp A400 /future iSilon                                   | ufr-dyn.isi1.public.ads.uni-freiburg.de:/ifs/isi1/ufr/bronze/nfs/denbi/& | hard,rw,nosuid,nconnect=2,nodev,vers=3 | storage (old)                      |
| /data/dnb02       | dnb     | NetApp A400 /future iSilon                                   | ufr-dyn.isi1.public.ads.uni-freiburg.de:/ifs/isi1/ufr/bronze/nfs/denbi/& | hard,rw,nosuid,nconnect=2,nodev,vers=3 | storage (old)                      |
| /data/dnb04       | dnb     | iSilon                                                       | ufr-dyn.isi1.public.ads.uni-freiburg.de:/ifs/isi1/ufr/bronze/nfs/denbi/& | hard,rw,nosuid,nconnect=2,nodev,vers=3 | storage (old)                      |
| /data/dnb05       | dnb     | NetApp A400                                                  | denbi.svm.bwsfs.uni-freiburg.de:/dnb01/&                                 | hard,rw,nosuid,nconnect=2,nodev,vers=3 | storage (old)                      |
| /data/dnb06       | dnb     | NetApp A400                                                  | denbi.svm.bwsfs.uni-freiburg.de:/dnb06                                   | hard,rw,nosuid,nconnect=2,nodev,vers=3 | storage (old)                      |
| /data/dnb07       | dnb     | NetApp A400                                                  | denbi.svm.bwsfs.uni-freiburg.de:/dnb07                                   | hard,rw,nosuid,nconnect=2,nodev,vers=3 | currently used                     |
| /data/dnb08       | dnb     | NetApp A400                                                  | denbi.svm.bwsfs.uni-freiburg.de:/dnb08                                   | hard,rw,nosuid,nconnect=2,nodev,vers=3 | currently used                     |
| /data/dnb09       | dnb     | NetApp A400                                                  | denbi.svm.bwsfs.uni-freiburg.de:/dnb09                                   | hard,rw,nosuid,nconnect=2,nodev,vers=3 | unused                             |
| /data/dnb10       | dnb     | NetApp A400                                                  | denbi.svm.bwsfs.uni-freiburg.de:/dnb10                                   | hard,rw,nosuid,nconnect=2,nodev,vers=3 |                                     |
| /data/dnb11       | dnb     | NetApp A400                                                  | denbi.svm.bwsfs.uni-freiburg.de:/dnb11                                   | hard,rw,nosuid,nconnect=2,nodev,vers=3 |                                     |
| /data/dnb12       | dnb     | NetApp A400                                                  | denbi.svm.bwsfs.uni-freiburg.de:/dnb12                                   | hard,rw,nosuid,nconnect=2,nodev,vers=3 |                                     |
| /data/dnb13       | dnb     | NetApp A400                                                  | denbi.svm.bwsfs.uni-freiburg.de:/dnb13                                   | hard,rw,nosuid,nconnect=2,nodev,vers=3 |                                     |
| /data/jwd         | jwd     | NetApp A400                                                  | denbi.svm.bwsfs.uni-freiburg.de:/ws01/&                                  | hard,rw,nosuid,nconnect=2,vers=3     | job working dir                     |
| /data/jwd01       | jwd     | NetApp (noads1)                                              | noads1.svm.bwsfs.uni-freiburg.de:/galaxy-mwd01/                          | hard,rw,nosuid,vers=3                | job working dir                     |
| /data/jwd03f      | jwd     | NetApp A400 flash                                            | denbi.svm.bwsfs.uni-freiburg.de:/ws02/&                                  | hard,rw,nosuid,nconnect=2,vers=3     | job working dir (full-flash)        |
| /data/jwd06       | jwd     | ZFS server (self-build)                                      | zfs06.bi.privat:/export/&                                                | hard,rw,nosuid (NFSv4)               | job working dir                     |
| /data/jwd07       | jwd     | ZFS server (self-build)                                      | zfs07.bi.privat:/export/&                                                | hard,rw,nosuid (NFSv4)               | job working dir                     |
| /data/jwd08       | jwd     | ZFS server (self-build)                                      | zfs08.bi.privat:/export/&                                                | hard,rw,nosuid (NFSv4)               | job working dir                     |
| /data/birna01     | jwd     | NetApp A400                                                  | denbi.svm.bwsfs.uni-freiburg.de:/&                                       | hard,rw,nosuid,nodev,nconnect=2,vers=3 | birna01 volume (read-only)         |
| /opt/galaxy (test)| sync    | NetApp A400                                                  | denbi.svm.bwsfs.uni-freiburg.de:/ws01/galaxy-sync/test                   | hard,rw,nosuid,nconnect=2,vers=3     | galaxy root (test)                  |
| /opt/galaxy       | sync    | NetApp A400                                                  | denbi.svm.bwsfs.uni-freiburg.de:/ws01/galaxy-sync/main                   | hard,rw,nosuid,nconnect=2,vers=3     | galaxy root                         |
| /opt/galaxy       | sync    | NetApp A400                                                  | denbi.svm.bwsfs.uni-freiburg.de:/galaxy-sync                             | hard,rw,nosuid,nconnect=2,vers=3     | galaxy root (galaxy's codebase)     |
| /tmp              | tmp     | NetApp A400                                                  | denbi.svm.bwsfs.uni-freiburg.de:/ws01/jwd/tmp                            | hard,rw,nosuid,nconnect=2,vers=3     | tmp                                 |
| /usr/local/tools  | tools   | NetApp A400                                                  | denbi.svm.bwsfs.uni-freiburg.de:/dnb01/tools                             | hard,rw,nosuid,nconnect=2,vers=3     | tool dir                            |
| /data/cache06     | cache   | ZFS server (self-build)                                      | zfs06.bi.privat:/export/&                                                | hard,rw,nosuid (NFSv4)               | cache                               |
| /data/cache07     | cache   | ZFS server (self-build)                                      | zfs07.bi.privat:/export/&                                                | hard,rw,nosuid (NFSv4)               | cache                               |
| /data/cache08     | cache   | ZFS server (self-build)                                      | zfs08.bi.privat:/export/&                                                | hard,rw,nosuid (NFSv4)               | cache                               |
| /data/misc06      | misc    | ZFS server (self-build)                                      | zfs06.bi.privat:/export/&                                                | hard,rw,nosuid (NFSv4)               | misc                                |
| /data/misc07      | misc    | ZFS server (self-build)                                      | zfs07.bi.privat:/export/&                                                | hard,rw,nosuid (NFSv4)               | misc                                |
| /data/misc08      | misc    | ZFS server (self-build)                                      | zfs08.bi.privat:/export/&                                                | hard,rw,nosuid (NFSv4)               | misc                                |
| /data/cvac08      | cvac    | ZFS server (self-build)                                      | zfs08.bi.privat:/export/cvac08                                           | hard,rw,nosuid (NFSv4)               | CVMFS alien cache (read-only)       |

"old" means in this case, the storage is still used to read old datasets, but not to write new ones.

The previously used `jwd02f`, `jwd04` and `jwd05e` mount points are no longer defined in `mountpoints.yml` (they are still listed in the `nfs_check_excluded_mounts` of [vars.yml](https://github.com/usegalaxy-eu/mounts/blob/master/vars.yml)). The `/data/0`, `/data/2`, `/data/dnb03`, `/data/gxtst`, `/data/gxkey` and `/data/galaxy-sync` mount points have been removed as well (`dnb03` was replaced by the `dnb-ds03` legacy mount, and the galaxy-sync shares now mount at `/opt/galaxy`).

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


