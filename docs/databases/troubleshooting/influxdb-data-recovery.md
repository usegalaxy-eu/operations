# Re-filling InfluxDB tables after data loss

See the [InfluxDB overview](../influxdb.md) for networking and data acquisition.
For example `gxadmin meta slurp-upto` can be used to fill ceratain influx tables.
If we loose the influx DB and need to retrospectively fill the tables we can do for example this:
```bash
gxadmin meta slurp-initial 2014-01-01 2022-08-08 server-users.upto
```
This will fill the registered user table and dashboard.

