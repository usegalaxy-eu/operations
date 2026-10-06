# Debugging

See the [VGCN disk model](../reference/bare_metal_vgcn_pxe.md#disk-setup) for background and [VGCN node operations](../runbooks/vgcn-node-operations.md) for the standard setup procedure.
## Manual check and fix the disk setup

1. Boot and check with `cat /opt/openslx/dmsetup.state` the type must be `1`
2. If not, check that there is a partition: `blkid | grep OPENSLX_SYS`
3. If not, install `gdisk`, make GPT partition table and create partition (`n`) and name it (`c`) as `OPENSLX_SYS`
4. Reboot and check that it worked
5. Check that `/scratch` is mounted

