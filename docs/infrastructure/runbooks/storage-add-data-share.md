# Steps to add a new data (_dnbXX_) share
1. Request the storage team (RZ) for a new data share (_dnbXX_)
2. Once the new mount point is made available, mount it and test if the new mount point actually works and is reachable (pick a worker node and try it).
3. The following places must be updated to roll out the new data share and to migrate from the previous share
   1. Add the new mount point to the [mounts repository](https://github.com/usegalaxy-eu/mounts). An example PR can be found [here](https://github.com/usegalaxy-eu/mounts/pull/4)
   2. Update the currently running `vgcnbwc-worker-*` nodes with the new mount using `pssh`.
      ``` bash
      pssh -h /etc/pssh/cloud -l centos -i 'sudo su -c "echo \"dnb09    -rw,hard,nosuid,nconnect=2      denbi.svm.bwsfs.uni-freiburg.de:/dnb09\" >> /etc/auto.data"'
      ````
   3. Verify that the mount is successful
      ```bash
      pssh -h /etc/pssh/cloud -l centos -i 'ls -l /data/dnb09/'
      ```
   4. Then, update the `object_store_conf.xml`, for example like [see here](https://github.com/usegalaxy-eu/infrastructure-playbook/pull/800)
   5. Once everything is merged, run the Jenkins job (`sn09` playbook project) to deploy the new data share
   6. Monitor the changes and the handler logs to make sure that there are no errors.

