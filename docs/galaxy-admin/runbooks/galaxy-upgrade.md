---
title: Galaxy Upgrading procedures
---

# 7 days before downtime

- Write an announcement about the potential Galaxy downtime explaining that Galaxy is being upgraded. Be sure to link to the release announcement, see https://github.com/usegalaxy-eu/website/blob/master/_data/notices.yml

# a few days before downtime

## update web-hooks repo

1. update our [webhooks repository](https://github.com/usegalaxy-eu/galaxy-webhooks) with the latest changes from [upstream Galaxy](https://github.com/galaxyproject/galaxy/tree/dev/config/plugins/webhooks)

## create a new Galaxy deployment branch

0. [Note the average memory usage](https://github.com/usegalaxy-eu/operations/blob/dce7ce8ebfc433d0b76d337b4e4d3cd85f89f138/procmgmt.md?plain=1#L96) of gunicorns and job handlers
1. Clone [our fork](https://github.com/usegalaxy-eu/galaxy/).
2. Check out the release branch you want to switch to, e.g. `release_XX.ZZ`
3. Ensure it's updated: `git pull`
4. Checkout _our_ previous release branch (`release_XX.YY`)
5. `git rebase -i release_XX.ZZ` to rebase our commits on top of the new release branch
   - try hard to get as many commits upstream, aim is to not carry around any commit
6. Update [`infrastructure-playbook`](https://github.com/usegalaxy-eu/infrastructure-playbook/) to:

- sync configuration files, see https://github.com/usegalaxy-eu/infrastructure-playbook/blob/master/bin/diff-before-update
  - While syncing the configuration files, look for any new `production` templates available in the `lib/galaxy/files/templates/examples` and in the `lib/galaxy/objectstore/templates/examples` in the newly created release branch above. If there are any new templates that we would like to include, add them to the `templates/galaxy/config/file_source_templates.yml.j2` and `templates/galaxy/config/object_store_templates.yml.j2` in the [infrastructure-playbook](https://github.com/usegalaxy-eu/infrastructure-playbook) repository. Check this [PR](https://github.com/usegalaxy-eu/infrastructure-playbook/pull/1225/commits/bb01c94ca30589914217ea6cfb6941bdce6273fc) for reference on adding new templates and simultaneously updating the [diff-before-update script](https://github.com/usegalaxy-eu/infrastructure-playbook/blob/master/bin/diff-before-update) to include the new templates. Please ensure that the `diff-before-update` script is updated to include the new templates before running the script.
- update to the latest commit ID of the new branch, see [this line](https://github.com/usegalaxy-eu/infrastructure-playbook/blob/be8d196b26f46852bc593a0d8a64e66dedde69c5/group_vars/sn09/sn09.yml#L354).

# Downtime begins

- (optionally) update conda with

```bash
galaxy@sn09:~$ export PATH=/usr/local/tools/_conda/bin/:$PATH
galaxy@sn09:~$ which conda
/usr/local/tools/_conda/bin/conda
galaxy@sn09:~$ conda update -n base -c conda-forge conda
```

- Run playbook (maybe with `make main.eu CHECK=1` to be certain of your changes.)
- (In case of some problems with the database migration, you can manually trigger it with `/opt/galaxy/venv/bin/python /opt/galaxy/server/scripts/manage_db.py -c /opt/galaxy/config/galaxy.yml upgrade`)
- Add a blog post about this (an [example](https://github.com/usegalaxy-eu/galaxy-freiburg/pull/82))

