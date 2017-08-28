# Operations Manual for usegalaxy.eu

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
