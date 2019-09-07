---
title: Galaxy Upgrading procedures
---


# 7 days before downtime

- Write an announcment about the potential Galaxy downtime explaining that Galaxy is being upgraded. Be sure to link to the release annoucement.

# 1 day before downtime

1. Clone [our fork](https://github.com/usegalaxy-eu/galaxy/).
2. Check out our current release branch (e.g. `release_XX.YY_europe`)
3. `git format-patch release_XX.YY` (e.g.) in order to get the patches from our current release
4. Go through and *delete* any that are described as being **already upstreamed** for the current release. Delete any CLIENTBUILD steps.
5. Checkout latest release (e.g. `release_AA.BB`), and create a branch with `release_AA.BB_europe` from there.
6. Apply the remaining patch files that were generated in step 3 (`git am -3 --ignore-whitespace < 0001-EU-foo-bar.patch`)
7. Update [`infrastructure-playbook`](https://github.com/usegalaxy-eu/infrastructure-playbook/) to sync configuration files and PR this + latest commit ID of the new branch
8. `make client-production`
9. `python scripts/plugin_staging.py` (if it exists)
9. `git add -f static/`
10. `git commit -a -m 'CLIENTBUILD'`
11. `git push -f`

If you're rebasing against an updated release branch (because you branched much earlier) then you'll want to do a `git rebase -i release_XX.YY` and **drop** any 'CLIENTBUILD' type commits, before doing another round of client-build / plugin staging / adding static / committing.

# Downtime begins

- (optionally) update conda with

```bash
galaxy@sn04:~$ export PATH=/usr/local/tools/_conda/bin/:$PATH
galaxy@sn04:~$ which conda
/usr/local/tools/_conda/bin/conda
galaxy@sn04:~$ conda update -n base -c conda-forge conda
```

- Run playbook (maybe with `make galaxy CHECK=1` to be certain of your changes.)
- Add a blog post about this (an [example](https://github.com/usegalaxy-eu/galaxy-freiburg/pull/82))

# Rebuilding the client

```
make client-production
git add -f static/
git commit -a -m 'CLIENTBUILD'
git push -f
```
