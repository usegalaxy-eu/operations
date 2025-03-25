# KVM Server for Critical Infrastructure

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
prefixed by "vm", in order to clarify their purpose.


### 2.2 Networking Setup

For each network used by guest VMs, a dedicated bridge has been
created on `ens802f1`, `build`'s second 10 GbE interface (the host's
primary net IF being `ens802f0`). Because all networks used are
VLAN-tagged, this requires creating a tagged virtual IF for each
bridge. With this setup, guests don't have to worry about VLAN
tagging, the respective bridge only needs to be specified in the VMs
`<interface>` definition tag. Multihomed guests are also possible, by
giving a guest VM more than one virtual interface.

As of this writing, the following bridges are defined for KVM use:

- `virbr1.223`: VLAN=223, CIDR=132.230.223.0/24

- `virbr1.2367`: VLAN=2367, CIDR=10.5.67.0/24

- `virbr1.2368`: VLAN=2368, CIDR=10.5.68.0/24

- `virbr1.68`: VLAN=68, CIDR=132.230.68.0/24`


These bridges have been created with `nmtui(8)` using default values
*execpt* as follows:

- "Aging time" set to 0 (infinity)

- "IP CONFIGURATION" set to `<Disabled>` for both IPv4 and IPv6

A virtual IF with the right VLAN tag needs to be added to the bridge
as a slave as well.


## 3 Guest Setup

### 3.1 General

Our VM images built for (or extracted from) OpenStack in "raw" format
can in principle be booted on KVM "as is". Since these images are
currently set up to be runtime-configured via the cloud-config
service, which our "vanilla" KVM server does not provide, there are some
issues to be dealt with in order to make the guests useful, on which
see sec. 3.3 "Tweaking VM Images" below.


### 3.2 Guest VM Creation

The actual creation of a guest VM from a cloud image is in three easy
steps:

1. It is recommended to create an LV for each disk image that the VM
uses and copy the image file to that VM with `dd(1)`

2. Copy the template file `kvm-guest-template.xml` found in the same
directory as this Markdown file to a file _guest-name_`.xml` (the XML
files are best kept in `/root/kvm`) and make the required changes as
noted in the header comment.

3. Run the command `virsh define` _guest-name_`.xml`


If all went well, the freshly created guest will show up in the output
of `virsh list --all` and can be started with `virsh start` _guest_


### 3.3 Tweaking VM Images

Images built for OpenStack are lacking two critical features when
started unmodified on a "vanilla" KVM server:

- Account setup

- Console access

These are set up by cloud-config (and in the case of console access,
provided by the "Dashboard"), a service we don't provide. A quick
workaround is to mount the image on the KVM server host and tweak the
image in a chroot shell. (See sec. 4.3 below for instructions to mount
the image.)

#### 3.3.1 Account Setup

Passwords and/or `authorized_keys` files must be set up for the users
`root` and `centos` (or whatever account is being used for SSH access
in OpenStack instances). The users' home directories can be accessed
after mounting the image in the host, for changing passwords a
chroot-shell is the easiest option.

Setting up sudo-rights for the login user is best accomplished by
creating a file with permissions "440 root:root" in `/etc/sudoers.d`,
the follwing example assumes the user name `centos`:

```
centos  ALL=(ALL)       NOPASSWD: ALL
```

#### 3.3.2 Providing Console Access

If `systemd-getty-generator(8)` is enabled it should start an
appropriate `agetty(8)` process on the virtual serial console
"automagically". If this fails for any reason a symlink

```
serial-getty@ttyS0.service -> /lib/systemd/system/serial-getty@.service
```

can be created in `/etc/systemd/system/getty.target.wants` using a
chroot shell.

NOTE that this setup alone will *not* allow for controlling GRUB or
seeing boot messages on the serial console. Accomplishing this by
re-configuring GRUB, if desired, is left as an excercise to the
reader...

#### 3.3.3 Setting up a Static IP Address

Some of our networks don't have a public DHCP service; also, even if
DHCP is available it is often desireable to have a stable IP address
on VMs hosting services. Once console access has been established
(see. sec. 3.3.2 above) a static IP address can be set while logged
into the running VM using `nmcli(1)`. Here's an example:

```
nmcli con modify eth0 connection.interface-name eth0 ipv4.method manual ipv4.addresses 10.5.68.237/24 ipv4.gateway 10.5.68.254 ipv4.dns 132.230.200.200 ipv4.may-fail no
```

(The default router is *always* on `.254` in UFR networks.)

NOTE: When assigning a static IP to a VM running in a network that
*does* have an active DHCP service, don't forget to add an IP
reservation to the relevant DHCP table, to avoid possible IP address
conflicts!


## 4 Managing Guest VMs

Management tasks broadly fall in one of the following categories:

- Starting/stopping/modifying VM guests with `virsh(1)`

- Managing VM disk images with LVM tools

- Mounting and manipulating VM disk images in the shell

The most common tasks will be covered in the following subchapters.


### 4.1 Basic virsh usage

**NOTE**: When using `virsh(1)` as user `root`, the tool will
currently spit out the following error message every time it is
invoked from the shell:

```
Error registering authentication agent: GDBus.Error:org.freedesktop.PolicyKit1.Error.Failed: Cannot determine user of subject (polkit-error-quark, 0)
```

This message, while annoying, is harmless and can safely be ignored.


The most pertinent virsh commands are

```
virsh list
```

Lists the names and IDs of running VM guests; use `--all` for also
listing currently inactive guests.


```
virsh start --console GUEST_NAME_OR_ID
```

(Omit the `--console` option if console access is not immediately
required. Once the console is launched, `CTRL-]` will close the
console and return to the shell.)


```
virsh autostart GUEST_NAME_OR_ID
```

Marks the guest VM for autostarting; this command will **not** start
the guest immediately. Use `--disable` to disable autostarting
instead.q


```
virsh console GUEST_NAME_OR_ID
```

Access the virtual serial console of an already running
guest. `CTRL-]` will close the console and return to the shell.


```
virsh shutdown GUEST_NAME_OR_ID
```

Gracefully shutdown the guest


```
virsh destroy GUEST_NAME_OR_ID
```

Force termination of the guest process; this command will **not**
remove the guest or its associated disk images.


```
virsh guestinfo GUEST_NAME_OR_ID
```

Print some useful status info for the guest.


`virsh(1)` has many more commands and options, see the manpage for the
gory detail.


### 4.2 Managing Logical Volumes (LVs)

As of this writing, the KVM server does **not** define any libvirt
storage pools; consequently, the storage pool commands listed in
section `STORAGE POOL COMMANDS` of the manual page do not work and
should **not** be used.

Instead, the standard LVM tools are used to manipulate VM disk
images. The most pertinent commands are `lvs(8)`, `lvcreate(8)`,
`lvrename(8)`, `lvresize(8)`, `lvremove(8)` and `lvconvert(8)`.

Examples of the most common tasks follow.

### 4.2.1 Listing LVs

```
lvs
```

List the logical volumes currently defined on the system. The output
is **not** limited to VM disk images only but also lists LVs used by
the host OS such as `root`, `home` or `opt`. It is recommended to
prefix names of LVs created specifically as VM disk images with the
literal string "vm" in order to clarify their purpose, e.g.
`vminfluxdb`. The name(s) must of course match whatever is specified
in the VM guest definition.


### 4.2.2 Creating LVs

```
lvcreate --name LV_NAME --size LV_SIZE rl_build
```

This creates a (linear) logical volume of size LV_SIZE with the name
LV_NAME in the volume group `rl_build` (the only VG currently
defined). The size parameter can be suffixed with the usual unit
specifiers `b`, `s`, `k`, `m`, `g` which are *always* base-2,
regardless of capitalization. E.g. for creating a 10 GiB LV to hold
the virtual system disk for a VM named `test1` one would use:

```
lvcreate --name vmtest1 --size 10g rl_build
```


### 4.2.3 Removing LVs

```
lvremove rl_build/LV_NAME
```

Removes the LV named LV_NAME in VG `rl_build`, asking for confirmation first.

**CAVEAT EMPTOR**: omitting the name of the LV will cause
`lvremove(8)` to **attempt to delete ALL LVs in the VG
specified(!)**. Fortunately, by default LVs that are mounted or
otherwise in use will be skipped and confirmation will be required for
deleting the others. **ALWAYS THINK TWICE BEFORE HITTING [RETURN] ON ANY**
`lvremove` **COMMAND AND *NEVER*, *EVER* USE ANY OF THE OPTIONS** `-y`,
`--yes`, `-f`, `--force` **!!!**

(Yes, the syntax and semantics of LV management commands *are* obscure
and an excellent example of how *not* to design a command line
interface...)


### 4.2.4 Renaming and resizing LVs

```
lvrename rl_build LV_NAME_BEFORE LV_NAME_AFTER
```

Rename the LV named LV_NAME_BEFORE in VG `rl_build` to LV_NAME_AFTER.


```
lvresize --size NEW_LV_SIZE rl_build/LV_NAME
```

Resize the the LV named LV_NAME in VG `rl_build` to NEW_LV_SIZE; this
can also be used on snapshot LVs (see below) that are smaller than
their parent and in danger of running out of blocks as more and more
of the parent's blocks get modified.


### 4.2.5 Managing LV snapshots

**NOTE** While the LV snapshot commands themselves are atomic, they
only manipulate the on-disk state of the associated VM and should thus
**not** be used on *running* VMs' LVs.


```
lvcreate --snapshot --name LV_SNAPSHOT_NAME --size SNAPSHOT_SIZE rl_build/LV_NAME
```

Creates a snapshot named LV_SNAPSHOT_NAME of size SNAPSHOT_SIZE on the
LV named LV_NAME in VG `rl_build`. It is recommended to embed the date
and time of snapshot creation in the name; it is also probably best to
use UTC rather than local time and suffix the time value with the
literal string "Z". E.g. to create a snapshot of the LV `vmtest1` with
size 5 GiB capturing the state of, say, Nov 6th 2024 at 16:18 CET one
could use the command

```
lvcreate --snapshot --name vmtest1-20241006T1518Z --size 5g rl_build/vmtest1
```


In order to restore an LV to the state captured in a snapshot, the
snapshot has to be *merged* into its parent with `lvconvert(8)`.
E.g. to restore the snapshot created in the example immediately above
one would use

```
lvconvert --mergesnapshot rl_build/vmtest1-20241006T1518Z --interval 10
```

(The `--interval` option is purely optional, but as `lvconvert` may
take its sweet time on larger LVs it is good to have a progress report
in 10 seconds intervals (or longer, as desired). Note that `lvconvert`
will usually run for some time even after it has reported "Merged:
100.00%".)

**NOTE** that `lvconvert --mergesnapshot` will **remove** the snapshot
LV, so if that state is to be retained for possible future use again,
a new snapshot will have to be created. Have I already mentioned that
the syntax and semantics of the Linux LV management tools are
completely obscure and a prime example of poor design...?


## 4.3 Mounting VM images

The LVs are block devices with device files named `/dev/dm-[0-9]+`
which in turn have symlinks pointing to them in both
`/dev/`*VG_NAME*`/` and `/dev/mapper/` the names of which make clear
to which LV the device file belongs; only these symlinks are normally
used to refer to LVs' device files.

Since, however, the virtual disk images are normally partinioned, the
file system(s) contained therein cannot be mounted using the LVs block
device. A tool named `kpartx(8)` is used to create/remove dedicated
block devices for the partitions of an LV containing a disk image.

```
kpartx -l /dev/mapper/LV_DEVICE_SPECIFIER
```

Print the names of the devices that *would be* created for the LV
pointed to by LV_DEVICE_SPECIFIER. No device files are created.


```
kpartx -a /dev/mapper/LV_DEVICE_SPECIFIER
```

Actually create the partition devices for the LV pointed to by
LV_DEVICE_SPECIFIER. Add `-v` to see the names of the devices
(actually: device symlinks) created.


```
kpartx -d /dev/mapper/LV_DEVICE_SPECIFIER
```

Remove the device symplinks that were previously created by `kpartx
-a`; add `-v` to see what's being done.


**NOTE** that while it is often more convenient (and perfectly
possible) to use the links under `/dev/`*VG_NAME*`/` rather than those
under `/dev/mapper` as arguments to `kpartx`, *the new partition
device links will ONLY ever be created in `/dev/mapper`*!

Here's a sample transcript that illustrates the process:

```
# lvs
  LV                          VG       Attr       LSize    Pool Origin     Data%  Meta%  Move Log Cpy%Sync Convert
  home                        rl_build -wi-ao----   50.00g
  opt                         rl_build -wi-ao----  100.00g
  root                        rl_build -wi-ao---- <100.00g
  vmvgcn-test2                rl_build owi-aos---   10.00g
  vmvgcn-test2-20241017T1033Z rl_build swi-a-s---   10.00g      vmvgcn-test2 6.11
# kpartx -av /dev/mapper/rl_build-vmvgcn--test2
add map rl_build-vmvgcn--test2p1 (253:7): 0 20969472 linear 253:3 2048
# mount -oro /dev/mapper/rl_build-vmvgcn--test2p1 /mnt
# ls /mnt
afs/  boot/   data/  etc/   lib@    media/  mnt/  opt/   root/  sbin@     srv/  tmp/  var/
bin@  cvmfs/  dev/   home/  lib64@  misc/   net/  proc/  run/   scratch/  sys/  usr/
# umount /mnt
# kpartx -dv /dev/rl_build/vmvgcn-test2
del devmap : rl_build-vmvgcn--test2p1
#
```

### Increase root partition
Make sure you find the right partition (`/dev/mapper/rl_build-yourVM`) or inside the VM `/dev/vda`
~~~
GROWPARTITION=<your partition>
growpart $GROWPARTITION 1
xfs_growfs "$GROWPARTITION"1
partprobe $GROWPARTITION # if size is not updated
~~~
