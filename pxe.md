# Bare Metal VGCN with Network Boot

In contrast to the industry trend, using compute nodes without virtualization can have several benefits, such as
- less overhead for hypervisors
- reduced system complexity
- more direct control
- almost no overhead for adding or removing servers

While installing and maintaining tens to hundreds of disk installations on these servers is a tedious task and economically unviable,
running the servers in a network boot setup keeps a whole cluster maintainable with relatively few resources.

## Basic concepts – From Power to SSH

Pre-boot execution environment (PXE Boot) is software that runs directly on the network interface card (NIC). Configuration is done in multiple steps, so called stages.
#### Stage :one:: DHCP  and TFTP
If it is configured in BIOS/EFI, after obtaining an IP adress from the DHCP server, the NIC requests a `filename` and an IP address for a so called `NextServer`. It will then contact this server using the `trivial file transfer protocol` (TFTP) and try to fetch a bootfile using the `filename` from the DHCP server.
This file is called [ipxe.efi](https://github.com/usegalaxy-eu/infrastructure-playbook/blob/master/files/dnbd3/ipxe.efi) in our case and is a binary, that was compiled from the official [iPXE Repository](https://github.com/ipxe/ipxe) by embedding our [ipxe script](https://gist.github.com/mira-miracoli/c7463fad492fcd6671561dc8df2547c0)


#### Stage :two:: Kernel and InitramFS
This iPXE extends the NIC's firmware included pPXE and allows the NIC to use HTTP instead of TFTP. The embedded script contains the link to a `boot.menu` file which is fetched from dnbd3-primary.galaxyproject.eu. When executing this [boot.menu](https://github.com/usegalaxy-eu/infrastructure-playbook/blob/master/templates/dnbd3/boot.menu.j2) file, it fetches a `kernel` and `initramFS` using HTTP and executes a boot command in which some `SLX` variables are set and which could be extended in order to set a [root-password]. Please keep in mind that the HTTP server is protected by network restriction only.
#### Stage :three:: SLX and DNBD3
SLX (StateLess eXtensions) is the company which initially developed the dnbd3 protocol, but the [repository](https://git.openslx.org/) is now maintained by the University of Freiburg.
In the so called 'Stage 3' the client boots the initramFS and kernel using the provided kernel command line, fetches SLX configurations and sets up the dnbd3 device:
 - Detects hardware
 - Sets up network
 - Downloads the [SLX config][slx_config] from HTTP server
 - Sets up [RW space](1#disk-setup) using a disk if it contains PARTLABEL="OPENSLX_SYS" and using RAMdisk as fallback otherwise
 - Combines the RW space with the RO DNBD3 image as `xloop` device called as set in `SLX_SYSTEM_PARTITION_IDENTIFIER` (usually 'system')
 - Mounts `/dev/mapper/root` to `/sysroot`
 - Downloads the 'pxe-config-tarball' from the HTTP server which is built from [pxe-config-tarball](https://github.com/usegalaxy-eu/pxe-config-tarball/tree/main) repository using Jenkins. Unpacks it to `/`
 - `switch_root /sysroot`
#### Stage :four: : DNBD3
Now the actual VGCN image boots and you should see a login screen in IPMI and be able to SSH.

## Servers, Repositories, Artifacts and Flow

This section should give an overview of the different entities involved in the bare metal set-up. From repositories where the code is tracked to the infrastructure servers that build the artifacts later consumed by the VGCN worker nodes.

<img src="./images/pxe-infrastructure.png" />

### Scope
This documentation describes:
- How the infrastructure providing netboot/pxe are configured
- The pipeline for building `VGCN images` and its artifacts
- The pipeline that creates and delivers the 'pxe-config-tarball'
- How the nodes are managed and added to HTCondor **after** boot
### Infrastructure
#### dnbd3-primary.galaxyproject.eu
**aka sn12.bi.privat**
This server hosts several essential services required to boot worker nodes:

#### `TFTP` Server
- Configured via `Infrastructure-Playbook`
- Provides:
  - [ipxe.efi]()

#### `HTTP` Server
- Serves:
  - the Linux kernel and `initramfs` needed for iPXE
  - [`slx.config`][slx_config]
    - specifies
      - DNBD server IP
      - the name of the linux image
      - the name of config tarball
      - partition information
  - `config.tgz`:
      - SSH keys (`authorized_keys`)
      - node configuration files

#### `DNBD`
- Hosts the final `VGCN image`, which the `vgcn compute node` mounts during PXE boot


This node is a ESXi machine, which can be handled using [vSphere](https://vcsa-rz.intra.uni-freiburg.de).
It runs the above mentioned services: TFTP, HTTP, DNBD3 and all artifacts created by the [VGCN-Image-Pipeline] and [pxe-config-tarball]
Jenkins acts as the orchestrator for the `VGCN image` build pipeline. It executes two primary scripts:

### :factory: Build Images
[VGCN-Image-Build](https://build.galaxyproject.eu/job/usegalaxy-eu/job/VGCN-Image-Build) Jenkins project builds the actual `VGCN image` using Packer and Ansible, as well as a kernel and an initramFS. All three artifacts are then copied to the [dnbd3-primary](1#dnbd3-primary.galaxyproject.eu).
The pipeline is defined in Groovy in the [jenkins-scripts repository](https://github.com/usegalaxy-eu/jenkins-scripts/blob/vgcn-pipeline-pxe/Jenkinsfile).
#### 📦️ Build
If you want to trigger a new image build, click on `Build with Parameters` and select the following for a 'normal' pxe image (yes, **always** with GPU):

1. **GENERIC**: generic
2. **TEMPLATE**: rockylinux-9-latest-x86_64
3. **FLAVOR**: workers-gpu
4. **SCOPE**: internal
5. **PXE**: pxe
6. **DELIVER_KVM**: no
7. **FORMAT**: qcow2

The last one is especially important because the [SLX config][slx_config] is configured to use qcow2 and not raw and otherwise the image is not compressed which can lead to creepy disk errors after several days.
#### :rocket: Rollout
In order to bring this new image to production, do the following

1. Change the revision ID in the [SLX config][slx_config]
2. [Reboot](1#reboot-%2F-powercycle) a worker node, that is currently idle or, if you want to be on the safe side, move that worker to the [test host group](https://github.com/usegalaxy-eu/vgcn-infrastructure-playbook/blob/main/hosts) before rebooting it, so it does not get integrated into production after reboot and CI run.
3. SSH to the node check that the new image was picked (you should see it in the motd) and make sure everything looks good. (Maybe run a test job from the training-pxe-test), if you added the node to the test host group. If so, just reboot other servers (if immediate rollout is required). Else: Change the revision ID back the value before (on the dnbd3-primary.galaxyproject.eu and in the Ansible variable).

### 🗜️ `pxe-config-tarball`: This builds the `config.tgz` archive, which includes runtime configuration files and SSH keys for the `vgcn compute node`.

These scripts interact with internal and external repositories to gather configurations, fetch dependencies, and trigger provisioning.

## Repositories Used
- **`jenkins-scripts`** (private): Contains Jenkins pipeline scripts that control the image build and configuration packaging process.
- **[`vgcn` playbook](https://github.com/usegalaxy-eu/vgcn)**: Contains the Packer configuration and Ansible provisioning roles used to build the `VGCN image`.
- **[`pxe-config-playbook`](https://github.com/usegalaxy-eu/pxe-config-playbook)**: Ansible playbook that generates the `config.tgz` archive, containing system- and user-level configuration for the vgcn compute node.

## Output Artifacts

- `VGCN image`: Built by Packer using a Kickstart file and provisioned via Ansible. This is the disk image that the PXE boot process ultimately mounts.
- `config.tgz`: A compressed archive containing configuration files for
  - automount/NFS
  - HTCondor job scheduler
  - Telegraf data connector
  - `authorized_keys` for SSH public key-based login setup

  The structure looks like:
     ```
    ├── etc
    │   ├── auto.data
    │   ├── auto.master.d
    │   │   └── data.autofs
    │   ├── auto.usrlocal
    │   ├── condor
    │   │   └── config.d
    │   │       └── 99-cloud-init.conf
    │   └── telegraf
    │       └── telegraf.d
    │           └── output.conf
    └── home
        └── centos
            └── .ssh
                └── authorized_keys
   ```

## Infrastructure Components



## Details from A-Z
### Disk Setup

|  Variable                                  | Place              | Info               |
|--------------------------------------------|--------------------|--------------------|
| **SLX_WRITABLE_DEVICE_IDENTIFIER**         | [SLX config][slx_config]     | During disk detection SLX only uses disks with this label set as partition label see the [Debugging](1#manual-check-and-fix-the-disk-setup) section for how to set it on the server |
| **SLX_SYSTEM_PARTITION_IDENTIFIER**         |  [SLX config][slx_config] | Sets the name for the xloop device created by SLX during boot |
| **SLX_WRITABLE_DEVICE_PARTITION_TABLE**     |  [SLX config][slx_config] | a space separated table consisting of 4 columns <type> <name> <size> <crypt>, see below. |

#### **SLX_WRITABLE_DEVICE_PARTITION_TABLE**
Following is copied from [https://git.openslx.org](https://git.openslx.org/openslx-ng/systemd-init.git/tree/dev-tools/example-openslx.config?h=gitlab-ci-escience)

This is a kind of partition table for the scratch device.

A line is composed of:
`      <type>         <name> <size> <crypt>`

* `Type` can be 'thin-snapshot', 'thin-volume', 'snapshot' or 'linear'.
* `Name` is just a name of the device mapper device created.
* `Size` are precalculated on the writable device found, so percentages
are calculated on the total device size. Lower and upper bounds can
be set, these will be attributed in a first-come-first-serve manner
(with respect to line order).
* `Crypt` would encrypt the device mapper device with a temporary key.
0 to disable (default), 1 to enable. Currently does not support persistent
keys.

Example of a more advanced partition config:
~~~
    thin-snapshot   root    10G    1
    thin-volume     tmp     20G    0
    linear          data0   5-10G  1
    linear          data1   1-50%  1
~~~
There needs to be at least one snapshot device configured, if none are set
it will default to use the *entire* writable device as a thin-snapshot:
~~~
SLX_WRITABLE_DEVICE_PARTITION_TABLE='
	thin-snapshot     root    100%
'
~~~
**:point_right: We actually use the above and a persistant partition for docker, see [GitHub](https://github.com/usegalaxy-eu/infrastructure-playbook/blob/7e920f8b06d0c0f024e2bb517c75bae6c01ae2c9/templates/dnbd3/config.j2)**
~~~
SLX_WRITABLE_DEVICE_PARTITION_TABLE='
thin-snapshot  root  50%  0
linear         tank  50%  0
'
~~~
#### :whale: Create Persistant Storage For Docker And Mount It
This is done in the [cloudinit-pxe](https://github.com/usegalaxy-eu/vgcn/blob/9942e36b53796e270bed461130b8a022fe2abe46/ansible/roles/cloudinit-pxe/files/boot-cron.sh#L8-L23) script which is a cronjob run at boot.

### :factory: Image building pipeline
~~~mermaid
sequenceDiagram
	participant Jenkins
	participant Webserver
	create participant VGCN
	Jenkins->>VGCN: fetches
	create participant jenkins-scripts
	Jenkins->>jenkins-scripts: fetches and executes
	activate jenkins-scripts
	jenkins-scripts->>VGCN: sets parameters and starts build.py
	activate VGCN
	create participant packer
	VGCN->>packer: starts packer
	activate packer
	create participant image
	packer->>image: builds image with kickstart
	activate image
	create participant Dracut-role
	packer->>Dracut-role: pulls
	Dracut-role-->>packer: ansible role
	packer->>image: provisions with ansible
	image-->>packer: finishes provisioning
	deactivate image
	packer-->>vgcn: finishes build
	deactivate packer
	VGCN->>Webserver: copies image

	deactivate VGCN
	deactivate jenkins-scripts
~~~

### :electric_plug: Reboot / Powercycle
**SSH**  
:smile:  
**non-SSH**  
Use `ipmitool` on [jumphost][jumphost] to automate the reboot with bash.
For individual nodes use the same, or use the ipmi web interface and trigger a 'powercycle'. The hostnames *should* be sp<node-number>.bi.privat but you can look them up in [infoblox][infoblox].

## Add Nodes to the Bare Metal Compute Cluster
(from issue[#756](https://github.com/usegalaxy-eu/issues/issues/756))

:label: **For each node the following needs to be checked:**

1. Is the DHCP `next server` set accordingly, or is it set globally?
2. Set the hostname, following the scheme: `cxxxmxxxgx-nxxxx.bi.privat`
3. Set the IPMI credentials as set in the ansible-vault

🚧 **Add the nodes to the new [vgcn-infrastructure-playbook](github.com/usegalaxy-eu/vgcn-infrastructure-playbook)**
1. Select a host-group (use `[test]` first)
2. Wait for the deployment to finish and check [Telegraf Script was added to VGCN-Infrastructure-Playbook](github.com/usegalaxy-eu/vgcn-infrastructure-playbook/pull/13) and using this [dashboard](https://stats.galaxyproject.eu/goto/ngJ_Mg_Ng?orgId=1) we can monitor if the storage config is correct for each pxe node


:rocket: **Once the disk setup is correct (everything green in the dashboard), we can move the nodes from `[test]` group to their production group (e.g. `compute`)**

### GPU-Compute mixed nodes
- If we migrate large GPU nodes, that contain only one GPU but large compute resources (>100 cores and > 100GB ram), add them to a new TPV destination that accepts both compute and gpu jobs but limits the job size to leave some space for undemanding GPU jobs (e.g. max memory 80G).
- Add a rule that sets the docker and singularity `arguments_extra` like in the pxe gpu only destinations, but only if it's a docker/singularity job and only if a GPU is used

## Debugging

### :floppy_disk: **Manual check and fix the disk setup**

1. Boot and check with `cat /opt/openslx/dmsetup.state` the type must be `1`
2. If not check that there is a partition `blkid | grep OPENSLX_SYS`
3. If not install `gdisk`, make GPT partition table and create partition (`n`) and name it (`c`) `OPENSLX_SYS`
4. Reboot and check that it worked
5. Check that /scratch is mounted
## Glossary

- **PXE (Preboot Execution Environment)**: Allows a machine to boot over the network.
- **initramfs**: Temporary root filesystem loaded into memory during the early boot process.
- **iPXE**: Advanced network boot firmware capable of booting via HTTP, TFTP, iSCSI, etc.
- **TFTP**: Lightweight file transfer protocol used for bootloaders.
- **Packer**: Tool for automating the creation of machine images.
- **Ansible**: Configuration management tool used to provision the image.
- **DNBD**: Distributed Network Block Device; provides the final image storage.

[slx_config]: https://github.com/usegalaxy-eu/infrastructure-playbook/blob/master/templates/dnbd3/config.j2
[jumphost]: dnbd3.galaxyproject.eu
[infoblox]: https://ipam.noc.uni-freiburg.de/
