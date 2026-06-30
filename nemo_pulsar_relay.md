# NEMO Pulsar (Relay Mode)

This document describes how usegalaxy.eu dispatches jobs to the **bwForCluster
NEMO** (University of Freiburg HPC) using **Pulsar in relay mode**, and how to
operate and maintain that setup.

Unlike the other remote Pulsar endpoints (which connect over RabbitMQ/AMQP via
`mq.galaxyproject.eu`), NEMO uses the **pulsar-relay**: a small HTTP service
that brokers messages between Galaxy and Pulsar by long-polling, so no inbound
ports or AMQP broker are required on the HPC side.

## Architecture

- **Galaxy** routes selected jobs to the `pulsar_eu_nemo` runner. The runner
  speaks to the relay over HTTP using credentials stored in the vault.
- **Relay** is an HTTP broker running on a bw-cloud VM. It holds pending
  messages in a Redis-compatible store so an in-flight job is not lost across a
  relay restart.
- **Pulsar** runs on a NEMO login node. It long-polls the relay for new job
  setup / status / kill messages, submits the actual work to **Slurm**, and
  publishes status updates back to the relay. Data is staged too, not just
  control messages: job inputs are transferred in for the Slurm job, and
  results are transferred back to Galaxy on completion.
- Tool dependencies are resolved as **Singularity/Apptainer** containers pulled
  from **CVMFS** (`/cvmfs/singularity.galaxyproject.org/all/`).

## Components and where they live

