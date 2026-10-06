# Job failures and diagnosis

See [Job operations](../runbooks/jobs.md) and [Job inspection commands](../reference/jobs-queries.md).
### fail all jobs of a particular user using gxadmin

The following command is failing all jobs of the service-account user.

```bash
gxadmin tsvquery jobs --user=service-account --nonterminal | awk '{print $1}' |  xargs -I {} -n 1 gxadmin mutate fail-job {} --commit
```

### fail all jobs on the nodes, in cases when condor_rm does not do the job

This cmd will find all jobs matching a string (here "obabel"), returns the group-pid and kills those group process. This seems to be the only way
to remove jobs from the condor nodes when condor_rm was not able to kill the jobs.

```bash
pssh -g cloud 'ps xao pgid,cmd | grep "[o]babel" | awk "{ print \$1 }" | xargs -I {} sudo kill -9 {}'
```

-----

### Get all errored jobs from a specific node (improve to grep more accurate time)

```bash
condor_history -af Cmd CompletionDate -startd -name c64m384g8-n3801.bi.privat | grep 1754 | cut -f1 -d' ' | xargs -i basename {}| awk 'match ($0,/[[:digit:]]+/) { print substr($0,RSTART,RLENGTH)}' | xargs -i gxadmin query job-info {} | grep error
```


### Identify a mismatch between a job and a particular machine? (Why is my job not scheduled on this node?)
~~~
condor_q --better-analyze <job-id> -machine <machine-fqdn>
~~~


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

