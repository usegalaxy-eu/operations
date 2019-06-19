---
title: Galaxy Update relative to upstream changes
author: Helena
---


```console
git checkout release_xx.yy
git pull # upstream release_xx.yy
git checkout release_xx.yy_europe
git rebase release_xx.yy
git rebase -i HEAD~5 # drop the latest CLIENTBUILD
make client-production
git add -f static
git commit -a -m 'CLIENTBUILD'
git push -f
```

And next night it will be deployed. Remember to restart handlers/swap zergligns as needed.
