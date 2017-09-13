# Operations Manual for usegalaxy.eu

## Adjusting a Tool's Requirements

1. Edit https://github.com/usegalaxy-eu/galaxy-playbook-temporary/blob/master/roles/galaxy_config/templates/job_conf.xml
2. Mirror changes to https://github.com/usegalaxy-eu/galaxy-playbook-temporary/blob/master/roles/galaxy_config/templates/job_conf.py)
3. Wait until the end of the hour, at which the playbook will run. You should be able to confirm this via [grafana](https://grafana.denbi.uni-freiburg.de/dashboard/db/galaxy?refresh=1m&panelId=39&fullscreen&orgId=1)

[An example PR](https://github.com/usegalaxy-eu/galaxy-playbook-temporary/pull/3/files)


## Restarting Galaxy

If you're doing a full restart of the server, use `supervisorctl restart all`
followed by `supervisorctl stop gx:zergling1` as supervisor restart restarts
too much.

Restarting handlers can be done via `supervisorctl restart hd:`, in case
changes are made to job scheduling.

However if you just want to swap the zerglings in use (e.g. for a newly
installed set of tools), then you must use `~/galaxy-dist/restart.sh` which
includes special logic for waiting until the new zergling is alive and then
stopping the old one, because they don't do the magic turning of the other one
off that is described in the galaxy training.

## InfluxDB Events

For administration tasks, sending events to influxdb is a good way to note any potential impacts your actions had on the server. Here's an example bash function:

```bash
function influxdb_event(){
	q=`date +%s`000000000;
	title=$1;
	desc=$2;
	tags=$3;
	curl -i \
		-XPOST \
		'http://influxdb.denbi.uni-freiburg.de:8086/write?db=rancher' \
		--data-binary "events,dc=rz value=\"$title\",description=\"$desc\",tags=\"$tags\" $q";
}

influxdb_event "testing some events" "with <b>description</b>" "galaxy,testing"
```

These functions are easy to insert anywhere and everywhere and let us make
notes on Grafana about these events. When trying to correlate things like "I
replaced the XML parsing in this service and restarted galaxy" annotated events
can be helpful in seeing the effects downstream.

![](./images/events.png)