| Component | Host | Notes |
|-----------|------|-------|
| Galaxy runner `pulsar_eu_nemo` | usegalaxy.eu | Defined in [`infrastructure-playbook`](https://github.com/usegalaxy-eu/infrastructure-playbook) job conf; creds from vault |
| TPV destination `pulsar_nemo_tpv` | usegalaxy.eu | Defined in [`infrastructure-playbook`](https://github.com/usegalaxy-eu/infrastructure-playbook) TPV destinations; tag `nemo-pulsar` |
| pulsar-relay | bw-cloud VM | Deployed by the [`pulsar-relay-role`](https://github.com/usegalaxy-eu/pulsar-relay-role); systemd service `pulsar-relay`, listens on `:9000`, Redis-compatible backend |
| Pulsar | NEMO login node | Deployed by the [`pulsar-nemo-login-role`](https://github.com/usegalaxy-eu/pulsar-nemo-login-role); submits to Slurm, supervised by supervisord |

## Routing a job to NEMO

The TPV destination `pulsar_nemo_tpv` requires the scheduling tag
`nemo-pulsar`. A job is only sent to NEMO if it carries that tag. Ways this can
happen:

1. **User-level opt-in**: a user selects the NEMO compute resource under
   [User -> Preferences -> Manage Information -> Use distributed compute
   resources](https://usegalaxy.eu/user) ("Freiburg (Germany) - bwForCluster
   NEMO 2").
2. **Per-user TPV rule**: an entry in `tpv/users.yml` that attaches the
   `nemo-pulsar` requirement for a given user (used for testing).
3. **Per-tool rule**: a TPV rule can tag a specific tool so it always routes
   to NEMO, independent of the user.

If a job is not tagged, it runs on the default destination as usual.

## Relay service (bw-cloud)

Deployed by the
[`pulsar-relay-role`](https://github.com/usegalaxy-eu/pulsar-relay-role). The
relay runs as a systemd unit; key configuration is delivered via an environment
file (`/etc/pulsar-relay.env`, referenced from the unit):

```ini
PULSAR_STORAGE_BACKEND=valkey
PULSAR_VALKEY_HOST=localhost
PULSAR_VALKEY_PORT=6379
PULSAR_BOOTSTRAP_ADMIN_USERNAME=admin
PULSAR_BOOTSTRAP_ADMIN_PASSWORD=<in vault>
PULSAR_JWT_SECRET_KEY=<in vault>
```

### Storage backend (and a version requirement worth knowing)

The relay's `PULSAR_STORAGE_BACKEND=valkey` setting selects a Redis-compatible
backend. The role installs this per-OS, because there is an important version
floor: the relay's 0.2.x storage layer uses **XRANGE exclusive-range bounds**,
which only exist in **Redis 6.2+ / Valkey**. An older backend (e.g. the Redis
6.0.x shipped by Ubuntu 22.04's apt) makes every `/messages/poll` return
**500** with "Invalid stream ID".

- **Debian/Ubuntu** (the production relay VM): the role installs **Redis 7.x**
  from the redislabs PPA and asserts the version is >= 7, so the old 6.0.x can
  never silently come back.
- **RHEL/Rocky** (e.g. Rocky Linux 10): the role installs **Valkey 8.x** from
  AppStream, modern by default, no PPA needed, no version-floor problem.

Because storage is persisted to the backend, the admin user and any in-flight
messages survive a relay restart.

Health check:

```bash
curl http://localhost:9000/health
# {"status":"healthy", ...}
```

Useful operations:

```bash
# relay logs (watch for the NEMO login-node IP long-polling)
sudo journalctl -u pulsar-relay -f

# restart
sudo systemctl restart pulsar-relay

# confirm the backend is up (Debian/Ubuntu)
redis-cli -a '<password>' ping   # -> PONG
# confirm the backend is up (RHEL/Rocky)
valkey-cli -a '<password>' ping   # -> PONG
```

> **Operational caveat:** the relay lives on a bw-cloud VM under a tight
> project quota. If the VM is stopped or shelved (e.g. to free quota for
> another instance), the relay goes offline and NEMO can no longer pick up
> jobs, Galaxy will still *accept* jobs, they simply won't run. Power the VM
> back on (`openstack server start pulsar-relay`); the relay and backend
> auto-start (both are `enabled`), and NEMO reconnects on its own.

## Pulsar (NEMO login node)

Deployed by the
[`pulsar-nemo-login-role`](https://github.com/usegalaxy-eu/pulsar-nemo-login-role),
which installs Pulsar into a virtualenv, templates `app.yml` and
`job_metrics_conf.xml`, and sets up process management. The install location
(`pulsar_nemo_home`, default `~/pulsar`) is a role variable, so `HOME` /
install path is configurable per deployment.

NEMO does not provide user-level systemd, so Pulsar is kept alive by
**supervisord**, running entirely in user space. supervisord is started on boot
via an `@reboot` cron entry and restarts Pulsar automatically if it exits. (A
small bash-loop wrapper script remains in the role's `templates/` as a
fallback, but supervisord is the supported path.)

Pulsar configuration (`~/pulsar/config/app.yml`):

```yaml
log_level: INFO
job_metrics_config_file: job_metrics_conf.xml
message_queue_url: http://<relay-host>:9000/
message_queue_username: admin
message_queue_password: <in vault>
staging_directory: <pulsar_nemo_home>/jobs_directory

container_resolvers:
  - type: apptainer

managers:
  _default_:
    type: queued_cli
    job_plugin: Slurm
```

Important points:

- The manager **must** be `queued_cli` with `job_plugin: Slurm`. With
  `queued_python` the job runs directly on the **login node** instead of being
  submitted to Slurm, not allowed, and will get the account flagged by the RZ
  admins.
- `job_metrics_conf.xml` enables the `core`, `cgroup` and `hostname` metrics
  plugins so the compute hostname and resource usage show up in Galaxy.
- The relay client refuses plaintext `http://` to a non-localhost relay unless
  `PULSAR_RELAY_ALLOW_INSECURE=1` is set (the launcher sets it). This is a
  stopgap until the relay is served over HTTPS, at which point the flag should
  be dropped (the login role has a variable wired for this).

Useful operations:

```bash
# supervisord-managed Pulsar status / control
supervisorctl -c ~/pulsar/supervisord.conf status
supervisorctl -c ~/pulsar/supervisord.conf restart pulsar

# tail the supervisor-managed log
tail -f ~/pulsar/pulsar-supervisor-err.log

# is a job actually on Slurm (and not the login node)?
squeue -u <user>

# completed-job history
sacct -j <slurm_job_id> --format=JobID,State,ExitCode
```

## Verifying end-to-end

1. From usegalaxy.eu, run a small tool (e.g. **ChangeCase** or **FastQC**) as a
   user routed to NEMO.
2. On NEMO, `squeue -u <user>` should show the job on a **compute node**
   (e.g. `n3308`), not the login node.
3. The relay log should show the NEMO login-node IP POSTing to
   `/messages/poll`, and the Galaxy side polling for `job_status_update`.
4. The job should reach **ok** in the Galaxy UI, and the job metrics should
   list the Singularity container ID pulled from CVMFS.

## Troubleshooting

**Every `/messages/poll` returns 500 ("Invalid stream ID")**
The relay's backend is older than Redis 6.2 and doesn't support XRANGE
exclusive-range bounds, which the 0.2.x relay relies on. Check the version
(`redis-cli ... INFO server | grep redis_version`, or `valkey-cli ...
valkey_version`) and move to Redis 7.x (redislabs PPA on Debian/Ubuntu) or
Valkey 8.x (AppStream on RHEL/Rocky). The role does this automatically; this is
mainly a concern on a hand-built backend.

**Job stuck in "queued"/"running" forever, but Slurm shows COMPLETED**
Pulsar submits the job and it finishes on Slurm, but completion never
propagates back to Galaxy. Cause: when Pulsar is installed via the
`pulsar-galaxy-lib` distribution, it bundles the Galaxy libraries
(galaxy-schema, galaxy-data, …). That makes `galaxy.model.Job` importable, so
the Slurm CLI plugin's `job_states` resolves to Galaxy's JobState enum
(`OK.value == "ok"`) instead of Pulsar's fallback enum (`OK == "complete"`).
The stateful manager compares against `status.COMPLETE == "complete"`, so
`"ok" != "complete"` and the job is never deactivated. Traced and reported in
galaxyproject/pulsar#460, where the maintainer landed a robust upstream fix
that determines the side explicitly rather than inferring it from what is
importable. A clean `pulsar-app` install hits the import fallback and never
sees the original symptom.

**`pulsar-relay authentication failed: 401`**
Pulsar's `message_queue_password` in `app.yml` does not match the relay's
`PULSAR_BOOTSTRAP_ADMIN_PASSWORD`. Re-sync and restart Pulsar.

**`RelayURLError: refusing plaintext http:// to non-localhost host`**
The relay client (0.2.x) refuses plaintext HTTP to a remote relay by default.
Set `PULSAR_RELAY_ALLOW_INSECURE=1` (the supervisord launcher does this) as a
stopgap, or serve the relay over HTTPS and drop the flag.

**`No such transport: http`**
The installed Pulsar version routes the relay URL through the AMQP/kombu path
(i.e. it predates relay support). Use a relay-capable Pulsar compatible with
the login node's Python; the known-good deployment is `0.15.15.dev0` /
`pulsar-app` on Python 3.11 with the standalone `pulsar-relay-client`.

**Jobs run on the login node**
Manager type is `queued_python` (or `job_plugin` is missing). Switch to
`queued_cli` + `job_plugin: Slurm` and restart.
