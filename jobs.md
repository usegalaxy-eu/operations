### Move Condor Master to a new node / IP address

1. Update CNAME record for condor-cm.galaxyproject.eu so it points to your new Central Manager
2. Stop and disable `condor.service` on the old Central Manager host
3. Change lines in /etc/condor/condor_config.local on the new Central Manager like in https://github.com/usegalaxy-eu/infrastructure-playbook/pull/783/files
4. Check if new DNS record is returned on all workers with `pssh -h /etc/pssh/cloud -l centos -i 'nslookup condor-cm.galaxyproject.eu'`
5. If not, temporarily replace the nameserver in `/etc/resolv.conf` on all nodes to e.g. `1.1.1.1`
6. Restart `condor.service` on the new Central Manager
7. Update the Manager IP address on all workers with `pssh -h /etc/pssh/cloud -l centos -i 'condor_reconfig'`


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

### Get all errored jobs from a specific node (improve to grep more accurate time)

```bash
condor_history -af Cmd CompletionDate -startd -name c64m384g8-n3801.bi.privat | grep 1754 | cut -f1 -d' ' | xargs -i basename {}| awk 'match ($0,/[[:digit:]]+/) { print substr($0,RSTART,RLENGTH)}' | xargs -i gxadmin query job-info {} | grep error
```

### condor_q is very powerful

```bash
condor_q  -constraint 'JobDescription == "spades"' -af ClusterID JobDescription RemoteHost RequestMemory MemoryUsage HoldReason
```
### List tools and requirements for idle jobs

```bash
condor_q -autoformat:t ClusterId JobDescription RequestMemory RequestCpus JobStatus | grep -P "\t1$"
```

### Identify a mismatch between a job and a particular machine? (Why is my job not scheduled on this node?)
~~~
condor_q --better-analyze <job-id> -machine <machine-fqdn>
~~~

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
condor_off -peaceful -name vgcnbwc-worker-c125m425-8231.novalocal
```

To begin running or restarting all daemons (other than condor_master) given in the configuration variable DAEMON_LIST on the host:
```bash
condor_on vgcnbwc-worker-c125m425-8231.novalocal
```

Both commands can be executed from the submitter node.

#### Condor drain and condor off
Since we do not configure `MaxJobRetirementTime` in our condor setup, running `condor_drain` will kill the job immediately as the default value of `MaxJobRetirementTime` is 0.

Instead of `condor_drain`, we could use `condor_off -peaceful -name <worker node name>` and running this command will make the daemons wait for all jobs to finish while ensuring no new jobs are accepted.

**Some useful links:**
* https://www-auth.cs.wisc.edu/lists/htcondor-users/2021-July/msg00024.shtml
* https://htcondor.readthedocs.io/en/latest/man-pages/condor_drain.html
* https://htcondor.readthedocs.io/en/latest/man-pages/condor_off.html


### Raise awareness during Global Climate Strikes on Fridays by closing the job queue

[Fridays for Future](https://fridaysforfuture.org/) organizes Global Climate
Strikes that take place on specific Fridays to raise awareness of the grim
consequences of global warming.

Galaxy Europe
[has participated in such strikes in the past](https://galaxyproject.org/news/2023-09-11-climate-strike/),
by closing the job queue so that new jobs will not start until the strike is
over. The strike protocol is as follows:
- Write a blog post. You can reuse
  [past blog posts](https://github.com/galaxyproject/galaxy-hub/blob/ca8a80e38b62e36a518570f219624755fb9ba0ac/content/news/2023-09-11-climate-strike/index.md).
- Notify users in advance. In the past, this
  [has been done displaying banner on the main page](https://github.com/galaxyproject/galaxy-hub/blob/ca8a80e38b62e36a518570f219624755fb9ba0ac/content/bare/eu/usegalaxy/notices.md?plain=1#L1-L7).
- Enforce the strike using a TPV rule (read below).

We have written a TPV rule that takes advantage of
[HTCondor's job deferral feature](https://htcondor.readthedocs.io/en/latest/users-manual/time-scheduling-for-job-execution.html)
to enforce the strike. A copy of
[the rule](https://github.com/usegalaxy-eu/infrastructure-playbook/blob/e431458b17ef85162b9c6357810b2e1681774347/files/galaxy/tpv/tool_defaults.yml#L53-L75)
is available below.

```yaml
      - id: climate_strike
        # delay jobs using HTCondor's job deferral feature
        # https://htcondor.readthedocs.io/en/latest/users-manual/time-scheduling-for-job-execution.html
        if: True
        execute: |
          from datetime import datetime

          strike_start = datetime(2023,9,15,7,0)
          strike_end = datetime(2023,9,15,19,0)

          training_roles = (
              [r.name for r in user.all_roles()
               if not r.deleted and r.name in
               ("training-bma231-ht23", "training-msc-tmr-ws23",
                "training-bio00058m")]
              if user is not None else []
          )

          now = datetime.now()
          if strike_start <= now < strike_end and not training_roles:
              entity.params["deferral_time"] = f"{int(strike_end.timestamp())}"
              entity.params["deferral_prep_time"] = "60"
              entity.params["deferral_window"] = "864000"  # 10 days
