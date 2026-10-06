# InfluxDB

See [Re-filling InfluxDB tables after data loss](troubleshooting/influxdb-data-recovery.md) for recovery operations.
## Networking
Influxdb is now behind a reverse proxy (traefik). The DNS record `influxdb.galaxyproject.eu` points to this proxy.
To reach the actual service VM, use `influxdb.bi.privat`.

## data aquisition

### telegraf

* telegraf is used to gather and push many system related information to influxdb
* gxadmin and telegraf can also be used together

### gxadmin

`gxadmin` has a mechanism called [`gxadmin meta influx-post`](https://galaxyproject.github.io/gxadmin/#/README.meta?id=meta-influx-post)
to directly push data

