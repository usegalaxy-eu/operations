---
title: Bare metal nodes
---

# Bare metal nodes

We are using a few bare metal nodes for some critical services.

They have  f.q.d.n. assigned by us and are collected [here](https://github.com/usegalaxy-eu/infrastructure/blob/4e22b02395c1bb8872ebda711cc123968ae8589f/dns.tf#L102)

`sn06.galaxyproject.eu` is the Galaxy machine

`sn05.galaxyproject.eu` is the PostgreSQL and HTCcondor central manager machine

`build.galaxyproject.eu` is the Jenkins master machine

`zfs1.galaxyproject.eu` is a ZFS server

`ssds1.galaxyproject.eu` is  an all-flash ZFS server

`manager.vgcn.galaxyproject.eu` was the previous HTCondor central manager and is waiting to be reallocated
