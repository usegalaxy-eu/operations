# Job inspection commands

See [Job operations](../runbooks/jobs.md) and [Job failures and diagnosis](../troubleshooting/jobs.md).
### Jobs/tools running into a specific host/flavour

```bash
condor_q -autoformat ClusterID JobDescription RemoteHost | grep cn032
```


### condor_q is very powerful

```bash
condor_q  -constraint 'JobDescription == "spades"' -af ClusterID JobDescription RemoteHost RequestMemory MemoryUsage HoldReason
```
### List tools and requirements for idle jobs

```bash
condor_q -autoformat:t ClusterId JobDescription RequestMemory RequestCpus JobStatus | grep -P "\t1$"
```


### Number of cores available

```bash
condor_status -autoformat Name Cpus | cut -f2 -d' ' | paste -s -d'+' | bc
```


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
gxadmin query q "select job.id from job inner join job_state_history jh on job.id = jh.job_id where job.handler = 'handler_sn09_0' and job.tool_id != '__DATA_FETCH__' and ( job.update_time between timestamp '2023-12-14 11:00:00' and '2023-12-14 12:00:00' )" | awk '{print$1}' | sort | uniq -c | sort -sn
~~~

### Show all jobs from PXE test nodes
~~~
watch -d -n 3 "condor_q -run | grep privat | cut -d. -f1 | xargs -i sh -c 'gxadmin query queue-detail | grep {}'"
~~~

### Find Host from ClusterID
~~~
condor_q -af RemoteHost -constraint 'ClusterId == <job_id>'
~~~
