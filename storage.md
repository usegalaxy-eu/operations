---
title: UseGalaxy.EU storage
---

# AutoFS

Our storage mounts are controlled everywhere with autofs.

In VGCN machines it's defined in the [userdata.yml](https://github.com/usegalaxy-eu/vgcn-infrastructure/blob/master/userdata.yaml) file while in other machines it is controlled by ansible in our [infra-playbook](https://github.com/usegalaxy-eu/infrastructure-playbook/blob/master/roles/hxr.autofs/templates/data.conf.j2)

## How it works

`/etc/data.autofs` has a line like:

```
/data           /etc/auto.data          nfsvers=3
```

Note that the above autofs conf is VERY sensitive to spaces. Do not retab unless you need to. `/etc/auto.data` looks like:

```
#name   options                         source
#
0       -rw,hard,intr,nosuid,quota      sn01.bi.uni-freiburg.de:/export/data3/galaxy/net/data/&
1       -rw,hard,intr,nosuid,quota      sn03.bi.uni-freiburg.de:/export/galaxy1/data/&
2       -rw,hard,intr,nosuid,quota      sn01.bi.uni-freiburg.de:/export/data4/galaxy/net/data/&
3       -rw,hard,intr,nosuid,quota      sn01.bi.uni-freiburg.de:/export/data5/galaxy/net/data/&
4       -rw,hard,intr,nosuid,quota      sn03.bi.uni-freiburg.de:/export/galaxy1/data/&
5       -rw,hard,intr,nosuid,quota      sn03.bi.uni-freiburg.de:/export/galaxy1/data/&
6       -rw,hard,intr,nosuid,quota      sn03.bi.uni-freiburg.de:/export/galaxy1/data/&
7       -rw,hard,intr,nosuid,quota      sn03.bi.uni-freiburg.de:/export/galaxy1/data/&
dnb01   -rw,hard,intr,nosuid,quota      ufr.isi1.public.ads.uni-freiburg.de:/ifs/isi1/ufr/bronze/nfs/denbi/&
dnb01   -rw,hard,intr,nosuid,quota      ufr.isi1.public.ads.uni-freiburg.de:/ifs/isi1/ufr/bronze/nfs/denbi/&
dnb02   -rw,hard,intr,nosuid,quota      ufr.isi1.public.ads.uni-freiburg.de:/ifs/isi1/ufr/bronze/nfs/denbi/&
dnb03   -rw,hard,intr,nosuid,quota      ufr.isi1.public.ads.uni-freiburg.de:/ifs/isi1/ufr/bronze/nfs/denbi/&
dnb04   -rw,hard,intr,nosuid,quota      ufr.isi1.public.ads.uni-freiburg.de:/ifs/isi1/ufr/bronze/nfs/denbi/&
db      -rw,hard,intr,nosuid,quota      sn02.bi.uni-freiburg.de:/export/fdata1/galaxy/net/data/&
gxmnt   -rw,hard,intr,nosuid,quota      sn03.bi.uni-freiburg.de:/export/galaxy1/system/galaxy
gxnew   -rw,hard,intr,nosuid,quota      sn03.bi.uni-freiburg.de:/export/galaxy1/system/galaxy-i1
gxtst   -rw,hard,intr,nosuid,quota      sn03.bi.uni-freiburg.de:/export/galaxy1/system/galaxy-i2
```



So dnb01 will be available under /data/dnb01
