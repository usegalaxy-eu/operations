---
title: KVM Infrastructure (Terraform + libvirt)
---

# KVM Infrastructure

We no longer run a cloud (bwCloud/OpenStack). All service VMs are now KVM guests on bare metal,
provisioned with [Terraform](https://www.terraform.io/) using the
[dmacvicar/libvirt](https://github.com/dmacvicar/libvirt) provider.

- Repository: [usegalaxy-eu/kvm-infrastructure](https://github.com/usegalaxy-eu/kvm-infrastructure)
- Hypervisor: `sn12.galaxyproject.eu` (`qemu+sshcmd://root@sn12.galaxyproject.eu/system`)
- Documentation of the former cloud setup: [archived/cloud/](../archived/cloud/)

# Overview

* All VMs are defined in a single map (`locals.vms`) in [vms.tf](https://github.com/usegalaxy-eu/kvm-infrastructure/blob/master/vms.tf)
* Every VM gets:
    * a static IPv4 address in the `10.4.68.0/24` network (default gateway `10.4.68.254`, DNS `132.230.200.200`). We need to manually add this  IPs in the [infoblox](https://ipam.noc.uni-freiburg.de/ui/).
    * the hostname `<name>.bi.privat`
    * a root disk (qcow2, backed by a base image) in the `images` pool
    * a data disk (qcow2) in the `nfs-pool`, formatted `ext4` and mounted by cloud-init ( `/data`)
    * a cloud-init ISO with static network configuration and the `cloud@vgcn` SSH keyss
* Guests are attached to the host bridge `virbr1.2068` (VLAN 2068) with virtio NICs
* The guest OS is q35/KVM with `host-passthrough` CPU mode for  the jenkins  worker.

# Repository layout

| File | Purpose |
| :--- | :------ |
| [main.tf](https://github.com/usegalaxy-eu/kvm-infrastructure/blob/master/main.tf) | Terraform + libvirt provider configuration (hypervisor URI) |
| [vars.tf](https://github.com/usegalaxy-eu/kvm-infrastructure/blob/master/vars.tf) | Variables: domain (`.bi.privat`), bridge interface, gateway, DNS servers, SSH authorized key, `mb`/`gb` helpers |
| [images.tf](https://github.com/usegalaxy-eu/kvm-infrastructure/blob/master/images.tf) | `images` storage pool and base image volumes |
| [data_pool.tf](https://github.com/usegalaxy-eu/kvm-infrastructure/blob/master/data_pool.tf) | `vg_data` LVM pool (`/dev/vg_data`) — defined but currently not used by `vms.tf` |
| [data_pool_nfs.tf](https://github.com/usegalaxy-eu/kvm-infrastructure/blob/master/data_pool_nfs.tf) | `nfs-pool` directory pool on `/data` (holds the VM data disks) |
| [vms.tf](https://github.com/usegalaxy-eu/kvm-infrastructure/blob/master/vms.tf) | VM definitions (`locals.vms`) and the resources built from them (root disks, data disks, cloud-init, domains) |
| [user-data.tpl](https://github.com/usegalaxy-eu/kvm-infrastructure/blob/master/user-data.tpl) | cloud-init (cloud-config) template |
| [sum_resources.py](https://github.com/usegalaxy-eu/kvm-infrastructure/blob/master/sum_resources.py) | Resource accounting: sums assigned vCPU/memory/disk and compares against the host capacity |
| [.github/workflows/validate.yml](https://github.com/usegalaxy-eu/kvm-infrastructure/blob/master/.github/workflows/validate.yml) | GitHub Actions workflow running `terraform validate` on every push/PR |

# Storage pools

| Pool    | Type | Source / target                | Used for                                        |
| :------ | :--- | :----------------------------- | :---------------------------------------------- |
| images  | fs   | `/dev/vg_images/images` → `/images` | Base images, per-VM root disks, cloud-init volumes |
| nfs-pool| dir  | `/data` (on sn12)              | Per-VM data disks (`data_disk_<name>.qcow2`)     |
| vg_data | logical (LVM) | `/dev/vg_data`        | defined, currently unused by `vms.tf`            |

# Base images

Base images are qcow2 files built by the VGCN image build pipeline (Packer, see the
[vgcn](https://github.com/usegalaxy-eu/vgcn) repository) and added as `libvirt_volume` resources in
[images.tf](https://github.com/usegalaxy-eu/kvm-infrastructure/blob/master/images.tf). Their names follow the pattern:

```
vgcn~<distro>~+generic+internal+kvm~<date>~<build-number>~<branch>~<commit>.qcow2
```

e.g. `vgcn~rockylinux-10-latest-x86_64~+generic+internal+kvm~20260423~56178~fix-kvm-build~f18dff3.qcow2`.

Each VM's root disk (`root_disk_<name>.qcow2`) is a qcow2 overlay backed by one of these base images.

# Current VMs

Defined in `locals.vms` in [vms.tf](https://github.com/usegalaxy-eu/kvm-infrastructure/blob/master/vms.tf).
Per VM: `ip_address` (CIDR), `memory` (GiB), `vcpu`, `root_disk_size`, `data_disk_size`, `image` (base image),
`data_disk_mount` (where `/dev/vdb` is mounted in the guest) and `data_device`.

| VM                 | IP (10.4.68.x) | vCPU | Mem (GiB) | Root | Data | Data mount | Base image   |
| :----------------- | :------------- | ---: | --------: | :--- | :--- | :--------- | :----------- |
| test-01            | .192           | 2    | 2         | 20G  | 50G  | /data      | rockylinux-10 |
| celery-1           | .193           | 16   | 16        | 32G  | 10G  | /data      | rockylinux-10 |
| celery-2           | .183           | 16   | 16        | 32G  | 10G  | /data      | rockylinux-10 |
| celery-3           | .182           | 16   | 16        | 32G  | 10G  | /data      | rockylinux-10 |
| upload             | .191           | 2    | 2         | 20G  | 10G  | /data      | rockylinux-10 |
| beacon             | .190           | 2    | 2         | 20G  | 50G  | /data      | rockylinux-10 |
| influxdb           | .189           | 6    | 32        | 20G  | 300G | /data      | rockylinux-10 |
| rabbitmq           | .188           | 4    | 16        | 20G  | 12G  | /opt       | rockylinux-10 |
| maintenance        | .187           | 12   | 32        | 50G  | 200G | /data      | rockylinux-10 |
| tpv-broker         | .186           | 2    | 2         | 20G  | 10G  | /data      | rockylinux-10 |
| apollo             | .180           | 8    | 16        | 20G  | 10G  | /data      | rockylinux-9  |
| ticketsystem       | .185           | 6    | 8         | 20G  | 10G  | /data      | rockylinux-10 |
| plausible          | .184           | 2    | 4         | 20G  | 100G | /data      | rockylinux-10 |
| cvmfs-stratum0     | .179           | 2    | 4         | 25G  | 250G | /data      | rockylinux-10 |
| cvmfs1-ufr0        | .173           | 2    | 4         | 65G  | ~0   | /storage   | rockylinux-10 |
| worker-0-kvm-build | .178           | 8    | 16        | 50G  | 10G  | /data      | rockylinux-10 |
| apps               | .177           | 4    | 8         | 16G  | 50G  | /data      | rockylinux-10 |
| grafana            | .176           | 4    | 4         | 20G  | 10G  | /data      | rockylinux-10 |
| ftp                | .175           | 1    | 2         | 20G  | 10G  | /data2     | rockylinux-10 |
| osiris             | .174           | 4    | 8         | 20G  | 10G  | /data      | rockylinux-9  |

# Cloud-init

[user-data.tpl](https://github.com/usegalaxy-eu/kvm-infrastructure/blob/master/user-data.tpl) is a cloud-config template rendered per VM. It:

* creates the `centos` user with passwordless sudo and the `cloud@vgcn` SSH authorized key (`ssh_deletekeys: false`, no new keys generated)
* writes a NetworkManager connection file (`enp1s0`) with the static IP address, gateway and DNS servers
* waits for `/dev/vdb`, formats it as `ext4` (label `data`) if needed, and mounts it at the VM's `data_disk_mount` via `/etc/fstab` (`nofail`)

The `meta-data` sets the instance id and `local-hostname` (`<name>.bi.privat`).
The ISO is generated with `libvirt_cloudinit_disk`, copied into the `images` pool, and is replaced whenever the
cloud-init configuration changes (`replace_triggered_by`).

# Resource accounting

[sum_resources.py](https://github.com/usegalaxy-eu/kvm-infrastructure/blob/master/sum_resources.py) parses `vms.tf`
and sums the assigned vCPU, memory and disk, comparing against the host capacity (`sn12`: 112 vCPU, 512 GiB memory):

```bash
python sum_resources.py --bar
```

# CI and deployment

* GitHub Actions runs `terraform validate` on every push and pull request (state files are removed before validation)
* The Terraform state is committed to the repository; every apply is recorded with a commit named `Terraform apply (N)`
* The `.vault_password` file is used locally and excluded via `.gitignore`

# Adding a new VM

1. If needed, build a new base image with the VGCN image build pipeline and add a `libvirt_volume` for it in [images.tf](https://github.com/usegalaxy-eu/kvm-infrastructure/blob/master/images.tf)
2. Add an entry to the `locals.vms` map in [vms.tf](https://github.com/usegalaxy-eu/kvm-infrastructure/blob/master/vms.tf) (pick a free IP in `10.4.68.0/24`, sizes, base image and data disk mount) and  make a pull  request against  the repository.
3. Review the terraform plan in jenkins [CI](https://build.galaxyproject.eu/job/usegalaxy-eu/job/kvm-infrastructure-pr/) 
4. Merge the PR.  This will trigger the  CI and  make  the terraform  apply.

# Relation to other repositories

* [infrastructure-playbook](https://github.com/usegalaxy-eu/infrastructure-playbook): configures the VMs with Ansible (inventory entries like `mq.bi.privat`, `ftp.bi.privat`, `maintenance.bi.privat`, ...); mounts come from the [mounts repository](https://github.com/usegalaxy-eu/mounts)
* [infrastructure](https://github.com/usegalaxy-eu/infrastructure): DNS records ([dns.tf](https://github.com/usegalaxy-eu/infrastructure/blob/master/dns.tf)); public service records point to the Traefik proxy, which forwards to these VMs
* [vgcn](https://github.com/usegalaxy-eu/vgcn) / [vgcn-infrastructure](https://github.com/usegalaxy-eu/vgcn-infrastructure): builds the base images used here
