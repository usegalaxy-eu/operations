# non responsive yum

```
rm -f /var/lib/rpm/__*
rpm --rebuilddb -v -v
yum clean all
```
