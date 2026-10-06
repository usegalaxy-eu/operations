# (Re-)sending activation links

Some users do not get the activation email or are unable to find it. On request we can generate the link with the
following procedure:

```bash
cd /opt/galaxy/server/
. ../venv/bin/activate
python /data/gxmnt/galaxy-dist/scripts/activation_link.py -c ~/config/galaxy.ini -e <their email>
```
