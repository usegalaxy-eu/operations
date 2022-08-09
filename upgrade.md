---
title: Galaxy Upgrading procedures
---


# 7 days before downtime

- Write an announcment about the potential Galaxy downtime explaining that Galaxy is being upgraded. Be sure to link to the release annoucement,  see https://github.com/usegalaxy-eu/website/blob/master/_data/notices.yml

# a few days before downtime

## update webhooks repo

1. update our [webhooks reposiroty](https://github.com/usegalaxy-eu/galaxy-webhooks) with the latest changes from [upstream Galaxy](https://github.com/galaxyproject/galaxy/tree/dev/config/plugins/webhooks)

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


