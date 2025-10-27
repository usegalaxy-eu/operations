# Compare VMs in 2+ clouds and HTCondor
Simply replace the Openstack credentials with yours, maybe change the sn09 hostname, voilà.
~~~
#!/bin/bash
date=$(date '+%Y-%m-%d')

ssh sn09 "condor_status --compact | grep vgcnbwc-worker | cut -d '.' -f1 > /tmp/$(date '+%Y-%m-%d')-condor"

scp sn09:/tmp/$date-condor /tmp/$date-condor

# replace with yours
source ~/app-cred-Mira-openrc.sh

openstack server list | grep vgcnbwc-worker > /tmp/$date-openstack-old

# replace with yours
source ~/app-cred-Mira-new-openrc.sh

openstack server list | grep vgcnbwc-worker > /tmp/$date-openstack-new
cat /tmp/$date-openstack-old /tmp/$date-openstack-new > /tmp/$date-openstack-all

echo "###################### By Names:"
comm -13 <(cat /tmp/$date-condor | sort -u) <(cat /tmp/$date-openstack-all | awk '{print $4}' | sort -u ) | tee /tmp/$date-missing

echo "###################### By IDs in OLD:"
cat /tmp/$date-openstack-old | grep -f /tmp/$date-missing | awk '{print $2}' | tee /tmp/$date-missing-ids

echo "###################### By IDs in NEW:"
cat /tmp/$date-openstack-new | grep -f /tmp/$date-missing | awk '{print $2}' | tee /tmp/$date-missing-ids
~~~
