# Limiting the wall clock time for jobs

Jobs managed by our HTCondor instance are subject to a wall time restriction.
As of this writing, jobs will be automatically placed on hold after 30 days
and automatically removed 2 days later (unless an administrator intervenes
to "resurrect" the job).

This is accomplished by setting the following HTCondor macros:
```
# Job management
SYSTEM_PERIODIC_HOLD = \
  (JobStatus == 1 || JobStatus == 2) && \
  ((time() - JobStartDate) >= (2592000))
SYSTEM_PERIODIC_HOLD_REASON = \
  ifThenElse(((time() - JobStartDate) >= (2592000), \
             "Maximum wallclock time exceeded", \
                 "Unspecified reason")
SYSTEM_PERIODIC_REMOVE = \
  (JobStatus == 5 && time() - EnteredCurrentStatus > 172800)
```

(The relevant job status codes are 1:idle, 2:running, 5:hold,
times are in seconds.)

## CI Information

The HTCondor config file is templated from [condor_config.local.j2](https://github.com/usegalaxy-eu/infrastructure-playbook/blob/master/templates/htcondor/condor-config.local)

The relevant CI variables are

- `htcondor_system_periodic_hold`

- `htcondor_system_periodic_remove`

they are defined in [group_vars/htcondor/vars.yml](https:///usegalaxy-eu/infrastructure-playbook/blob/mast
er/group_vars/htcondor/vars.yml)