```

Before merging the rule to
[tool_defaults.yml](https://github.com/usegalaxy-eu/infrastructure-playbook/blob/e431458b17ef85162b9c6357810b2e1681774347/files/galaxy/tpv/tool_defaults.yml)
(as a list item under the key
[`tools.default.rules`](https://github.com/usegalaxy-eu/infrastructure-playbook/blob/e431458b17ef85162b9c6357810b2e1681774347/files/galaxy/tpv/tool_defaults.yml#L23C8-L23C8)),
make sure to:
- Change the strike start and end time.
- Training roles are not always cleaned up after trainings are over. Thus, it
  is necessary to **modify the rule so that ongoing trainings are not
  affected**.
  - First, log-in to the
    [TIAAS admin panel](https://usegalaxy.eu/tiaas/admin/). The password, at the
    moment of writing this text, can be found
    [here](https://github.com/usegalaxy-eu/infrastructure-playbook/blob/e431458b17ef85162b9c6357810b2e1681774347/secret_group_vars/all.yml).
    If the password has changed, you will have to switch to the main branch of
    the repository.
  - After logging-in the
    [TIAAS calendar](https://usegalaxy.eu/tiaas/calendar/) will display the
    _"Event ID"_ under the _"Details"_ section on the right. Training role names
    are constructed adding the prefix `"training-"` to the Event ID.
  - Replace the role names already in the rule with the role names of the
    ongoing trainings.

After merging the rule, all jobs submitted during the strike will remain on
_"queued"_ state (gray) until the strike is over. Note that this TPV rule
only affects jobs running on HTCondor.

### Find jobs known to htcondor that are not known to Galaxy anymore

```bash
comm -23 <(condor_q --json | jq '.[]? | .ClusterId' | sort) <(gxadmin query queue-detail | awk '{print $5}' | sort)
```

Those ID can be piped to `condor_rm` if needed.

### Find finished jobs that galaxy does not update anymore
Introduced for https://github.com/usegalaxy-eu/issues/issues/865
~~~
comm -12 <(condor_history -af ClusterId | sort) <(gxadmin query queue-detail | awk 'NR > 2 { print $5 }' | sort)
~~~

### Concurrent Job Count Highscore
```bash
gxadmin query queue-detail --all | awk -F\| '{print$5}' | sort | uniq -c | sort -sn
```
Gives a list of all users that currently have jobs in the queue and how many (new, queued and running), in decending order.

### Show the job starting time human readable
```
condor_q -autoformat ClusterId Cmd JobDescription RemoteHost JobStartDate | awk '{ printf "%s %s %s %s %s\n", $1, $2, $3, $4, strftime("%Y-%m-%d %H:%M:%S", $5) }'
```
### Get the jobs that were updated frequently by a handler
Helped to solve
- https://github.com/usegalaxy-eu/issues/issues/504
~~~
gxadmin query q "select job.id from job inner join job_state_history jh on job.id = jh.job_id where job.handler = 'handler_sn06_0' and job.tool_id != '__DATA_FETCH__' and ( job.update_time between timestamp '2023-12-14 11:00:00' and '2023-12-14 12:00:00' )" | awk '{print$1}' | sort | uniq -c | sort -sn
~~~

### Show all jobs from PXE test nodes
~~~
watch -d -n 3 "condor_q -run | grep privat | cut -d. -f1 | xargs -i sh -c 'gxadmin query queue-detail | grep {}'"
~~~

### Find Host from ClusterID
~~~
condor_q -af RemoteHost -constraint 'ClusterId == <job_id>'
~~~
