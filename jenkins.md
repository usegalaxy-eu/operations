---
title: Jenkins CI/CD
---

# Jenkins CI/CD

Jenkins orchestrates our Ansible playbook runs, image builds, and other automation tasks.
The Jenkins master runs on `build.galaxyproject.eu`.

Web UI: <https://build.galaxyproject.eu>

## Workers / Agents

We run two types of workers:

| Worker type | Description | Tooling |
|---|---|---|
| **Internal** | Runs directly on `build.galaxyproject.eu` (or a co-located VM). Always available, even if external network is impaired. | May lack full python/uv stack; see §Pre-flight below |
| **External / gold** | Additional SSH agents on dedicated VMs or bare-metal nodes. Required for most playbook runs. | Full tooling expected |

The worker list is at: <https://build.galaxyproject.eu/computer/>

### Worker availability during outages

During a power outage or major network event, **only the internal worker may be available**.
Before triggering any Jenkins job in this situation, run the pre-flight checks below.

## Pre-flight Checklist Before Running Playbooks

Run these checks whenever workers may have been restarted or are in an unknown state:

```bash
# 1. Confirm at least one external worker is online
#    Go to https://build.galaxyproject.eu/computer/ and look for "online" status.

# 2. SSH into the target worker and verify required tooling
ssh <worker-host>

python3 --version    # must be ≥ 3.9
uv --version         # must exist; if missing:
#   curl -LsSf https://astral.sh/uv/install.sh | sh
#   (or install via system package manager if available)

ansible --version    # must match the version expected by infrastructure-playbook
ansible-galaxy --version

# 3. Verify vault access (requires the vault password to be configured on the worker)
ansible-vault view /path/to/vault/file --vault-password-file ~/.vault_pass
```

### Installing missing tooling on a worker

If `uv` is missing on the internal worker:

```bash
# Install uv (Python package/project manager used in some playbooks)
curl -LsSf https://astral.sh/uv/install.sh | sh
# or if network is restricted:
pip3 install uv
```

If `ansible` is missing or at the wrong version:

```bash
pip3 install --upgrade ansible
# or for a specific version:
pip3 install ansible==<version>
```

## Triggering Playbook Runs Manually

When the Jenkins schedule is disrupted (e.g. after an outage), some playbooks may need manual triggers:

1. Navigate to the relevant job, e.g.
   - [VGCN-Infrastructure-Playbook](https://build.galaxyproject.eu/job/usegalaxy-eu/job/VGCN-Infrastructure-Playbook)
   - [infrastructure-playbook](https://build.galaxyproject.eu/job/usegalaxy-eu/job/infrastructure-playbook)
2. Click **Build Now** (or **Build with Parameters** if the job requires inputs).
3. Monitor the console output for errors.

## Accessing Jenkins Credentials

See [notes.md – How to find out any password from Jenkins](./notes.md#how-to-find-out-any-password-from-jenkins).

## Rolling Back Jenkins

See [notes.md – How to roll-back Jenkins](./notes.md#how-to-roll-back-jenkins).

## SSH Access via Jenkins / Gold Worker

The internal Jenkins worker (gold worker) can serve as an SSH jump host to reach VMs that are not
directly reachable over the public network.

```bash
# Jump to an internal VM via the gold worker
ssh -J gold.galaxyproject.eu <vm-internal-ip-or-hostname>

# Or set up a ProxyJump in ~/.ssh/config:
# Host *.bi.privat
#     ProxyJump gold.galaxyproject.eu
```

See also [power-outage-recovery.md – VM SSH Access Fallback](./power-outage-recovery.md#f--vm-ssh-access-fallback).
