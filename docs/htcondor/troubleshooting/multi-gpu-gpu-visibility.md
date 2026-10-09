# Troubleshooting GPU environment visibility

See [Multi-GPU on a single HTCondor node](../runbooks/multi-gpu-single-node-htcondor.md) for the current configuration.
## Symptom

* Submitting 5 jobs results in 4 running and 1 idle — **expected**.
* However, only **one GPU shows load** in `nvidia-smi` — **unexpected**.
* Within the job script, `$CUDA_VISIBLE_DEVICES` appears **empty or incorrect**.

## Diagnosis

1. **HTCondor 9.x+** introduces **UUID-based GPU advertising** (e.g., `GPU-b156e653`) rather than index-based (`CUDA0`, `CUDA1`, etc.).
2. Initial assumption: HTCondor would automatically translate UUIDs to usable indices in `CUDA_VISIBLE_DEVICES`.
3. Reality: HTCondor **does not perform translation**, and environment variables (`CUDA_VISIBLE_DEVICES`) were populated with **truncated or invalid values** (e.g., `156653` from `GPU-b156e653`).
4. As a result, **TensorFlow failed to detect any GPUs**.

## Verification

Check individual job ClassAds to confirm GPU assignment:

```bash
condor_q -l <job_id> | grep -i assigned
# Example output:
AssignedGPUs = "GPU-b156e653"
```


## Investigation history

The sections below preserve the original investigation and its later updates.

### Overview

Here, I describe how to configure and utilize multiple GPUs on a single worker node within an HTCondor compute environment. It outlines my attempts at HTCondor configuration changes, the behavior of partitionable slots, troubleshooting steps, and the final solution for ensuring GPU visibility within jobs.


### HTCondor GPU configuration

#### 1. Worker node configuration

On a GPU worker node, update the HTCondor configuration to [export necessary GPU-related environment variables](https://htcondor-wiki.cs.wisc.edu/index.cgi/wiki?p=HowToManageGpus):

```ini
ENVIRONMENT_FOR_AssignedGPUs = CUDA_VISIBLE_DEVICES, GPU_DEVICE_ORDINAL
```

Apply the configuration change:

```bash
condor_reconfig

# and/or

systemctl restart condor
```

#### 2. Job submission

In the job submit file, request GPU resources as needed:

```ini
request_gpus = 1
```

This ensures that HTCondor allocates one GPU per job.


### Final solution

#### Updated configuration

Only set:

```ini
ENVIRONMENT_FOR_AssignedGPUs = CUDA_VISIBLE_DEVICES
```

Then, **inside the job script**, explicitly export the proper environment variable using the HTCondor-published `_CONDOR_AssignedGPUs` variable:

```bash
export CUDA_VISIBLE_DEVICES=$_CONDOR_AssignedGPUs
```

_HTCondor automatically publishes the $_CONDOR_AssignedGPUs environment variable, which contains the value of the slot’s AssignedGPUs attribute._

Finally, I submitted 5 GPU jobs (see the [example job files and scripts](../reference/multi-gpu-slots.md#examples) and the NFS path `/data/misc06/test_pxe_gpu_jobs`).

![image](https://github.com/user-attachments/assets/875866c3-9df1-4bac-9fc9-4ab207d1cd98)

As expected, I can see that four jobs are running and one is idle; each of the four running jobs uses its own assigned GPU.

![Image](https://github.com/user-attachments/assets/2d603c29-57df-4f86-8891-1c7c1da85329)

Further, the job output files (a few `print` and `echo` statements in the example script) show that each job is assigned only one GPU and that it uses that

![Image](https://github.com/user-attachments/assets/78d66815-8925-4214-9463-6e385bad76a3)

![image](https://github.com/user-attachments/assets/56699e67-a7d3-465a-b423-6066365468d0)

#### Why this works

* `_CONDOR_AssignedGPUs` contains the exact value of the slot’s `AssignedGPUs` attribute (e.g., `GPU-b156e653`).
* Recent versions of TensorFlow support GPU UUIDs (and probably similar libraries and tools), including short UUIDs.
* No additional index conversion/translation is needed to translate the UUIDs into the GPU index
* _We might have to 100% validate that all tools/libraries other than Tensorflow understand the GPU UUIDs and that all of them rely only on the ENV `CUDA_VISIBLE_DEVICES`_


#### Update 1:

* I ran a latest test where I removed the `ENVIRONMENT_FOR_AssignedGPUs = CUDA_VISIBLE_DEVICES` from the HTCondor worker conf.

* Without this ( `ENVIRONMENT_FOR_AssignedGPUs = CUDA_VISIBLE_DEVICES`) in the HTCondor worker config, the variable `CUDA_VISIBLE_DEVICES` actually gets correctly populated (instead of the truncated `156653`, they get `GPU-b156e653`), unlike what I described above, which warranted a dedicated `export CUDA_VISIBLE_DEVICES=$_CONDOR_AssignedGPUs` on the test script.

* Output from my latest test run (submitted six jobs, 4 of them ran, where each job had access to individual GPUs), I added the following to the bash script (see issue above for details)

```bash
echo "Raw Assigned GPU(s): $_CONDOR_AssignedGPUs"
echo "CUDA_VISIBLE_DEVICES: $CUDA_VISIBLE_DEVICES"
```

```bash
Raw Assigned GPU(s): GPU-b156e653
CUDA_VISIBLE_DEVICES: GPU-b156e653
```

![Image](https://github.com/user-attachments/assets/9c4550fb-7b7f-4508-be5d-be0ad9da0eca)

This indicates that no modifications are needed to the HTCondor worker config or additional handling of environment variables in the scripts.

---
#### Update 2:

* Once the above (Update 1) patch was rolled out, I started 6 [Flux jobs](https://usegalaxy.eu/?tool_id=toolshed.g2.bx.psu.edu%2Frepos%2Fbgruening%2Fblack_forest_labs_flux%2Fblack_forest_labs_flux%2F2024%2Bgalaxy4&version=latest) and while monitoring, I identified that four jobs were started concurrently (that's a good sign), however, all of them were using the GPU index zero instead of their own assigned GPU.
* The reason behind that is that these Flux jobs are running inside a Docker container to which we pass the Docker run parameter `--gpus all`, and Docker seems to handle this differently. The container sees all 4 GPUs when running `nvidia-smi` from within the container, and all the jobs end up using GPU index 0.
* To **fix** this, we should explicitly set the Docker ENV **`--env CUDA_VISIBLE_DEVICES=$_CONDOR_AssignedGPUs'`** and this makes the jobs to use only the assigned GPUs. _Note: In theory, one could also pass the assigned GPU ID directly to Docker’s `--gpus` option, e.g., `--gpus "device=$_CONDOR_AssignedGPUs"`. However, due to complex shell quoting and variable interpolation challenges, this approach seems cumbersome and error-prone. Using the environment variable to control GPU visibility is simpler and more robust._
* Further, I have also tested the **`-divide <N>`** to split the 4 GPU slots into N slots (`N` = 3, in this example; so we have 12 GPU slots). The HTcondor config is this: `GPU_DISCOVERY_EXTRA = -extra-divide 3`.
* I then submitted six jobs (manually using the [example job files](../reference/multi-gpu-slots.md#examples), and also submitted six Flux jobs) and all 6 of them started concurrently.
* In this picture, we can see that more than 1 GPU job is run per GPU (see the bottom of the image, which shows the GPU index and the corresponding process)

![Image](https://github.com/user-attachments/assets/75373af0-2efa-46fb-88e1-b2b8159ada3f)
