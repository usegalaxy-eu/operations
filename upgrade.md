---
title: Galaxy Upgrading procedures
---


# 7 days before downtime

- Write an announcement about the potential Galaxy downtime explaining that Galaxy is being upgraded. Be sure to link to the release announcement,  see https://github.com/usegalaxy-eu/website/blob/master/_data/notices.yml

# a few days before downtime

## update web-hooks repo

1. update our [webhooks repository](https://github.com/usegalaxy-eu/galaxy-webhooks) with the latest changes from [upstream Galaxy](https://github.com/galaxyproject/galaxy/tree/dev/config/plugins/webhooks)

## create a new Galaxy deployment branch

1. Clone [our fork](https://github.com/usegalaxy-eu/galaxy/).
2. Check out the release branch you want to switch to, e.g. `release_XX.ZZ`
3. Ensure it's updated: `git pull`
4. Checkout *our* previous release branch (`release_XX.YY`)
5. `git rebase -i release_XX.ZZ` to rebase our commits on top of the new release branch
   * try hard to get as many commits upstream, aim is to not carry around any commit  
6. Update [`infrastructure-playbook`](https://github.com/usegalaxy-eu/infrastructure-playbook/) to:
 * sync configuration files, see https://github.com/usegalaxy-eu/infrastructure-playbook/blob/master/bin/diff-before-update
 * update to the latest commit ID of the new branch, see https://github.com/usegalaxy-eu/infrastructure-playbook/blob/341d1e41c519f400b24f58d01aa356d3fe961fe8/group_vars/sn06.yml#L538


# Downtime begins

- (optionally) update conda with

```bash
galaxy@sn06:~$ export PATH=/usr/local/tools/_conda/bin/:$PATH
galaxy@sn06:~$ which conda
/usr/local/tools/_conda/bin/conda
galaxy@sn06:~$ conda update -n base -c conda-forge conda
```

- Run playbook (maybe with `make main.eu CHECK=1` to be certain of your changes.)
- Add a blog post about this (an [example](https://github.com/usegalaxy-eu/galaxy-freiburg/pull/82))


# Jenkins

I would recommend to read [the official backup guide](https://www.jenkins.io/doc/book/system-administration/backing-up/) first.  

Announcing the downtime is always important, as well as scheduling preferrably a date in the morning in the compute center for the maintenance. (If you come in the afternoon and something goes wrong it can happen that the room is locked down before you are done.)

Updating Jenkins is generally not difficult, because the whole service is file-based and all relevant files live in the `$JENKINS_HOME` directory. This is defined [here](https://github.com/usegalaxy-eu/infrastructure-playbook/blob/25ddd20a643c33234712ae40641cc29b0fab731d/group_vars/build.yml#L3). This directory lives in a separate Logical Volume and can be backed up easily by shutting Jenkins down and creating a snapshot. After the Upgrade / OS re-installation is done, it can be rsynced / remounted and the build playbook can be run.  

## Graceful Shutdown

In order to stop Jenkins gracefully, you can [prepare for Shutdown](https://build.galaxyproject.eu/manage/prepareShutdown) which gives you also the option to communicate the reason to your users. This will not shut down Jenkins, but it will not run any new jobs. Once all jobs have ended, you can send a POST request to `https://build.galaxyproject.eu/exit` which will shut down Jenkins (if you are logged in as admin, of course).  

## Backup
Now you can check `journalctl` and make sure it has fully stopped. To create a LV snapshot, you can use the following commands:
~~~sh
# mount NFS if not happened
mount -t nfs ufr-dyn.isi1.public.ads.uni-freiburg.de:/ifs/isi1/ufr/bronze/nfs/denbi/ /data/dnb01
# Create the snapshot
lvcreate -L50G -s -n <snapshot-name> <jenkins-home-dir-LV-name> # e.g. /dev/rl/jenkins-home
# Create a disk image and save it to NFS
dd if=/dev/<vg-name>/<snapshot-name> of=/data/dnb01/jenkins-backup/<backup-image-name>.dd
~~~
If you want to feel extra-safe, you can also create a FS-dump and also test if you can mount the back-up image with
~~~sh
mount -o loop /data/dnb01/jenkins-backup/<backup-image-name>.dd /opt
~~~
Ideally you should now even be able to start Jenkins again. Otherwise just check the files are there.

## Installation
Everything else is created by the playbook (yes, really, I tested it!)  
So you could even build a whole new disk in and install your new OS.
While installing the OS, do not forget to create the correct VLAN interface (VLAN ID is 223), give it the static IPv4, that is also in the DNS record for `build.galaxyproject.eu` and remove/disable all other IP addresses.  

## Restore
Once your installation is done, you can restore the home directory.
1. Create a LV for the `$JENKINS_HOME`, create a FS for it, mount it.
2. Mount in the backup image as described in the Backup step.
3. rsync the whole directory from the mounted backup image to the LV
4. unmount the backup image

## Playbooks
Now it gets interesting: Last step is to run the playbooks and see if everything worked as expected.
NOTICE: It is quite normal for playbooks to fail after installing newer OS versions, many roles are specified to certain versions and break on newer OS versions.
You should not break anything by incrementally run the playbook and fix one broken package after the other.
Once the Playbook ran through, you should be able to reach `build.galaxyproject.eu`

## Troubleshooting
A few errors I ran into:
- be careful with fstab – if you change a FS that is defined there and `nofail` is not specified, the server will crash on reboot
- if the website is not reachable, check if Jenkins is running, if it is running, it could be probably NGINX or the firewall. Test the ports with `telnet build.galaxyproject.eu 80` and 443. 80 needs to be open for TLS-domain-challenge done by certbot.
- if Jenkins crashes on startup and without any logs, it might be a false command-line option, try without
