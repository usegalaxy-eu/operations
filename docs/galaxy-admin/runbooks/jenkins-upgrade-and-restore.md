# Jenkins

See [Jenkins upgrade troubleshooting](../troubleshooting/jenkins-upgrade.md) if the restored service does not start correctly.
I would recommend to read [the official backup guide](https://www.jenkins.io/doc/book/system-administration/backing-up/) first.

Announcing the downtime is always important, as well as scheduling preferrably a date in the morning in the compute center for the maintenance. (If you come in the afternoon and something goes wrong it can happen that the room is locked down before you are done.)

Updating Jenkins is generally not difficult, because the whole service is file-based and all relevant files live in the `$JENKINS_HOME` directory. This is defined [here](https://github.com/usegalaxy-eu/infrastructure-playbook/blob/25ddd20a643c33234712ae40641cc29b0fab731d/group_vars/build.yml#L3). This directory lives in a separate Logical Volume and can be backed up easily by shutting Jenkins down and creating a snapshot. After the Upgrade / OS re-installation is done, it can be rsynced / remounted and the build playbook can be run.

## Graceful Shutdown

In order to stop Jenkins gracefully, you can [prepare for Shutdown](https://build.galaxyproject.eu/manage/prepareShutdown) which gives you also the option to communicate the reason to your users. This will not shut down Jenkins, but it will not run any new jobs. Once all jobs have ended, you can send a POST request to `https://build.galaxyproject.eu/exit` which will shut down Jenkins (if you are logged in as admin, of course).

## Backup

Now you can check `journalctl` and make sure it has fully stopped. To create a LV snapshot, you can use the following commands:

```sh
# mount NFS if not happened
mount -t nfs ufr-dyn.isi1.public.ads.uni-freiburg.de:/ifs/isi1/ufr/bronze/nfs/denbi/ /data/dnb01
# Create the snapshot
lvcreate -L50G -s -n <snapshot-name> <jenkins-home-dir-LV-name> # e.g. /dev/rl/jenkins-home
# Create a disk image and save it to NFS
dd if=/dev/<vg-name>/<snapshot-name> of=/data/dnb01/jenkins-backup/<backup-image-name>.dd
```

If you want to feel extra-safe, you can also create a FS-dump and also test if you can mount the back-up image with

```sh
mount -o loop /data/dnb01/jenkins-backup/<backup-image-name>.dd /opt
```

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
4. copy over the keys from `/root/.ssh/` backup to new root directory
5. unmount the backup image

## Playbooks

Last step is to run the playbook `build.yml` and see if everything worked as expected.
NOTICE: It is quite normal for playbooks to fail after installing newer OS versions, many roles are specialised for certain versions and break on newer OS versions.
You should not break anything by incrementally run the playbook and fix one broken package after the other.
Once the Playbook ran through, you should be able to reach `build.galaxyproject.eu`.

