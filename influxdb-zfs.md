# InfluxDB: ZFS Instrumentation


## ZFS Monitoring with Telegraf

Telegraf (unit `telegraf.service`) is used for data acquisition and
transfer to InfluxDB.

For monitoring our ZFS servers a custom monitoring script has been
written, that collects basic status and performance data and transmits
it via the InfluxDB line protocol.


### Line Protocol

At this writing the script `/opt/sbin/zfsstat-influx` is run once per
minute by telegraf. Sample output:

```
zfs,scope=zpool,fset=io,vers=1,ds=zp0 rops=0,wops=670,rbw=0,wbw=53698362
zfs,scope=zpool,fset=space,vers=1,ds=zp0 alloc=7725047697408,free=328278833803264,frag=35,cap=2
zfs,scope=dataset,fset=space,vers=1,ds=zp0 used=24412936676826,avail=214310606658086,compr=1.33
zfs,scope=dataset,fset=space,vers=1,ds=zp0/bcache-zvol used=18920917148922,avail=233231523684704,compr=1.00
zfs,scope=dataset,fset=space,vers=1,ds=zp0/jwd01 used=5464647578208,avail=214310606658086,compr=1.33
zfs,scope=dataset,fset=space,vers=1,ds=zp0/speedtest used=209664,avail=214310606658086,compr=1.00
zfs,scope=dataset,fset=space,vers=1,ds=zp0/upload01 used=209664,avail=214310606658086,compr=1.00
```

#### The meaning of the tags is as follows:

- `scope`: which type of entity was sampled (currently `zpool` or `dataset`)

- `fset`: a name for the field set (currently `io` or `space`):
  - `io`: I/O performance data
  - `space`: data block usage statistics

- `vers`: a version number for the fset format (to be incremented
  whenever the field set layout for a given scope changes)

- `ds`: the entity that was sampled (dataset or zpool name)


#### Observation data:

- The data of the first field group(s) (`rops`, `wops`, `rbw`, `wbw`)
  comes from the command `zpool iostat` corresponding to the columns
  "operations read/write" and "bandwidth read/write", the units are
  ops/s and bytes/s, respectively. This performance data is currently
  a 5 second snapshot; the sample interval for `zpool iostat` could be
  extended if desired, however, in this case the timeout defined in
  the telegraf config file needs to be changed to match.

  There is one `scope=zpool,fset=io` field group for each active zpool
  found on the system.

- The next field group(s) (`alloc`, `free`, `frag`, `cap`) report
  block usage at the zpool level. The data comes from the command
  `zpool list` and corresponds to the columns "alloc", "free", "frag"
  and "cap". The units are bytes (alloc, free) and percentage
  (fragmentation, pool capacity).

  There is one `scope=zpool,fset=space` field group for each active
  zpool found on the system.

- The remaining field groups (`used`, `avail`, `compr`) report block
  usage at the dataset ("filesystem") level . The data comes from the
  command `zfs get` and reports the ZFS properties "used", "avail"
  (bytes) and "compressratio" (ratio as floating point).

  There is one `scope=dataset,fset=space` field group for every
  dataset or zvol (including the zpool's root data set) found in any
  of the active zpools on the system.



