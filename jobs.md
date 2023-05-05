
### Galaxy Job handling 

Reassign jobs from handler 11 to handler 3 with gxadmin:

```bash
gxadmin tsvquery queue-detail-by-handler handler_main_11  | cut -f1 | xargs -I{} -n1 gxadmin mutate reassign-job-to-handler {} handler_main_3 --commit

```
------

### Change job properties on the fly

condor_edit is your friend and the htcondor classads. Most commonly used ones are `RequestCpus`, `RequestMemory` (in MiB), `RequestGpus`, but a full list of all [Job ClassAd Attributes can be found in the htcondor docs.](https://htcondor.readthedocs.io/en/latest/classad-attributes/job-classad-attributes.html).

```bash
condor_qedit 37110378 RequestMemory=50000
```

-----

### Change htcondor labels on-the-fly:

```bash
sed -i 's/"compute"/"dockerhack"/g' /etc/condor/condor_config.local; systemctl reload condor
```

Test with:

```bash
condor_status -autoformat Machine GalaxyGroup GalaxyDockerHack | grep hack | sort -u
```

-----

### fail all jobs of a particular user using gxadmin

The following command is failing all jobs of the service-account user.

```bash
gxadmin tsvquery jobs --user=service-account --nonterminal | awk '{print $1}' |  xargs -I {} -n 1 gxadmin mutate fail-job {} --commit 
```

### fail all jobs on the nodes, in cases when condor_rm does not do the job

This cmd will find all jobs matching a string (here "obabel"), returns the group-pid and kills those group process. This seems to be the only way
to remove jobs from the condor nodes when condor_rm was not able to kill the jobs.

```bash
pdsh -g cloud 'ps xao pgid,cmd | grep "[o]babel" | awk "{ print \$1 }" | xargs -I {} sudo kill -9 {}'
```

-----
### Jobs/tools running into a specific host/flavour

```bash
condor_q -autoformat ClusterID JobDescription RemoteHost | grep cn032
```

### cndor_q is very powerful

```bash
condor_q  -constraint 'JobDescription == "spades"' -af ClusterID JobDescription RemoteHost RequestMemory MemoryUsage HoldReason
```

### Number of cores available

```bash
condor_status -autoformat Name Cpus | cut -f2 -d' ' | paste -s -d'+' | bc
```

### Debugging of a Condor job that was giving back an empty file as result
As input we had a galaxy job id `11ac61790d0cc33b8086442012d093zu (11384941)` and a note of an empty file as result. The job was a step of a big collection where the other steps were successful.

To understand the reason for the problem, I proceeded as follows:

```bash
condor_history | grep 11384941
```
to retrieve the condor id

```bash
condor_history -l 6545461
```
to retrieve all the job detail, and here, I found this error message:  
`"Error from slot1_1@cn030.bi.uni-freiburg.de: Failed to open '/data/dnb03/galaxy_db/job_working_directory/011/384/11384941/galaxy_11384941.o' as standard output: No such file or directory (errno 2)"`

A quick check into the compute node
```[root@cn030 ~]# cd /data/dnb03
-bash: cd: /data/dnb03: No such file or directory
```
showed it was not mounting properly the NFS export.

### Reserve an handler for a tool and move all running jobs to it

Add a new handler to the `job_conf.xml`

```xml
	<handlers assign_with="db-skip-locked" max_grab="8">
		<handler id="handler_key_0"/>
		<handler id="handler_key_1"/>
		<handler id="handler_key_2"/>
		<handler id="handler_key_3"/>
		<handler id="handler_key_4"/>
		<handler id="handler_key_5"/>
		<handler id="handler_key_6" tags="special_handlers"/>
	</handlers>
```
associate the tool to that handler

```xml
	<tools>
		<tool id="upload1" destination="gateway_singlerun" />
		<tool id="toolshed.g2.bx.psu.edu/repos/chemteam/gmx_sim/gmx_sim/2020.4+galaxy0" destination="gateway_singlerun" resources="usegpu" />
		<tool id="toolshed.g2.bx.psu.edu/repos/chemteam/gmx_sim/gmx_sim/2019.1.5.1" destination="gateway_singlerun" resources="usegpu" />
		<tool id="gmx_sim" destination="gateway_singlerun" resources="usegpu" />
		<tool id="param_value_from_file" handler="special_handlers" />
```
restart workflow schedulers
and
move all running jobs to the new handler

```bash
for j in `gxadmin query queue-detail --all| grep param_value_from_file |grep -v handler_key_6 | cut -f2 -d'|' | paste -s -d ' '`; do gxadmin mutate reassign-job-to-handler $j handler_key_6 --commit;done
```

### How to shut down/start up a single execute node without killing jobs

This “peaceful” shutdown of a startd will cause that daemon to wait indefinitely for all existing jobs to exit before shutting down. During this time, no new jobs will start.
```bash
condor_off -peaceful -startd vgcnbwc-worker-c125m425-8231.novalocal
```

To begin running or restarting all daemons (other than condor_master) given in the configuration variable DAEMON_LIST on the host:
```bash
condor_on vgcnbwc-worker-c125m425-8231.novalocal
```

Both commands can be executed from the submitter node.

### How to raise awareness for Climate Stike Fridays by closing the queue
Do these steps for every training that should run on that Friday.
- for every training put an equal share of all non-training worker vms into a `mytraining1.txt` hostfile
- on Thursday evening, or Friday morning run `pssh -h mytraining1.txt -l centos 'sudo sed -i '"'"'s/"compute"/"<training-tag>"/g'"'"' /etc/condor/condor_config.local; sudo sed -i '"'"'s/GalaxyTraining = false/GalaxyTraining = true/g'"'"' /etc/condor/condor_config.local; sudo systemctl reload condor'`
- TEST and make sure that training still works by running `condor_status | grep training` (and perhaps submit a job while having the training role)
- on Friday evening run `pssh -h mytraining1.txt -l centos 'sudo sed -i '"'"'s/"<training-tag>"/"compute"/g'"'"' /etc/condor/condor_config.local; sudo sed -i '"'"'s/GalaxyTraining = true/GalaxyTraining = false/g'"'"' /etc/condor/condor_config.local; sudo systemctl reload condor'`

### Find jobs known to htcondor that are not known to Galaxy anymore

```bash
comm -23 <(condor_q --json | jq '.[]? | .ClusterId' | sort) <(gxadmin query queue-detail | awk '{print $5}' | sort) 
```

Those ID can be piped to `condor_rm` if needed.

### Concurrent Job Count Highscore
```bash
gxadmin query queue-detail --all | awk -F\| '{print$5}' | sort | uniq -c | sort -sn
```
Gives a list of all users that currently have jobs in the queue and how many (new, queued and running), in decending order.

### Show the job starting time human readable
```
condor_q -autoformat ClusterId Cmd JobDescription RemoteHost JobStartDate | awk '{ printf "%s %s %s %s %s\n", $1, $2, $3, $4, strftime("%Y-%m-%d %H:%M:%S", $5) }'
```
