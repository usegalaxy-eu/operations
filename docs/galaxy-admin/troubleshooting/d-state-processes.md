# debug 'D' state in processe

Get all processes in D state: 

> ps axl | awk '$10 ~ /D/'

Looking at file handlers of a thread yields to:

```
root@sn09:~$ ll /proc/215503/task/296960/fd/**
lr-x------ 1 galaxy galaxy 64 Aug  2 17:09 /proc/215503/task/296960/fd/0 -> /dev/null
lrwx------ 1 galaxy galaxy 64 Aug  2 17:09 /proc/215503/task/296960/fd/1 -> 'socket:[3487300049]'
lr-x------ 1 galaxy galaxy 64 Aug  2 17:09 /proc/215503/task/296960/fd/10 -> /data/jwd01/main/048/946/48946081
lr-x------ 1 galaxy galaxy 64 Aug  2 17:11 /proc/215503/task/296960/fd/11 -> /data/jwd01/main/048/946/48946885
lr-x------ 1 galaxy galaxy 64 Aug  2 17:11 /proc/215503/task/296960/fd/12 -> /data/jwd01/main/048/950/48950933
lr-x------ 1 galaxy galaxy 64 Aug  2 17:11 /proc/215503/task/296960/fd/13 -> /data/jwd01/main/048/950/48950933
lrwx------ 1 galaxy galaxy 64 Aug  2 17:09 /proc/215503/task/296960/fd/2 -> 'socket:[3487300049]'
lrwx------ 1 galaxy galaxy 64 Aug  2 17:09 /proc/215503/task/296960/fd/3 -> 'socket:[3487336618]'
lrwx------ 1 galaxy galaxy 64 Aug  2 17:09 /proc/215503/task/296960/fd/4 -> 'socket:[3487342602]'
lrwx------ 1 galaxy galaxy 64 Aug  2 17:09 /proc/215503/task/296960/fd/41 -> 'socket:[3487388502]'
lrwx------ 1 galaxy galaxy 64 Aug  2 17:09 /proc/215503/task/296960/fd/42 -> 'socket:[3487426468]'
lrwx------ 1 galaxy galaxy 64 Aug  2 17:09 /proc/215503/task/296960/fd/43 -> 'socket:[3487471967]'
lrwx------ 1 galaxy galaxy 64 Aug  2 17:09 /proc/215503/task/296960/fd/44 -> 'socket:[3487492268]'
lrwx------ 1 galaxy galaxy 64 Aug  2 17:09 /proc/215503/task/296960/fd/45 -> 'socket:[3501137915]'
lrwx------ 1 galaxy galaxy 64 Aug  2 17:09 /proc/215503/task/296960/fd/47 -> 'socket:[3487842897]'
lrwx------ 1 galaxy galaxy 64 Aug  2 17:09 /proc/215503/task/296960/fd/5 -> 'socket:[3487337597]'
lrwx------ 1 galaxy galaxy 64 Aug  2 17:09 /proc/215503/task/296960/fd/53 -> 'socket:[3518012875]'
l-wx------ 1 galaxy galaxy 64 Aug  2 17:09 /proc/215503/task/296960/fd/6 -> /opt/galaxy/server/compliance.log
lrwx------ 1 galaxy galaxy 64 Aug  2 17:09 /proc/215503/task/296960/fd/7 -> 'socket:[3526229330]'
lr-x------ 1 galaxy galaxy 64 Aug  2 17:11 /proc/215503/task/296960/fd/8 -> /data/jwd01/main/048/946/48946885/metadata
lr-x------ 1 galaxy galaxy 64 Aug  2 17:11 /proc/215503/task/296960/fd/9 -> /data/jwd01/main/048/946/48946081/outputs
```

Which looks ok, Galaxy is cleaning up jobs.
