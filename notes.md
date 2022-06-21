# decode Galaxy id
```
user@sn06:~$ . /opt/galaxy/venv/bin/activate
(venv) user@sn06:~$ cd /opt/galaxy
(venv) user@sn06:/opt/galaxy$ python server/scripts/secret_decoder_ring.py decode ec81bbe85ee13506
746380
```

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

# GPUs

Check if tensorflow is compiled with GPU support and a GPU is available.

```python
import tensorflow as tf;
sess = tf.Session(config=tf.ConfigProto(log_device_placement=True));
print(tf.test.is_built_with_cuda()); print( tf.test.is_gpu_available())
```

Check the utilization of the GPU on the host system:

```console
> nvidia-smi 

Sun Aug 25 22:41:01 2019       
+-----------------------------------------------------------------------------+
| NVIDIA-SMI 418.67       Driver Version: 418.67       CUDA Version: 10.1     |
|-------------------------------+----------------------+----------------------+
| GPU  Name        Persistence-M| Bus-Id        Disp.A | Volatile Uncorr. ECC |
| Fan  Temp  Perf  Pwr:Usage/Cap|         Memory-Usage | GPU-Util  Compute M. |
|===============================+======================+======================|
|   0  Tesla T4            Off  | 00000000:00:05.0 Off |                    0 |
| N/A   40C    P0    28W /  70W |      0MiB / 15079MiB |      0%      Default |
+-------------------------------+----------------------+----------------------+
|   1  Tesla T4            Off  | 00000000:00:06.0 Off |                    0 |
| N/A   42C    P0    28W /  70W |      0MiB / 15079MiB |      0%      Default |
+-------------------------------+----------------------+----------------------+
|   2  Tesla T4            Off  | 00000000:00:07.0 Off |                    0 |
| N/A   42C    P0    27W /  70W |      0MiB / 15079MiB |      0%      Default |
+-------------------------------+----------------------+----------------------+
|   3  Tesla T4            Off  | 00000000:00:08.0 Off |                    0 |
| N/A   43C    P0    26W /  70W |      0MiB / 15079MiB |      0%      Default |
+-------------------------------+----------------------+----------------------+
                                                                               
+-----------------------------------------------------------------------------+
| Processes:                                                       GPU Memory |
|  GPU       PID   Type   Process name                             Usage      |
|=============================================================================|
|  No running processes found                                                 |
+-----------------------------------------------------------------------------+

```

# How to find out any password from Jenkins

1. find out the credential name from the "Bindings" tab in the project's configuration.

![](images/image.png)

2. find the encrypted value:
```
root@build:~$ grep -A1 vault-pass-usegalaxy-star /opt/jenkins/jenkins/jobs/usegalaxy-eu/config.xml
              <description>vault-pass-usegalaxy-star</description>
              <secret>{supersecretstringhere}</secret>
```
3. decrypt

go to jenkins → manage jenkins → script console
https://build.galaxyproject.eu/script

google "jenkins decrypt secret" because you can never remember  
println(hudson.util.Secret.fromString("{supersecretstringhere}").getPlainText())

4. done!

# How Condor honors TIaaS priorities

All the details in this https://github.com/usegalaxy-eu/issues/issues/277

# PostgreSQL configuarions

* [PGTune](https://pgtune.leopard.in.ua) is a PG configurator assistent

# How to install pdsh with genders support on Centos8

https://gist.github.com/gmauro/cc97ff1287282469ce98c2b8035100f2
