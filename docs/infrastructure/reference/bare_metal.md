---
title: Bare metal nodes
---

# Bare metal nodes

We are using a few bare metal nodes for some critical services.

They have  f.q.d.n. assigned by us and are collected [here](https://github.com/usegalaxy-eu/infrastructure/blob/master/dns.tf)

`sn09.galaxyproject.eu` is the Galaxy machine (head node)

`sn10.galaxyproject.eu` hosts the UCSC Genome Browser VM (libvirt/Vagrant)

`sn11.galaxyproject.eu` is the Galaxy PostgreSQL database server

`sn12.galaxyproject.eu` is the Jenkins master machine and the HTCondor central manager. It is also a KVM/libvirt host and the DNBD3 proxy

`zfs0f.galaxyproject.eu` is an all-flash ZFS server (formerly `ssds1.galaxyproject.eu`)

`zfs1.galaxyproject.eu` is a ZFS server (spinning disks with flash cache)

`zfs2f.galaxyproject.eu` is an all-flash ZFS server

`zfs3f.galaxyproject.eu` is an all-flash ZFS server

`dnbd3-primary.galaxyproject.eu` is the primary server of the DNBD3 network boot infrastructure for the bare metal VGCN nodes

`manager.vgcn.galaxyproject.eu` was the previous HTCondor central manager; its DNS record has been removed
