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
dnb01   -rw,hard,nosuid      ufr-dyn.isi1.public.ads.uni-freiburg.de:/ifs/isi1/ufr/bronze/nfs/denbi/&
dnb02   -rw,hard,nosuid      ufr-dyn.isi1.public.ads.uni-freiburg.de:/ifs/isi1/ufr/bronze/nfs/denbi/&
dnb03   -rw,hard,nosuid      ufr-dyn.isi1.public.ads.uni-freiburg.de:/ifs/isi1/ufr/bronze/nfs/denbi/&
dnb04   -rw,hard,nosuid      ufr-dyn.isi1.public.ads.uni-freiburg.de:/ifs/isi1/ufr/bronze/nfs/denbi/&
dnb05   -rw,hard,nosuid      denbi.svm.bwsfs.uni-freiburg.de:/dnb01/&
dnb06   -rw,hard,nosuid      denbi.svm.bwsfs.uni-freiburg.de:/dnb01/&
db      -rw,hard,nosuid      ufr-dyn.isi1.public.ads.uni-freiburg.de:/ifs/isi1/ufr/bronze/nfs/denbi/&
gxtst   -rw,hard,nosuid      denbi.svm.bwsfs.uni-freiburg.de:/ws01/galaxy-sync/test
gxkey   -rw,hard,nosuid      denbi.svm.bwsfs.uni-freiburg.de:/ws01/galaxy-sync/main
jwd     -rw,hard,nosuid      denbi.svm.bwsfs.uni-freiburg.de:/ws01/&
```



So dnb01 will be available under /data/dnb01

# Sync
We have `/usr/bin/galaxy-sync-to-nfs`, created by this [Ansible role](https://github.com/usegalaxy-eu/infrastructure-playbook/blob/master/roles/usegalaxy-eu.rsync-to-nfs/tasks/main.yml), on sn04 that takes care of synchronizing Galaxy data from sn04 to the storage into the computational cluster.

Currently, the script is invoked:
* by the [handler](https://github.com/usegalaxy-eu/infrastructure-playbook/blob/4e6121da8af500dfe878c312243be49807ac5f48/sn06.yml#L57) in the Galaxy playbook.
* by Jenkins, as a downstream project at the end of tools installation. See [install_tools](https://build.galaxyproject.eu/job/usegalaxy-eu/job/install-tools/)
