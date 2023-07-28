This document is a guide to the day-to-day operations of the admin team.

## Daily monitoring:
1. Grafana dashboards
	1. [Node details](https://stats.galaxyproject.eu/d/000000023/node-detail-infrastructure?orgId=1)
        * This dashboard gives you an overview of all the nodes (headnode, worker nodes, etc.)
	2. [Storage (ZFS server)](https://stats.galaxyproject.eu/d/IUk_uK04z/zfs?orgId=1)
        * This dashboard gives you an overview of the ZFS storage server, its load, performance, availability, etc.
	3. [VGCN monitoring](https://stats.galaxyproject.eu/d/Zn2z0NYVk/vgcn-monitoring?orgId=1)
        * This dashboard gives your information related to the worker nodes. Helps to find the worker nodes that are not connected to HTCondor anymore but are still in the BWCloud. Helps to determine the worker nodes in the stuck state. In such cases have a look at the remote logs (`/var/log/remote/<worker_node_name_here>/`) of the worker nodes available on the maintenance server (`maintenance.galaxyproject.eu`).
	4. [CVMFS](https://stats.galaxyproject.eu/d/XtcPRpImz/cvmfs-stratum-1-server-status?orgId=1)
        * This dashboard gives you an overview of the CVMFS stratum 1 availability and the repo availability.
    5. [Galaxy](https://stats.galaxyproject.eu/d/000000004)
        * This dashboard gives you an overview of condor job states and which tools are currently used
    6. [Jobs-Dashboard](https://stats.galaxyproject.eu/d/000000034)
        * shows not the Condor job status, but Galaxy's job status
    7. [Alerts](https://stats.galaxyproject.eu/d/000000052/alerts?orgId=1)
    8. _NOTE: There is a new WIP [dashboard](https://stats.galaxyproject.eu/d/ZmZaLfz4k/day-to-day?orgId=1&refresh=30s) that groups and summarizes information_
2. Sentry: Check for [new issues](https://sentry.galaxyproject.org/organizations/galaxy/issues/?project=7&statsPeriod=24h)
3. Rabbitmq: [Dashboard](https://mq.galaxyproject.eu/) (Check for connection errors, have a look at the queue)
4. Celery Flower: [Dashboard](http://100.118.169.22:5555/dashboard) (Check if workers are offline and the number of failing tasks is increasing, check recent failed tasks in this case)
    * To connect:
        1. Install tailscale client,
        2. Login using GitHub creds,
        3. Select usegalaxy-eu organization (you need to be a member of [usegalaxy-eu/admin](https://github.com/orgs/usegalaxy-eu/teams/admin))
5. On headnode:
    1. Check server load: `top`, `htop`, in `top` especially the `wa` (waiting for I/O) value might be interesting. It should not exceed `8.0` and can indicate a storage problem or handler misconfiguration.
	2. Check storage availability of: JWD's, root partition, etc. (only if not available in Grafana or further investigation is needed)
	3. Check the idle, running, held jobs in condor queue: `condor_q`
        * If jobs are in held state then investigate those jobs and try to release them.
            1. To get the list of jobs in held state and the reason: `condor_q -hold`
                * If you see the reason as `SYSTEM_PERIODIC_HOLD` then it means that the job is held because of the periodic hold policy. This policy is set to hold the jobs which are in the queue or was running for more than `2592000` seconds (720 hrs).
                * In such cases have a look at the job details (use `gxadmin` queries), who submitted it, what tool it is and if you know that this tool does not take that long then it means something is wrong. So try and investigate it or simply release the job by running `condor_release <job_id>` and monitor the job for a while.
            2. You can better analyze the job: `condor_q --better-analyze <job_id>`
            3. To release the job: `condor_release <job_id>`
        * If many jobs are in the `idle` state then it means the cluster is under heavy load
            1. Check if there are any `Unclaimed/Idle` slots available: `condor_status --compact | (head -n 2; grep Ui)`
            2. Check VGCN monitoring dashboard for any issues related to the availability of the worker nodes: [Dashboard](https://stats.galaxyproject.eu/d/Zn2z0NYVk/vgcn-monitoring?orgId=1)
            3. Get more information about the idle jobs: `condor_q -autoformat:t ClusterId JobDescription RequestMemory RequestCpus JobStatus | grep -P "\t1$"`
            4. Have a brief look at the better analysis of the jobs: `condor_q --better-analyze <job_id>` and check the resource requirements of the job.
            5. By fixing any issues with the availability of the worker nodes usually fixes the issue.
	4. Gxadmin count of new, queue, running jobs: `gxadmin tsvquery queue-detail --all | awk '{print $1}' | sort | uniq -c`
    5. Watch the new and queue jobs to find if they are getting picked up by the handlers and getting the condor job ids:
        1. `watchendnew`: It's an alias, watches the end of the new queue. This helps to find whether the jobs are getting picked up by the handlers or not.
        2. `watchendqueue`: It's an alias, watches the end of the queue. This helps to find whether the jobs are getting assigned the condor id's or not.
        3. `highscore`: It's an alias, shows the number of jobs submitted by each user.
    6. Check handler logs: `glh` or `journalctl -fu galaxy-handler@<handler_number_here>` and glg or `journalctl -fu galaxy-gunicorn@<handler_number_here>`
    7. Check when was the last time the web handlers wrote some logs: `gxadmin gunicorn lastlog` (should be as recent as possible, if not it means web handlers have some issues)

## Day-to-day user requests:
1. Internal user (Freiburg) requests
2. External user requests (pinged on Gitter channels or direct messages)
3. Pull requests in various repositories and [Issues](https://github.com/usegalaxy-eu/issues/issues)
4. Requests for TIaaS
5. Requests for quota increase

## Projects:
* Projects are converted to tasks and priorities are defined for each task and documented here: [Projects](https://github.com/orgs/usegalaxy-eu/projects/2)
* Projects typically belong to the following:
    1. Quality of Life projects
    2. New feature projects
    3. Infrastructure improvement projects
    4. Documentation improvement projects
    5. Projects related to the maintenance, updates, migration, monitoring, testing.
