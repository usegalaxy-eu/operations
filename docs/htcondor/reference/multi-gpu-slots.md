# Understanding partitionable GPU slots

See [Multi-GPU on a single HTCondor node](../runbooks/multi-gpu-single-node-htcondor.md) for configuration and [Troubleshooting GPU environment visibility](../troubleshooting/multi-gpu-gpu-visibility.md) for diagnosis.
## Understanding partitionable GPU slots

### 1. GPU worker advertising

HTCondor advertises all available GPUs as part of a partitionable slot.

Example output from a GPU host with 4 GPUs:

```bash
condor_status -l tstgpu.bi.privat | grep -i gpu

AssignedGPUs = "GPU-b156e653,GPU-b2c83767,GPU-c62b119c,GPU-e58c2e11"
AvailableGPUs = { GPUs_GPU_b156e653,GPUs_GPU_b2c83767,GPUs_GPU_c62b119c,GPUs_GPU_e58c2e11 }
```

This reflects a single partitionable slot encompassing all 4 GPUs.

### 2. Dynamic slot creation

When a job is submitted with `request_gpus = 1`:

* HTCondor creates a dynamic slot from the partitionable slot.
* One specific GPU is assigned (e.g., `GPU-b156e653`).
* The dynamic slot's `AssignedGPUs` attribute determines the exact GPU UUID.

HTCondor sets the specified environment variables (`CUDA_VISIBLE_DEVICES`, etc.) accordingly — if configured correctly.

### 3. GPU allocation rules

* Concurrency limit: Only as many jobs as available GPUs can run simultaneously.
* Example: With 4 GPUs, 4 jobs requesting 1 GPU each will run. A 5th job will remain idle until a GPU becomes available.
* _This might lead to underutilized GPUs_

### 4. Over-subscribing GPUs (this is untested), more than one job per GPU

* Add the following to the HTCondor configuration, and this will create two slots per GPU on the GPU node ([ref](https://agenda.hep.wisc.edu/event/2014/contributions/28474/attachments/9193/11097/PattonJ%20-%20GPUs%20with%20HTCondor.pdf))

```ini
GPU_DISCOVERY_EXTRA = $(GPU_DISCOVERY_EXTRA) -divide 2
```


## Examples:

* Example job submit file I used for the testing

```ini
universe = vanilla
executable = /data/misc06/test_pxe_gpu_jobs/gpu_test.sh
output = /data/misc06/test_pxe_gpu_jobs/job1.out
error = /data/misc06/test_pxe_gpu_jobs/job1.err
log = /data/misc06/test_pxe_gpu_jobs/job1.log
requirements = Machine == "tstgpu.bi.privat"
request_cpus = 2
request_memory = 2GB
request_GPUs = 1
queue 1
```

* Example `gpu_test.sh`

```bash
#!/bin/bash
echo "[$(date)] Starting job on host: $(hostname)"
echo "Raw Assigned GPU(s): $_CONDOR_AssignedGPUs"
echo "Assigned GPU(s): $CUDA_VISIBLE_DEVICES"
export CUDA_VISIBLE_DEVICES=$_CONDOR_AssignedGPUs
/data/misc06/test_pxe_gpu_jobs/tf-cuda-venv/bin/python3 /data/misc06/test_pxe_gpu_jobs/gpu_test_tf.py
echo "[$(date)] Job finished."
```

* Example `gpu_test_tf.py`

```python
# gpu_test_tf.py
import tensorflow as tf
import time
import os

gpus = tf.config.list_physical_devices('GPU')
if not gpus:
    print("No GPU found.")
    exit(1)

# Optionally: log which GPU(s) TensorFlow sees
print("Visible GPU(s) to TensorFlow:", gpus)

print("Using GPU(s):", gpus)

# Create two large constant tensors
a = tf.random.normal([4096, 4096])
b = tf.random.normal([4096, 4096])

@tf.function
def matrix_multiply():
    return tf.matmul(a, b)

start = time.time()
print("Starting 10-minute TensorFlow GPU workload...")

# Run matrix multiplication in a loop for ~10 minutes
while time.time() - start < 100:
    result = matrix_multiply()
    _ = result.numpy()  # Force evaluation on GPU

print("Workload complete.")
```

## References:
1. [HTCondor Configuration Macros](https://htcondor.readthedocs.io/en/latest/admin-manual/configuration-macros.html#ENVIRONMENT_FOR_Assigned%3Cname%3E),
2. [HTCondor manage GPUS](https://htcondor-wiki.cs.wisc.edu/index.cgi/wiki?p=HowToManageGpus)
3. [HTCondor GPU short UUIDs](https://indico.cern.ch/event/1174979/contributions/5056722/attachments/2528544/4349952/Using%20GPUs%20with%20HTCondor.pdf)
4. https://www.youtube.com/watch?v=qFHSfguP9XI
5. https://agenda.hep.wisc.edu/event/2014/contributions/28474/attachments/9193/11097/PattonJ%20-%20GPUs%20with%20HTCondor.pdf

---
