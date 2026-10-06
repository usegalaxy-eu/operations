---
title: Galaxy Update relative to upstream changes
author: Helena
---


```console
git checkout release_xx.yy
git pull # upstream release_xx.yy
git checkout release_xx.yy_europe
git rebase release_xx.yy
git rebase -i release_xx.yy # drop the latest CLIENTBUILD
make client-production
git add -f static
git commit -a -m 'CLIENTBUILD'
git push -f
```

And next night it will be deployed. Remember to restart handlers/swap zergligns as needed.

## Cherry Picking Commits

Say they write a super cool patch upstream for some feature we want but it's in dev.

1. Update the current release branch (just in case)

   ```
   git checkout release_xx.yy
   git pull upstream release_xx.yy
   ```

2. Go back to our branch and rebase on top of latest release branch:

   ```
   git checkout release_xx.yy_europe
   # And update relative to upstream
   git rebase release_xx.yy
   ```

3. Find the commits of the feature you want to apply on top, and cherry-pick those commits

   ```
   git cherry-pick f42bdb4f606ce049deed2470784bf8e4d85f699d
   git cherry-pick 901a9da826d0372551b5d186ab20454a2941bac6
   ```

4. I recommend that you next squash these cherry picked commits:

   ```
   git rebase -i release_xx.yy
   ```

   Take the commits with unhelpful messages like:

   ```
   pick 5ce042768d Add tools/json page which serves json-ld data
   pick 04530f77c9 Remove microdata tags
   pick 3fff23b949 CLIENTBUILD
   pick ab43005ab7 something useless
   pick 4300053489 and again
   ```

   and squash them

   ```
   pick 5ce042768d Add tools/json page which serves json-ld data
   pick 04530f77c9 Remove microdata tags
   pick 3fff23b949 CLIENTBUILD
   pick ab43005ab7 something useless
   squash 300053489 and again
   ```

   and give them a nicer message like "CHERRY-PICKED #8722" (or whatever upstream PR it was so you know when you can drop those commits)

5. Remember to drop + recreate the clientbuild if either the rebase or the cherry-picking introduced new UI commits!
