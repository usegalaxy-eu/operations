# Operations Manual for usegalaxy.eu

Welcome to the operations documentation for the European Galaxy server.

- The rendered site lives at <https://usegalaxy-eu.github.io/operations/>
- The former bwCloud documentation has been moved to [archived/cloud/](./archived/cloud/)

## Overview

- [Infrastructure](infrastructure/reference/bare_metal.md) — bare metal nodes, PXE/VGCN boot infrastructure, storage
- [KVM Infrastructure](miscellanea/kvm/README.md) — Terraform + libvirt service VMs, Galaxy Europe Services
- [Galaxy Admin](galaxy-admin/runbooks/admin_day_to_day.md) — day-to-day operations, runbooks, troubleshooting
- [HTCondor](htcondor/reference/wallclock-time-limit.md) — job management, GPU configuration
- [Databases](databases/influxdb.md) — InfluxDB and PostgreSQL
- [Knowledgebase](knowledgebase/conda_biocontainers_galaxy_how_they_are_connected.md)
- [Miscellanea](miscellanea/README.md) — scripts, telegraf configs, TSM, galaxy-storage
- [Archive](archived/kvm-server.md) — retired documentation (former cloud, KVM server, monitoring, process management)

## Working on the docs

```bash
pip install zensical
zensical serve          # live preview with search at http://localhost:8000
zensical build --strict # build check: fails on broken links and anchors (same check as CI)
```

CI validates every pull request with `zensical build --strict`, and pushes to `main` are deployed to GitHub Pages automatically.
