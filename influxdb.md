# InfluxDB

## data aquisition

### telegraf

* telegraf is used to gather and push many system related information to influxdb
* gxadmin and telegraf can also be used together

### gxadmin

`gxadmin` has a mechanism called [`gxadmin meta influx-post`](https://galaxyproject.github.io/gxadmin/#/README.meta?id=meta-influx-post)
to directly push data

For example `gxadmin meta slurp-upto` can be used to fill ceratain influx tables.
If we loose the influx DB and need to retrospectively fill the tables we can do for example this:
```bash
gxadmin meta slurp-initial 2014-01-01 2022-08-08 server-users.upto
```
This will fill the registered user table and dashboard.

