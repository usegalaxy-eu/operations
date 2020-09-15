
### Galaxy Job handling 

Reassign jobs from handler 11 to handler 3 with gxadmin:

```bash
gxadmin tsvquery queue-detail-by-handler handler_main_11  | cut -f1 | xargs -I{} -n1 gxadmin mutate reassign-job-to-handler {} handler_main_3 --commit

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
gxadmin query queue-details | grep  service-account | awk '{print $3}' |  xargs -I {} sh -c "gxadmin mutate fail-job {} --commit"
```

-----
### Jobs running into a specific host

```bash
condor_q -autoformat ClusterID JobDescription RemoteHost | grep cn032
```

### Number of cores available

```bash
condor_status -autoformat Name Cpus | cut -f2 -d' ' | paste -s -d'+' | bc
```

### Debugging of a Condor job that was giving back an empty file as result
As input we had a galaxy job id `11ac94870d0bb33a8013642012e063ec (11384941)` and a note of an empty file as result. The job was a step of a big collection where the other steps were successful.

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



