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

ClickHouse logs (via `journalctl -u clickhouse-server`) contain:

```
DB::Exception: Too many (N) broken parts in table plausible_events_db.events.
Limit is M. Change `max_suspicious_broken_parts` setting in order to allow loading it.
```

This can occur after a power loss or unclean shutdown where on-disk data structures were partially written.

**Mitigation**

```bash
# Step 1: Connect to the ClickHouse server
sudo -u clickhouse clickhouse-client

# Step 2: Raise the broken-parts threshold to allow the table to load
# (Replace 'plausible_events_db' and 'events' with the actual DB/table if different)
ALTER TABLE plausible_events_db.events
  MODIFY SETTING max_suspicious_broken_parts = 200;

# Exit the client
exit

# Step 3: Restart ClickHouse
sudo systemctl restart clickhouse-server
sudo systemctl status clickhouse-server
```

**Validation**

```bash
# Check for remaining errors
sudo journalctl -u clickhouse-server -n 100 --no-pager | grep -iE 'exception|error|warning'

# Verify the table is queryable
sudo -u clickhouse clickhouse-client --query \
  "SELECT count() FROM plausible_events_db.events"

# Check for detached/broken parts
sudo -u clickhouse clickhouse-client --query \
  "SELECT table, name, reason FROM system.detached_parts WHERE database = 'plausible_events_db'"
```

**Post-recovery cleanup**

Once ClickHouse has started successfully and the broken parts have been handled:

1. Drop detached parts that ClickHouse has quarantined (verify they are truly broken before dropping):

   ```bash
   sudo -u clickhouse clickhouse-client --query \
     "ALTER TABLE plausible_events_db.events DROP DETACHED PART '<part_name>'"
   ```

2. Reset `max_suspicious_broken_parts` to the default to avoid masking future corruption:

   ```bash
   sudo -u clickhouse clickhouse-client --query \
     "ALTER TABLE plausible_events_db.events
      RESET SETTING max_suspicious_broken_parts"
   ```

3. Restart ClickHouse to confirm the default limit is enforced cleanly:

   ```bash
   sudo systemctl restart clickhouse-server
   ```

### ClickHouse Fails to Start (General)

```bash
# Check the service status and recent log output
sudo systemctl status clickhouse-server
sudo journalctl -u clickhouse-server -n 200 --no-pager

# Check ClickHouse error log directly
sudo tail -n 200 /var/log/clickhouse-server/clickhouse-server.err.log
```

## Plausible Application Recovery

If ClickHouse is healthy but the Plausible web application is not responding:

```bash
# Check Plausible container / service status
# (Adjust to docker/docker-compose or systemd depending on deployment)
docker ps | grep plausible          # if deployed via Docker
systemctl status plausible          # if deployed as a systemd service

# Restart Plausible
docker restart plausible            # or:
systemctl restart plausible

# Check Plausible logs
docker logs plausible --tail 100    # or:
journalctl -u plausible -n 100 --no-pager
```

## Post-Outage Verification Checklist

- [ ] `clickhouse-server` is running: `systemctl status clickhouse-server`
- [ ] No `Too many broken parts` errors in the ClickHouse log
- [ ] `system.detached_parts` is empty (or only expected entries)
- [ ] `SELECT count() FROM plausible_events_db.events` returns a plausible number
- [ ] Plausible web UI is accessible and shows recent pageview data
- [ ] `max_suspicious_broken_parts` has been reset to the default after recovery

## Related Documentation

- [power-outage-recovery.md – ClickHouse/Plausible Recovery](./power-outage-recovery.md#g--clickhouseplausible-recovery)
- [monitoring.md](./monitoring.md) – general monitoring overview
