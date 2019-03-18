# Operations Manual for usegalaxy.eu

## Read-only Fridays

- **NO EXCEPTIONS**
- Do not merge things to the playbook repositories that will be auto-applied
- Do not do any manual systems administration
- Consider writing documentation or more test cases instead.

## Custom Galaxy Subdomain

First, choose a name. In this tutorial we'll use `example` which will be `example.usegalaxy.eu`, with a brand of "Example". Remember to change as appropriate for your name.

### Galaxy Configuration

1. [Add your site](https://github.com/usegalaxy-eu/infrastructure-playbook/blob/master/group_vars/custom-sites.yml). It should look something like:

    ```yaml
    - name: example
      brand: Example
    ```

    Name is an id used in creation of several filenames internally and in the website repository. It should match `[a-z]+`

2. Make a PR with these changes

In the website repository:

1. [Create an index page like this one](https://github.com/usegalaxy-eu/website/blob/master/index-metagenomics.md) in the website repository. Above we specified that `name: example`, so you should create `index-example.md` in the root of the website repository.
2. Make a PR with these changes

### DNS Changes

1. Add your domain to [this list](https://github.com/usegalaxy-eu/infrastructure/blob/master/dns.tf#L36) under `subdomain`, and increase the `count` parameter below by one.
2. Make a PR with these changes.

### Customizing Tools

1. Edit [global_host_filter.py](https://github.com/usegalaxy-eu/infrastructure-playbook/blob/master/templates/galaxy/config/global_host_filters.py.j2), you'll want to edit both functions to define appropriate values for your galaxy subdomain.

## Adding a User to Grafana

1. They should [login](https://grafana.denbi.uni-freiburg.de/login) using GitHub auth.
    - Note that they must be a member of an [approved organisation](https://github.com/usegalaxy-eu/infrastructure-playbook/blob/39d5b7e86b4f45acba53adb965b11b63700327ad/group_vars/grafana.yml#L119).  (Note that this link is to a specific revision where I could be sure the line number was correct, please check against `master`)
2. (As an admin) Open [the user list](https://grafana.denbi.uni-freiburg.de/admin/users/)
3. Find them and "edit"
4. Under "Organizations" type "Main" and select the main organisation that shows up, adding them as the appropriate role.

## Updating a Tool

Please just editing the [yaml file](https://github.com/usegalaxy-eu/usegalaxy-eu-tools)

## Adjusting a Tool's Requirements (Increasing Memory / CPU)

1. Edit
2. PR is merged
3. Wait until the end of the hour, at which the playbook will run. You should be able to confirm this via [grafana](https://grafana.denbi.uni-freiburg.de/dashboard/db/galaxy?refresh=1m&panelId=39&fullscreen&orgId=1)

## Restarting Galaxy

If you're doing a full restart of the server, use `supervisorctl restart all`
followed by `supervisorctl stop z1:zergling1` as supervisor restart restarts
too much.

Restarting handlers can be done via `gxadmin handler restart`, in case
changes are made to job scheduling.

However if you just want to swap the zerglings in use (e.g. for a newly
installed set of tools), then you must use `gxadmin zeg swap` which
includes special logic for waiting until the new zergling is alive and then
stopping the old one, because they don't do the magic turning of the other one
off that is described in the galaxy training.

## (Re-)sending activation links

Some users do not get the activation email or are unable to find it. On request we can generate the link with the
following procedure:

```bash
cd /opt/galaxy/server/
. ../venv/bin/activate
python /data/gxmnt/galaxy-dist/scripts/activation_link.py -c ~/config/galaxy.ini -e <their email>
```

## Galaxy Upgrading procedures

### 7 days before downtime

- (If necessary) Write an announcment about the Galaxy downtime explaining what is being upgraded. Be sure to link to the release annoucement.

### 1 day before downtime

1. Clone [our fork](https://github.com/usegalaxy-eu/galaxy/).
2. Check out our current release branch (e.g. `release_XX.YY_europe`)
3. `git format-patch release_XX.YY` (e.g.) in order to get the patches from our current release
4. Go through and *delete* any that are described as being **already upstreamed** for the current release.
5. Checkout latest release, and create a branch with `_europe` from there.
6. Apply the remaining patches
7. Update [`infrastructure-playbook`](https://github.com/usegalaxy-eu/infrastructure-playbook/) to sync configuration files and PR this + latest commit ID of the new branch
8. `make client-production`
9. `python scripts/plugin_staging.py` (if it exists)
9. `git add -f static/`
10. `git commit -a -m 'CLIENTBUILD'`
11. `git push -f`

If you're rebasing against an updated release branch (because you branched much earlier) then you'll want to do a `git rebase -i release_XX.YY` and **drop** any 'CLIENTBUILD' type commits, before doing another round of client-build / plugin staging / adding static / committing.

### Downtime begins

- Run playbook (maybe with `make galaxy CHECK=1` to be certain of your changes.)
- Add a blog post about this (an [example](https://github.com/usegalaxy-eu/galaxy-freiburg/pull/82))
