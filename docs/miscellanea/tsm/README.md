# TSM Client Configuration Files

Here you'll find the actual configuration files for our TSM
clients. After the TSM client application is installed, these
files go in

```
/opt/tivoli/tsm/client/ba/bin/
```

\*yuck\* That said, in order to achieve a slightly more SysVR4-
compliant directory layout, I usually put those files in
```
/etc/opt/tivoli/
```

and create symlinks to there in `/opt/tivoli/tsm/client/ba/bin/`.
The TSM client software will, of course, only look is its own
installation directory.


PS: This piece of software by IBM has historically been known as
"Data Storage Manager" (DSM), "Tivoli Storage Manager" (TSM) and
"Spectrum Protect Manager". It is thus variously referred to as
"DSM", "TSM", "Tivoli" and "Spectrum Protect" in file and variable
names as well as existing documentation. Go figure...

