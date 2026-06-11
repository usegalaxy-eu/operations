# NEMO Pulsar (Relay Mode)

This document describes how usegalaxy.eu dispatches jobs to the **bwForCluster
NEMO** (University of Freiburg HPC) using **Pulsar in relay mode**, and how to
operate and maintain that setup.

Unlike the other remote Pulsar endpoints (which connect over RabbitMQ/AMQP via
`mq.galaxyproject.eu`), NEMO uses the experimental **pulsar-relay**: a small
HTTP service that brokers messages between Galaxy and Pulsar by long-polling,
so no inbound ports or AMQP broker are required on the HPC side.

## Architecture

- **Galaxy** routes selected jobs to the `pulsar_eu_nemo`
  runner. The runner speaks to the relay over HTTPS using credentials stored
  in the vault.
- **Relay** is a stateless-ish HTTP broker running on a bw-cloud VM. It holds
  pending messages in **Valkey** (Redis-compatible) so an in-flight job is not
  lost across a relay restart.
- **Pulsar** runs on a NEMO login node. It long-polls the relay for new job
  setup / status / kill messages, submits the actual work to **Slurm**, and
  publishes status updates back to the relay.
- Tool dependencies are resolved as **Singularity/Apptainer** containers pulled
  from **CVMFS** (`/cvmfs/singularity.galaxyproject.org/all/`).

## Components and where they live

| Component | Host | Notes |
|-----------|------|-------|
| Galaxy runner `pulsar_eu_nemo` | usegalaxy.eu | Defined in `infrastructure-playbook` `job_conf.yml`; creds from vault |
| TPV destination `pulsar_nemo_tpv` | usegalaxy.eu | Defined in `infrastructure-playbook` `tpv/destinations.yml.j2`; tag `nemo-pulsar` |
| pulsar-relay | bw-cloud VM | systemd service `pulsar-relay`, listens on `:9000`, Valkey backend |
| Pulsar | NEMO login node | started via wrapper script; submits to Slurm |

## Routing a job to NEMO

The TPV destination `pulsar_nemo_tpv` requires the scheduling tag
`nemo-pulsar`. A job will only be sent to NEMO if it carries that tag. Two ways
this happens today:

1. **User-level opt-in**, a user selects the NEMO compute resource in
   *User → Preferences → Manage Information → Use distributed compute
   resources* ("Freiburg (Germany) - bwForCluster NEMO 2").
2. **Per-user TPV rule**, an entry in `tpv/users.yml` that attaches the
   `nemo-pulsar` requirement for a given user/tool (used for testing).

If a job is not tagged, it runs on the default destination as usual.

## Relay service (bw-cloud)

The relay is a systemd unit. Key environment variables (set in
`/etc/systemd/system/pulsar-relay.service`):

```ini
Environment="PULSAR_STORAGE_BACKEND=valkey"
Environment="PULSAR_VALKEY_HOST=localhost"
Environment="PULSAR_VALKEY_PORT=6379"
Environment="PULSAR_BOOTSTRAP_ADMIN_USERNAME=admin"
Environment="PULSAR_BOOTSTRAP_ADMIN_PASSWORD=<in vault>"
Environment="PULSAR_JWT_SECRET_KEY=<in vault>"
```

Valkey is installed via snap and runs as its own service. Because storage is
persisted to Valkey, the admin user and any in-flight messages survive a relay
restart.

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

# confirm Valkey is up
valkey.cli ping   # -> PONG
```

## Pulsar (NEMO login node)

NEMO does not provide user-level systemd, so Pulsar is kept alive by a small
wrapper script that restarts it if it exits. Pulsar configuration lives in
`~/pulsar/config/app.yml`:

```yaml
log_level: INFO
job_metrics_config_file: job_metrics_conf.xml
message_queue_url: http://<relay-host>:9000/
message_queue_username: admin
message_queue_password: <in vault>
staging_directory: /home/.../pulsar/jobs_directory

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
  submitted to Slurm, this is not allowed and will get the account flagged by
  the RZ admins.
- `job_metrics_conf.xml` enables the `core`, `cgroup` and `hostname` metrics
  plugins so the compute hostname and resource usage show up in Galaxy.

Useful operations:

```bash
# is Pulsar running?
ps aux | grep pulsar-main | grep -v grep

# tail the log
tail -f ~/pulsar/pulsar.log

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
   `/messages/poll` and the Galaxy side polling `/messages/poll` for
   `job_status_update`.
4. The job should reach **ok** in the Galaxy UI, and the job metrics should
   list the Singularity container ID pulled from CVMFS.

## Troubleshooting

**Job stuck in "queued"/"running" forever, but Slurm shows COMPLETED**
Pulsar is submitting and the job finishes, but completion is not propagating
back. Confirm the Slurm CLI status plugin maps the "job no longer in squeue"
case to `complete`. (This was a real bug when Galaxy is importable in the same
venv as Pulsar: the CLI plugin returned `job_states.OK` which resolves to
Galaxy's `"ok"` rather than Pulsar's `"complete"`, so the stateful manager
never deactivated the job. Fixed upstream in galaxyproject/pulsar.)

**`pulsar-relay authentication failed: 401`**
Pulsar's `message_queue_password` in `app.yml` does not match the relay's
`PULSAR_BOOTSTRAP_ADMIN_PASSWORD`. Re-sync and restart Pulsar.

**`No such transport: http`**
The installed Pulsar version is routing the relay URL through the AMQP/kombu
path. Use a Pulsar build with relay support that is compatible with the NEMO
Python version.

**Jobs run on the login node**
Manager type is `queued_python` (or `job_plugin` is missing). Switch to
`queued_cli` + `job_plugin: Slurm` and restart.
