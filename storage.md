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

* managed iSilon storage
* managed NetApp storage
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
