# TFTP / autofs startup ordering

The TFTP boot files live on an NFS path managed by autofs (e.g. `/netboot/boot`).  If `tftp.service`
starts before that mount is available, PXE clients will fail to download the bootloader.

To ensure correct ordering, the `tftp.service` unit must declare an `After=` and `Wants=` dependency
on autofs and the network:

```ini
# /etc/systemd/system/tftp.service.d/autofs-after.conf
[Unit]
After=network-online.target remote-fs.target autofs.service
Wants=network-online.target remote-fs.target autofs.service
# Optionally, also fail if the specific mount disappears:
# RequiresMountsFor=/netboot/boot
```

Apply with:

```bash
systemctl daemon-reload
systemctl restart tftp.service
systemctl status tftp.service
ls /netboot/boot          # verify boot files are visible before declaring the service healthy
```

> **Caveat:** `RequiresMountsFor=` causes the service to stop if the NFS mount unmounts later.
> Use it only if you want `tftp.service` to restart on NFS hiccups.  Without it, tftp will keep
> running but serve stale or missing files if the mount disappears.

This drop-in is managed via Ansible in the `dnbd3primary` host group of the
[infrastructure-playbook](https://github.com/usegalaxy-eu/infrastructure-playbook).
See also power-outage-recovery.md §A (TFTP / autofs startup ordering).

See the [TFTP server reference](../reference/bare_metal_vgcn_pxe.md#tftp-server) for service details.
