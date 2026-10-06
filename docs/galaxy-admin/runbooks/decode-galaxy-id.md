# decode Galaxy id
```
user@sn09:~$ . /opt/galaxy/venv/bin/activate
(venv) user@sn09:~$ cd /opt/galaxy
(venv) user@sn09:/opt/galaxy$ python server/scripts/secret_decoder_ring.py decode ec81bbe85ee13506
746380
```
or using gxadmin
```
user@sn09:~$ . /opt/galaxy/venv/bin/activate
(venv) user@sn09:~$ GALAXY_ROOT=/opt/galaxy/server GALAXY_CONFIG_FILE=/opt/galaxy/config/galaxy.yml gxadmin galaxy decode ec81bbe85ee13506
746380
```

