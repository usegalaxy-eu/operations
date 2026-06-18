---
title: Power Outage Recovery Runbook
---

# Power Outage Recovery Runbook

This runbook captures the lessons and procedures derived from the "Power outage afterplay" incident
(usegalaxy-eu/issues#990).  Follow the sections below **in order** during a full datacenter power
recovery.  Each section links to the more detailed, per-topic docs that live elsewhere in this repo.

## Coverage map

| Issue topic | Addressed in |
|---|---|
| A – TFTP / autofs startup ordering | [bare_metal_vgcn_pxe.md – TFTP Service Dependencies](#a-tftp--autofs-startup-ordering) + `bare_metal_vgcn_pxe.md` |
| B – Jenkins worker / Python environment | [jenkins.md](./jenkins.md) + [this doc §B](#b-jenkins-workers--pre-flight-checks) |
| C – Bare-metal power cycling (IPMI) | [bare_metal_vgcn_pxe.md – Power Cycle](./bare_metal_vgcn_pxe.md#reboot--power-cycle) + [this doc §C](#c-bare-metal-power-cycling) |
| D – Host availability validation (pssh) | [bare_metal_vgcn_pxe.md – Cluster Health](./bare_metal_vgcn_pxe.md#cluster-health-validation) + [this doc §D](#d-host-availability-validation) |
| E – KVM / NFS volume recovery | [kvm-server.md – NFS/virsh recovery](./kvm-server.md#5-power-outage-recovery) + [this doc §E](#e-kvmnfs-data-volume-recovery) |
| F – VM SSH access fallback | [kvm-server.md – SSH fallback](./kvm-server.md#ssh-access-fallback-via-jenkins) + [this doc §F](#f-vm-ssh-access-fallback) |
| G – ClickHouse / Plausible recovery | [clickhouse.md](./clickhouse.md) + [this doc §G](#g-clickhouseplausible-recovery) |

---

## Prerequisites

Before starting recovery, confirm:

- [ ] Power is stable and UPS systems are back to normal.
- [ ] Network switches are up (check SNMP/Grafana or walk the rack).
- [ ] At least **one** SSH-reachable jumphost is available (see [bare_metal.md](./bare_metal.md)).
- [ ] You have access to Infoblox/IPAM for BMC hostname lookups: <https://ipam.noc.uni-freiburg.de/>
- [ ] Jenkins `build.galaxyproject.eu` is reachable **or** you can work via the gold/internal worker (§F / §B).

---

## A – TFTP / autofs Startup Ordering

### What failed

The `tftp.service` on `dnbd3-primary.galaxyproject.eu` started before the autofs-managed NFS mount
`/netboot/boot` was available, leaving PXE boot files inaccessible.

### Remediation

Ensure `tftp.service` (and any other service whose data lives on an autofs-mounted path) declares the
correct systemd ordering.  On the TFTP host:

```ini
# /etc/systemd/system/tftp.service.d/autofs-after.conf
[Unit]
After=network-online.target remote-fs.target autofs.service
Wants=network-online.target remote-fs.target autofs.service
# If the mount path is known at deploy time, also add:
# RequiresMountsFor=/netboot/boot
```

Reload and verify:

```bash
systemctl daemon-reload
systemctl restart tftp.service
systemctl status tftp.service
ls /netboot/boot          # must list files before tftp is marked active
```

> **Note:** `RequiresMountsFor=` stops the service if the mount disappears later.  Use it only if you
> want the service to fail (and restart) when the NFS path becomes unavailable.

This is managed via Ansible in the [infrastructure-playbook](https://github.com/usegalaxy-eu/infrastructure-playbook)
host group `dnbd3primary`.  See also [bare_metal_vgcn_pxe.md](./bare_metal_vgcn_pxe.md) – TFTP Server section.

---

## B – Jenkins Workers / Pre-flight Checks

> Detailed worker documentation lives in [jenkins.md](./jenkins.md).

During the incident, only the **internal** worker was available, and it lacked the required `python`/`uv`
tooling needed to run some playbooks.

### Pre-flight checklist before running playbooks

Run this before triggering any Jenkins job during a recovery:

```bash
# 1. Confirm which workers are online and connected
# Go to: https://build.galaxyproject.eu/computer/
# Check that at least one EXTERNAL worker is listed as "online".

# 2. If only the internal worker is available, verify tooling
ssh <internal-worker-host>
python3 --version    # must exist
uv --version         # must exist; install with: curl -LsSf https://astral.sh/uv/install.sh | sh
ansible --version    # must exist

# 3. Check vault access
ansible-vault view /path/to/vault/file --vault-password-file ~/.vault_pass
```

See [jenkins.md](./jenkins.md) for the full worker setup and tooling requirements.

---

## C – Bare-Metal Power Cycling

> See [bare_metal_vgcn_pxe.md – Reboot / Power Cycle](./bare_metal_vgcn_pxe.md#reboot--power-cycle) for
> the canonical procedure.

### Quick reference — IPMI power cycle via `ipmitool`

```bash
# Standard nodes: BMC hostname scheme is sp<node-number>.bi.privat
# Look up BMC hostnames in Infoblox: https://ipam.noc.uni-freiburg.de/

BMC_HOST="sp<node-number>.bi.privat"
BMC_USER="admin"           # override per the exceptions table below

# Read the password from stdin (never pass on command line)
read -rs BMC_PASS
ipmitool -I lanplus -H "$BMC_HOST" -U "$BMC_USER" -P "$BMC_PASS" power cycle

# Check power status afterwards
ipmitool -I lanplus -H "$BMC_HOST" -U "$BMC_USER" -P "$BMC_PASS" power status
```

> **Security note:** Always use `read -rs BMC_PASS` or a secrets manager.  Never pass passwords via
> `-P` on the command line in scripts that are version-controlled or logged.

### Bulk power cycle with a hosts file

```bash
# Build a hosts file for ipmitool iteration (uses vgcn-infrastructure-playbook hosts)
wget https://raw.githubusercontent.com/usegalaxy-eu/vgcn-infrastructure-playbook/refs/heads/main/hosts \
  -O /tmp/vgcn-hosts
# Strip section headers, keeping only hostnames:
grep -v '^\[' /tmp/vgcn-hosts | grep -v '^$' | grep -v '^#' > /tmp/vgcn-bmc-hosts.txt

read -rs BMC_PASS
while IFS= read -r node; do
  bmc="sp${node%%.*}.bi.privat"   # derive BMC hostname — verify against Infoblox
  echo "Power cycling $bmc ..."
  ipmitool -I lanplus -H "$bmc" -U admin -P "$BMC_PASS" power cycle
done < /tmp/vgcn-bmc-hosts.txt
```

### Known BMC hostname / user exceptions

Some nodes do **not** follow the standard `sp<n>.bi.privat` / `admin` convention.  Record exceptions here
and keep them in sync with the canonical inventory (Infoblox / ansible vault):

| Compute node | BMC hostname | BMC user | Notes |
|---|---|---|---|
| `spgput4.*` | *(check Infoblox)* | `admin` | GPU node; hostname prefix differs |
| `c128m512g4-n37104.*` | *(check Infoblox)* | `root` | Non-standard user; verify before use |

> **Keep this table up to date.** The authoritative source for BMC credentials is the Ansible vault
> (`secret_group_vars/`) in the infrastructure-playbook.

---

## D – Host Availability Validation

After powering on the cluster, verify that compute nodes are reachable before re-enabling the HTCondor
scheduler.

### Using `pssh`

```bash
# Get a fresh hosts file
wget https://raw.githubusercontent.com/usegalaxy-eu/vgcn-infrastructure-playbook/refs/heads/main/hosts \
  -O /tmp/vgcn-hosts
sed -i '/^\[.*\]$/{ :a; n; /^\[/!ba; x; d; }' /tmp/vgcn-hosts   # strip section headers

# Run a no-op command across all nodes
pssh -h /tmp/vgcn-hosts -l root -t 30 -i "hostname && uptime"

# Count successful vs failed responses
pssh -h /tmp/vgcn-hosts -l root -t 30 -i "echo OK" 2>&1 | grep -c '\[SUCCESS\]'
```

> **Expected result:** All nodes return `[SUCCESS]`.  Nodes still booting or unreachable show
> `[FAILURE]` or `[TIMEOUT]`.  Investigate those before allowing jobs to run on them.

### Alternative: HTCondor slot check

```bash
condor_status -totals     # shows available / claimed / offline slots
condor_status | grep Offline
```

---

## E – KVM / NFS Data Volume Recovery

> Full details in [kvm-server.md – Power Outage Recovery](./kvm-server.md#5-power-outage-recovery).

### Quick checklist

```bash
# On the KVM host (build.galaxyproject.eu)

# 1. Confirm NFS data volume is mounted
mount | grep /data        # expected: nfs / nfs4 entry
ls /data/                 # must list galaxy data subdirs

# If missing, remount:
mount -a                  # or: systemctl restart nfs-client.target

# 2. Refresh libvirt storage pool (if defined — see kvm-server.md §4.2 note)
virsh pool-refresh default 2>/dev/null || echo "No libvirt pool defined (expected)"

# 3. Verify expected logical volumes
lvs | grep ^vm            # list VM disk images

# 4. Shut down and restart VMs in the correct order
#    (stop dependents first, then restart in reverse order)
for vm in $(virsh list --name); do
  echo "Shutting down $vm"
  virsh shutdown "$vm"
done
# Wait for all to stop:
watch -n5 "virsh list --all | grep running"

# 5. Start VMs
virsh start <vm-name>     # repeat for each VM in dependency order
```

See [kvm-server.md](./kvm-server.md) for the full procedure including in-VM `vdb` disk validation and
post-recovery CI verification.

---

## F – VM SSH Access Fallback

When direct SSH to a KVM guest is unavailable (e.g. network misconfiguration after reboot), use the
**virsh console** path or jump via Jenkins/gold worker:

```bash
# Option 1: virsh serial console (on the KVM host)
virsh console <vm-name>    # press CTRL-] to detach

# Option 2: SSH via Jenkins internal worker / gold worker
ssh gold.galaxyproject.eu   # or whatever the internal jump host is
ssh <vm-internal-ip>

# Option 3: SSH via dnbd3-primary (if on the same network segment)
ssh dnbd3-primary.galaxyproject.eu
ssh <vm-internal-ip>
```

See [kvm-server.md – SSH Access Fallback](./kvm-server.md#ssh-access-fallback-via-jenkins) for full
details on the Jenkins-mediated path.

---

## G – ClickHouse / Plausible Recovery

> Full details in [clickhouse.md](./clickhouse.md).

### Symptom

ClickHouse logs show messages such as:

```
DB::Exception: Too many (N) broken parts in table <table>. Limit is M (use setting max_suspicious_broken_parts to lower the threshold)
```

### Mitigation

```bash
# SSH into the Plausible / ClickHouse host
ssh stats-internal.galaxyproject.eu   # adjust to actual hostname

# Temporarily raise the broken-parts limit so ClickHouse can start
# (value of 200 is a safe starting point; reduce after recovery)
sudo -u clickhouse clickhouse-client --query \
  "ALTER TABLE plausible_events_db.events MODIFY SETTING max_suspicious_broken_parts = 200"

# Restart ClickHouse
sudo systemctl restart clickhouse-server
sudo systemctl status clickhouse-server

# Validate: check for errors in the log
sudo journalctl -u clickhouse-server -n 50 --no-pager

# Re-check the Plausible analytics dashboard to confirm data is flowing
```

> **Important:** Reset `max_suspicious_broken_parts` back to the default (100) once the broken parts
> have been repaired or removed, to avoid masking future corruption.

See [clickhouse.md](./clickhouse.md) for background, post-recovery validation, and long-term remediation.

---

## Post-Recovery Verification

After all services are back:

- [ ] Galaxy web interface responds at <https://usegalaxy.eu>.
- [ ] Submit a test job and verify it completes.
- [ ] Check Grafana dashboards for queue depth, error rates, NFS latency.
- [ ] Verify PXE nodes are running jobs (`condor_status`).
- [ ] Confirm RabbitMQ / Celery queues are draining (see [celery.md](./celery.md)).
- [ ] Run the infrastructure-playbook on Jenkins to restore any configuration drift.
- [ ] Update the incident log / GitHub issue with recovery timeline.
