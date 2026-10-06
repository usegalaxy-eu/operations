# How To (A-Z)

See the [VGCN PXE reference](../reference/bare_metal_vgcn_pxe.md) for architecture background.
## Add Nodes to the Bare Metal Compute Cluster

(from issue [#756](https://github.com/usegalaxy-eu/issues/issues/756))

### Check for each node

1. Is the DHCP `next server` set accordingly, or is it set globally?
2. Set the hostname, following the scheme: `cxxxmxxxgx-nxxxx.bi.privat`
3. Set the IPMI credentials as set in the ansible-vault

### Add the nodes to the new [vgcn-infrastructure-playbook](https://github.com/usegalaxy-eu/vgcn-infrastructure-playbook)

1. Select a host-group (use `[test]` first)
2. Wait for the deployment to finish and check [Telegraf Script was added to VGCN-Infrastructure-Playbook](https://github.com/usegalaxy-eu/vgcn-infrastructure-playbook/pull/13) and using this [dashboard](https://stats.galaxyproject.eu/goto/ngJ_Mg_Ng?orgId=1) we can monitor if the storage config is correct for each PXE node
3. If not, do the following procedure (e.g. pssh):
4. Check that there is a partition blkid | grep OPENSLX_SYS
5. If not use `parted`, make GPT partition table (`sudo parted -s /dev/sdX mklabel gpt`) and create partition with name OPENSLX_SYS (`sudo parted -s /dev/sda mkpart primary xfs 0% 100% name 1 OPENSLX_SYS`)
6. Reboot and check that it worked
7. Check the dashboard again
8. Once all is green, move the nodes to another host-group

**GPU-Compute mixed nodes**

If we migrate large GPU nodes that contain only one GPU but have large compute resources (>100 cores and >100GB RAM), we should use HTCondor's [partitionable slot feature](https://htcondor.readthedocs.io/en/latest/admin-manual/ep-policy-configuration.html#partitionable-slots); see also [issue #800](https://github.com/usegalaxy-eu/issues/issues/800).

### Move to production

Once the disk setup is correct (everything green in the dashboard), we can move the nodes from `[test]` group to their production group (e.g. `compute`).

## Build and Deploy Images

[VGCN-Image-Build](https://build.galaxyproject.eu/job/usegalaxy-eu/job/VGCN-Image-Build) Jenkins project builds the actual `VGCN image` using Packer and Ansible, as well as a kernel and an initramFS. All three artifacts are then copied to the [dnbd3-primary](../reference/bare_metal_vgcn_pxe.md#dnbd3-primarygalaxyprojecteu).

If you want to build an image with a latest version of a EL major release, then check [here](https://github.com/bwLehrpool/dnbd3/blob/master/.github/workflows/build-kernel-module.yml) if the latest version is already added and if yes, if it builds successfully. If it is not added, please open a PR against this file to add it.

The pipeline is defined in Groovy in the [jenkins-scripts repository](https://github.com/usegalaxy-eu/jenkins-scripts/blob/vgcn-pipeline-pxe/Jenkinsfile).

### Build

If you want to trigger a new image build, click on `Build with Parameters` and select the following for a 'normal' PXE image (yes, **always** with GPU):

1. **GENERIC**: generic
2. **TEMPLATE**: rockylinux-9-latest-x86_64
3. **FLAVOR**: workers-gpu
4. **SCOPE**: internal
5. **PXE**: pxe
6. **DELIVER_KVM**: no
7. **FORMAT**: qcow2

The last one is especially important because the [SLX config][slx_config] is configured to use qcow2 and not raw; otherwise the image is not compressed which can lead to creepy disk errors after several days.

### Rollout

In order to bring this new image to production, do the following:

1. Change the revision ID in the [SLX config][slx_config]
2. [Reboot](#reboot-power-cycle) a worker node that is currently idle or, if you want to be on the safe side, move that worker to the [test host group](#add-nodes-to-the-bare-metal-compute-cluster) before rebooting it, so it does not get integrated into production after reboot and CI run.
3. SSH to the node and check that the new image was picked (you should see it in the MOTD) and make sure everything looks good. Maybe run a test job from the training-pxe-test. If you added the node to the test host group and everything is good, just reboot other servers (if immediate rollout is required). Otherwise, change the revision ID back to the previous value on the dnbd3-primary.galaxyproject.eu and in the Ansible variable.

## Mount a new NFS share

Make sure the shares are accessible on the subnet used by our bare metal cluster. Add it to the [mounts repo](https://github.com/usegalaxy-eu/mounts/blob/main/mountpoints.yml) as usual. Run [VGCN-Infrastructure-Playbook on Jenkins](https://build.galaxyproject.eu/job/usegalaxy-eu/job/VGCN-Infrastructure-Playbook). The new shares should now be available. In case you want to manually debug/check, you can use `pssh` as usual. For a hosts file, run:

```bash
wget https://raw.githubusercontent.com/usegalaxy-eu/vgcn-infrastructure-playbook/refs/heads/main/hosts && sed -i '/^\[.*\]$/{ :a; n; /^\[/!ba; x; d; }' hosts
```

## Reboot / Power cycle

**SSH**

:smile:

**non-SSH**

Use `ipmitool` on `dnbd3.galaxyproject.eu` to automate the reboot with bash.

For individual nodes use the same, or use the IPMI web interface and trigger a 'powercycle'. The hostnames *should* be `sp<node-number>.bi.privat` but you can look them up in [infoblox][infoblox].

### IPMI power cycle — secure procedure

Always read the BMC password from stdin to avoid exposing it in shell history or process listings:

```bash
BMC_HOST="sp<node-number>.bi.privat"   # look up in Infoblox: https://ipam.noc.uni-freiburg.de/
BMC_USER="admin"                        # see exceptions table below

read -rs BMC_PASS
ipmitool -I lanplus -H "$BMC_HOST" -U "$BMC_USER" -P "$BMC_PASS" power cycle

# Verify power state afterwards
ipmitool -I lanplus -H "$BMC_HOST" -U "$BMC_USER" -P "$BMC_PASS" power status
```

> **Never** hard-code BMC passwords in scripts or pass them via environment variables that may appear
> in CI logs.  The `read -rs` pattern above keeps the password out of shell history and process listings.

### Known BMC hostname / user exceptions

Some nodes deviate from the standard `sp<n>.bi.privat` / `admin` convention.  The authoritative source
for BMC credentials is the Ansible vault (`secret_group_vars/`) in the
[infrastructure-playbook](https://github.com/usegalaxy-eu/infrastructure-playbook).

| Compute node | BMC hostname | BMC user | Notes |
|---|---|---|---|
| `spgput4.*` | *(check Infoblox)* | `admin` | GPU node; hostname prefix differs |
| `c128m512g4-n37104.*` | *(check Infoblox)* | `root` | Non-standard BMC user |

Update this table whenever new exceptions are discovered.

## Set a root password

Using the `SLX_ROOT_PASS` variable in the [boot.menu][boot_menu] allows you to set a root password, so you can log in from IPMI console viewer for debugging purposes. Please keep in mind that this is not secure and the password should be randomly created for this purpose, because the [boot.menu][boot_menu] file is only protected by network access restriction of the HTTP server.

## TIaaS

See this [issue](https://github.com/usegalaxy-eu/issues/issues/800) dedicated to the topic and for a short-term solution see the following [PR](https://github.com/usegalaxy-eu/vgcn-infrastructure-playbook/pull/17) as an example:

**Step 1:**

Create a `group_vars/<your-training-name>/vars.yml` with the following content. `<your-training-name>` can be an arbitrary string, `<your-training-identifier>` must be the same as in TiaaS.

```yaml
galaxy_group: training-<your-training-identifier>
```

**Step 2:**

Create a host group with the same name and **move** as many hosts as you like there:

```ini
[<your-training-name>]
c192m1536-n3701.bi.privat
c192m1536-n3702.bi.privat

[compute]
```

(Remove the hosts from compute and add them to the training group)


[vgcn]: https://github.com/usegalaxy-eu/vgcn/tree/pxe
[vgcn-image-pipeline-jenkins]: https://build.galaxyproject.eu/job/usegalaxy-eu/job/VGCN-Image-Build
[vgcn-infra-playbook-jenkins]: https://build.galaxyproject.eu/job/usegalaxy-eu/job/VGCN-Infrastructure-Playbook
[slx_config]: https://github.com/usegalaxy-eu/infrastructure-playbook/blob/master/templates/dnbd3/config.j2
[infoblox]: https://ipam.noc.uni-freiburg.de/
[pxe-config-tarball]: https://github.com/usegalaxy-eu/pxe-config-tarball
[boot_menu]: https://github.com/usegalaxy-eu/infrastructure-playbook/blob/master/templates/dnbd3/boot.menu.j2
[hosts]: https://github.com/usegalaxy-eu/vgcn-infrastructure-playbook/blob/main/hosts
