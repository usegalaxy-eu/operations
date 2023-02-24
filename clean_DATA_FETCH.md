Given that script:

```python3
galaxy@sn06:/data/dnb02/galaxy_db$ cat /tmp/get_wd.py 
#!/usr/bin/python

import os, sys, shutil
job_id = sys.argv[1]

#/data/jwd02f/main/055/587/55587325/

path1 = f'/data/jwd02f/main/0{job_id[:2]}/{job_id[2:5]}/{job_id}/'
path2 = f'/data/jwd04/main/0{job_id[:2]}/{job_id[2:5]}/{job_id}/'

if os.path.exists(path1):
        print(path1)
        shutil.rmtree(path1)
elif os.path.exists(path2):
        print(path2)
        shutil.rmtree(path2)
```

I do the following:

1. get a list of IDs that you would like to restart:

```bash
gxadmin query queue-details --all | grep DATA_FE | grep celery | head -n 120 | awk '{print $3}' > /tmp/top_120.txt

```

2. fail all jobs
```bash
cat /tmp/top_120.txt | xargs -i gxadmin mutate fail-job {} --commit
```

3. remove JWDs
```bash
cat /tmp/top_120.txt | xargs -i /tmp/get_wd.py {}
```

4. reassign handlers - change from celery to the real stuff
```bash
cat /tmp/top_120.txt | xargs -i gxadmin mutate reassign-job-to-handler {} handler_sn06_0 --commit
```

5. restart the job
```bash
cat /tmp/top_120.txt | xargs -i gxadmin mutate restart-jobs --commit {}
```
