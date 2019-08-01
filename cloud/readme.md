---
title: Cloud Overview
---

- [services](./services.md)


There are two main groups of VMs:

## [vgcn-infrastructure](https://github.com/usegalaxy-eu/vgcn-infrastructure)

- repository for managing the VMs that Galaxy uses
- [runs on cron every hour](https://build.galaxyproject.eu/job/usegalaxy-eu/job/vgcn-infrastructure/)

## [infrastructure](https://github.com/usegalaxy-eu/infrastructure)

- repository for managing the other VMs, those not used by Galaxy
- [runs on git push + cron](https://build.galaxyproject.eu/job/usegalaxy-eu/job/infrastructure/)

