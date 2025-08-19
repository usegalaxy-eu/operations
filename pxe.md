# Bare Metal VGCN with Network Boot

In contrast to the industry trend, using compute nodes without virtualization can have several benefits, such as
- less overhead for hypervisors
- reduced system complexity
- more direct control
- almost no overhead for adding or removing servers

While installing and maintaining tens to hundreds of disk installations on these servers is a tedious task and economically unviable,
running the servers in a network boot setup keeps a whole cluster maintainable with relatively few resources.

## Basic concepts

# Setting Up A PXE Virtual Galaxy Compute Node (VGCN)

This documentation outlines the automated image building process for setting up a **PXE-bootable Virtual Galaxy Compute Node (vgcn)**, used within the Galaxy Europe infrastructure. The system uses Jenkins, Packer, Ansible, and iPXE to provision compute nodes that boot over the network using images built via this process.


**Reference**: [Virtual Galaxy Compute Nodes](https://github.com/usegalaxy-eu/vgcn)
```
Galaxy Europe runs jobs on compute nodes belonging to the bwCloud/de.NBI-cloud. These compute nodes are known as "Virtual Galaxy Compute Nodes" (VGCN).

Virtual Galaxy Compute Nodes boot from VGCN images, which are built off this repository and made available as GitHub releases and on this static site.
```
## Scope
This documentation describes:
- The workflow for building `VGCN images` using Jenkins and associated scripts
- The tools and repositories involved in the image building process
- The role of the PXE infrastructure in booting the `vgcn compute node`
- The artifacts generated during the process and their purposes
## Jenkins
Jenkins acts as the orchestrator for the `VGCN image` build pipeline. It executes two primary scripts:

- `vgcn-pxe-pipeline`: This pipeline builds the actual `VGCN image` using Packer and Ansible.

- `pxe-config-playbook`: This builds the `config.tgz` archive, which includes runtime configuration files and SSH keys for the `vgcn compute node`.

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

### `dnbd01` — PXE Head Node

This server hosts several essential services required to boot and run a `vgcn compute node`:

#### `TFTP` Server
- Manually configured
- Provides:
  - PXE bootloader (e.g., iPXE binary)
  - iPXE script for boot instructions
  - The initial handoff from iPXE to PXE ROM happens here

#### `HTTP` Server
- Serves:
  - the Linux kernel and `initramfs` needed for iPXE
  - [`slx.config` (gist)](https://gist.github.com/mira-miracoli/72fed7b3ce6ed30345283ce621ccf6aa)
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


## Workflow of the image building process
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

## Add Nodes to the Bare Metal Compute Cluster
(from issue[#756](https://github.com/usegalaxy-eu/issues/issues/756))

:label: **For each node the following needs to be checked:**

1. Is the DHCP `next server` set accordingly, or is it set globally?
2. Set the hostname, following the scheme: `cxxxmxxxgx-nxxxx.bi.privat`
3. Set the IPMI credentials as set in the ansible-vault

🚧 **Add the nodes to the new [vgcn-infrastructure-playbook](github.com/usegalaxy-eu/vgcn-infrastructure-playbook)**
1. Select a host-group (use `[test]` first)
2. Wait for the deployment to finish and check [Telegraf Script was added to VGCN-Infrastructure-Playbook](github.com/usegalaxy-eu/vgcn-infrastructure-playbook/pull/13) and using this [dashboard](https://stats.galaxyproject.eu/goto/ngJ_Mg_Ng?orgId=1) we can monitor if the storage config is correct for each pxe node

:hammer: **Manual check and fix the disk setup**

1. Boot and check with `cat /opt/openslx/dmsetup.state` the type must be `1`
2. If not check that there is a partition `blkid | grep OPENSLX_SYS`
3. If not install `gdisk`, make GPT partition table and create partition (`n`) and name it (`c`) `OPENSLX_SYS`
4. Reboot and check that it worked
5. Check that /scratch is mounted

:rocket: **Once the disk setup is correct (everything green in the dashboard), we can move the nodes from `[test]` group to their production group (e.g. `compute`)**

### GPU-Compute mixed nodes
- If we migrate large GPU nodes, that contain only one GPU but large compute resources (>100 cores and > 100GB ram), add them to a new TPV destination that accepts both compute and gpu jobs but limits the job size to leave some space for undemanding GPU jobs (e.g. max memory 80G).
- Add a rule that sets the docker and singularity `arguments_extra` like in the pxe gpu only destinations, but only if it's a docker/singularity job and only if a GPU is used

## Glossary

- **PXE (Preboot Execution Environment)**: Allows a machine to boot over the network.
- **initramfs**: Temporary root filesystem loaded into memory during the early boot process.
- **iPXE**: Advanced network boot firmware capable of booting via HTTP, TFTP, iSCSI, etc.
- **TFTP**: Lightweight file transfer protocol used for bootloaders.
- **Packer**: Tool for automating the creation of machine images.
- **Ansible**: Configuration management tool used to provision the image.
- **DNBD**: Distributed Network Block Device; provides the final image storage.
