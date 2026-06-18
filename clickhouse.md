---
title: ClickHouse and Plausible Analytics
---

# ClickHouse and Plausible Analytics

[Plausible](https://plausible.io/) is our privacy-friendly web analytics service.  It uses
**ClickHouse** as its OLAP database backend.  This document covers operational notes and recovery
procedures.

## Service Location

- Plausible web UI: <https://plausible.galaxyproject.eu> (or configured domain)
- ClickHouse listens on `localhost:9000` (native protocol) and `localhost:8123` (HTTP)
- Managed via [infrastructure-playbook](https://github.com/usegalaxy-eu/infrastructure-playbook)

## Common Issues

### Broken Parts After Crash / Unclean Shutdown

**Symptom**

ClickHouse logs contain:

```
DB::Exception: Too many (N) broken parts in table plausible_events_db.events.
Limit is M. Change `max_suspicious_broken_parts` setting in order to allow loading it.
```

This can occur after a power loss or unclean shutdown where on-disk data structures were partially written.

**Mitigation**

if ClickHouse is not alive with Suspiciously many (14 parts) broken parts to remove while maximum allowed broken parts count is 10 then you can change the ```/data/plausible/clickhouse/clickhouse-config.xml``` and add:
```
    <merge_tree>
        <max_suspicious_broken_parts>50</max_suspicious_broken_parts>
    </merge_tree>
```
