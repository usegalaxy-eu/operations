# KVM Server for Critical Infrastructure

[Note: This document is currently work in progress]

## 1 Rationale

OpenStack has proven to be too unreliable to host non-redundant
mission-critical servers, of which we have a few and then some. A
no-frills, "vanilla" KVM-server is a cheap, simple alternative that
will do the job.

The physical server host `build.galaxyproject.eu`has been upgraded
with a pair of redundant (MD RAID-1) 900 GiB SSDs as well as a second
10 GbE interface so it can host KVM guests with bridged networking.

The KVM setup is intentionally kept as simple as possible: The guest
VMs are managed via libvirt, but the networking and storage management
is accomplished with the generic operating system tools such as
`nmcli(8)`, `nmtui(8)`, `bridge(8)` as well as the usual LVM shell
tools. In particular, the `net-*` and `pool-*` subcommands of
`virsh(8)` are **not** used, meaning in particular that the
`migrate-*` and `snapshot-*` commands of virsh will **not**
work. (Snapshotting of guests can be accomplished with `lvcreate(8)`
and `lvconvert(8)`.)


## 2 Server Setup

### 2.1 Storage Setup

For simplicity and flexibility, the KVM guests' image LVs are created
in the volume group that was created for the OS' file systems during
system install (`rl_build`). Creating a dedicated VG for KVM would
have looked somewhat tidier, but would have required a fixed,
pre-defined partitioning between OS and KVM storage spaces, rendering
the system inflexible in the face of possible future changes. (The
system is not fully dedicated to KVM, after all.) It is recommened to
name the guests' LVs after the respective guests' VMs, possibly
prefixed by "vm-", in order to clarify their purpose.


### 2.2 Networking Setup

For each network used by guest VMs, a dedicated bridge has been
created on `ens802f1`, `build`s second 10 GbE interface (the host's
primary net IF being `ens802f0`). Because all networks used are
VLAN-tagged, this requires creating a tagged virtual IF for each
bridge. With this setup, guests don't have to worry about VLAN
tagging, the respective bridge only needs to be specified in the VMs
`<interface>` definition tag. Multihomed guests are also possible, by
giving a guest VM more than one virtual interface.

As of this writing, the following bridges are defined for KVM use:

- `virbr1.223`: VLAN=223, CIDR=132.230.223.0/24

- `virbr1.2368`: VLAN=2368, CIDR=10.5.68.0/24


These bridges have been created with `nmtui(8)` using default values
*execpt* as follows:

- "Aging time" set to 0 (infinity)

- "IP CONFIGURATION" set to "<Disabled>" for both IPv4 and IPv6

A virtual IF with the right VLAN tag needs to be added to the bridge
as a slave as well.


## 3 Guest Setup

### 3.1 General

Our VM images built for (or extracted from) OpenStack in "raw" format
can in principle be booted on KVM "as is". Since these images are
currently set up to be runtime-configured via the cloud-config
service, which out vanilla KVM server does not provide, there are some
issued to be dealt with in order to make the guests useful, on which
see below.


### 3.2 Guest VM Creation

The actual creation of a guest VM from a could image is in three easy
steps:

1. It is recommended to create an LV for each disk image that the VM
uses and copy the image file to that VM with `dd(1)`

2. Copy the template file `kvm-guest-template.xml` found in the same
directory as this Markdown file to a file <guest-name>.xml (the XML
files are best kept in `/root/kvm`) and make the required changes as
noted in the header comment.

3. Run the command `virsh define `_description-file_


If all went well, the freshly created guest will show up in the output
of `virsh list --all` and can be started with `virsh start `_guest_


### 3.3 Tweaking VM Images

!FIXME TBD!


## 4 Managing Guest VMs

!FIXME TBD!
