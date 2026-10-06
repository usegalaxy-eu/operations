# Multi-GPU on a single HTCondor node

See [Understanding partitionable GPU slots](../reference/multi-gpu-slots.md) for how slot allocation works and [Troubleshooting GPU environment visibility](../troubleshooting/multi-gpu-gpu-visibility.md) for diagnosis.
## TL;DR

To run multiple GPU jobs—each correctly mapped to its assigned GPU—on a single HTCondor node, here’s what to change:

TPV changes:

* TPV destinations (add the below to your respective GPU destination or even TPV tool defaults):

```YAML
    params:
      request_gpus: "{gpus or 0}"
```
_Example [conf](https://github.com/usegalaxy-eu/infrastructure-playbook/blob/94dc58ad59618a45c3a6645b9b58d07c722f5cd3/files/galaxy/tpv/destinations.yml.j2#L543-L545)_

* If your tools are running in a Docker container, add the below to the tool's conf in the `tools.yml`
* Let the container see only the assigned GPU.

```YAML
    params:
      docker_run_extra_arguments: ' --gpus all  --env CUDA_VISIBLE_DEVICES=$_CONDOR_AssignedGPUs '
```
_Example [conf](https://github.com/usegalaxy-eu/infrastructure-playbook/blob/94dc58ad59618a45c3a6645b9b58d07c722f5cd3/files/galaxy/tpv/tools.yml#L464)_

* If your tools are running in a Singularity container, add the below to the tool's conf in the `tools.yml`

```YAML
    params:
      singularity_run_extra_arguments: ' --nv --env CUDA_VISIBLE_DEVICES=$_CONDOR_AssignedGPUs '
```
_Singularity [doc](https://docs.sylabs.io/guides/3.5/user-guide/gpu.html#multiple-gpus)._

HTCondor config changes:
* If you would like to divide the GPU slots on your GPU host so that you can run/associate/map more than 1 GPU job per GPU

```ini
GPU_DISCOVERY_EXTRA = -extra -divide <N>
```

_Where `N` is an Int. (GPU memory will be equally divided between slots)_

* If you would like to for whatever reason want to make HTCondor use the GPU Index instead of short UUIDs.

```ini
GPU_DISCOVERY_EXTRA = -extra -by-index
```

_Use `-by-index`. GPU discovery command [doc](https://htcondor.readthedocs.io/en/latest/man-pages/condor_gpu_discovery.html)._


