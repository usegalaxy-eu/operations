# Roles
## that we carry around to fix or monitor things and that do not have an own repo/readme.md
### usegalaxy_eu.fs_maintenance
#### cron job cleanup-scrips submit to HTCondor (this one has a repo but no description)
This is scheduled as condor job, so I commented it for now, because we can also schedule this from sn06
and as soon as we have HTCondor on sn07 running we could uncomment it, because it will check the condor queue for running jobs before it reschedules them.
The other two cron jobs are a `docker purge` and `gxadmin cleanup` we most likely dont need docker anymore (also commented out) and can run `gxadmin cleanup` only on one node, because it will lead to conflicts otherwise.
### usegalaxy-eu.monitoring
#### NFS access time in cloud and nfsstat
This role adds a script to the telegraf exec plugin, which executes several pdsh commands to gather NFS access-time information from all worker nodes. It is basically a redundancy of usegalaxy-eu.montor-disk-access-time, which was merged to monitoring. The other part it does without pdsh is collecting the output from nfsstat commant and send it to influxDB
**This role can and should be moved to monitoring worker completely**

### usegalaxy-eu.rsync-to-nfs
Since we don't want to sync sn07 to NFS we don't need that role variable
### hxr.monitor-email
Watches the /var/spool/mail directory, because it got flooded by HTCondor and cron jobs a few times in the past.
### hxr.monitor-cluster
Sends the output of various `condor ... ` commands` to InfluxDB. Since we only have one HTCondor queue, we dont want to have this redundant, I guess? (also there is no HTCondor on sn07 so far)
### usegalaxy-eu.galaxy-slurp
The same idea: this is data from postgres, so we don't need to run this on both headnodes, it can be easily **moved to the maintenance worker node**
### usegalaxy-eu.htcondor_release
This should only run on one node to avoid strange behaviour. It could be migrated to maintenance, but needs condor or ssh to a headnode and then uses condor there, or run only on one headnode.
### usegalaxy-eu.unscheduled jobs/workflows
This was a fix for a galaxy bug that should be upstream now. However if we would need this, it needs to run on **both headnodes**, because it uses the handler logs to grep for 'failure running job'
### usegalaxy-eu.fix-ancient-ftp-data
This creates email-named folders to store ftp data and cleans up afterwards. I don't really now if we need this in the future.  
**Clear is that this should not run on more than one node.**
### usegalaxy-eu.galaxy-procstat
Gathers information about the `galaxy-xxxx@*.services` so it can run on **both headnodes**.  
Gunicorn will replace zergling in a later commit.
### usegalaxy-eu.fix-missing-api-keys
Creates API keys for all users automatically. This was once needed for the deprecated InteractiveEnvironments (now InteractiveTools). We can **remove this from both headnodes**
### usegalaxy-eu.fix-user-quotas
This executes a python script on cron to 'recalculate user disk quota', which should not be needed anymore and will be removed in a later commit.
The other thing it does, fixing ELIXIR quotas with a `gxadmin muate` command is stil needed and should be run only on one machine, **preferably the maintenance woker**
