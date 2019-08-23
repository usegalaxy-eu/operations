# non responsive yum

```
rm -f /var/lib/rpm/__*
rpm --rebuilddb -v -v
yum clean all
```

# visit all compute nodes and execute one command

```console
pdsh -g cloud 'singularity --version | colordiff'
```
