# Machines underlying the OpenStack Cloud
The machines are listed under the corresponding OpenStack flavor names.  
VMs that created with these flavours can only spawn on the below listed hosts.  
Sorted by cores, than by memory.

## c1.c28m225
### Description
'Old' AMD machines, very stable
### Count
```yaml
VMs-per-machine: 1
machines: 7
max-VMs: 7
```
<details>
    <summary>Hostnames</summary>
    
```yaml
hosts:
- n4724.bwcloud.privat
- n4721.bwcloud.privat
- n4722.bwcloud.privat
- n4726.bwcloud.privat
- n4723.bwcloud.privat
- n4725.bwcloud.privat
- n4727.bwcloud.privat
```
    
</details>

## c1.c28m475
### Description
'Old' AMD machines, very stable
### Count
```yaml
VMs-per-machine: 1
machines: 12
max-VMs: 12
```
<details>
    <summary>Hostnames</summary>
    
```yaml
- n4707.bwcloud.privat
- n4718.bwcloud.privat
- n4720.bwcloud.privat
- n4709.bwcloud.privat
- n4702.bwcloud.privat
- n4712.bwcloud.privat
- n4719.bwcloud.privat
- n4711.bwcloud.privat
- n4703.bwcloud.privat
- n4713.bwcloud.privat
- n4715.bwcloud.privat
- n4716.bwcloud.privat
```
    
</details>

## c1.c36m100
### Description
'Old' Intel machines, not always stable
### Count
```yaml
VMs-per-machine: 1
machines: 31
max-VMs: 31
```
<details>
    <summary>Hostnames</summary>
    
```yaml
- n3619.bwcloud.privat
- n3620.bwcloud.privat
- n3621.bwcloud.privat
- n3617.bwcloud.privat
- n3618.bwcloud.privat
- n3626.bwcloud.privat
- n3630.bwcloud.privat
- n3628.bwcloud.privat
- n3627.bwcloud.privat
- n3625.bwcloud.privat
- n3631.bwcloud.privat
- n3623.bwcloud.privat
- n3629.bwcloud.privat
- n3624.bwcloud.privat
- n3633.bwcloud.privat
- n3637.bwcloud.privat
- n3639.bwcloud.privat
- n3642.bwcloud.privat
- n3635.bwcloud.privat
- n3640.bwcloud.privat
- n3638.bwcloud.privat
- n3634.bwcloud.privat
- n3641.bwcloud.privat
- n3643.bwcloud.privat
- n3644.bwcloud.privat
- n3645.bwcloud.privat
- n3646.bwcloud.privat
- n3649.bwcloud.privat
- n3647.bwcloud.privat
- n3648.bwcloud.privat
- n3657.bwcloud.privat
```
    
</details>

## c1.c36m225
### Description
'Old' Intel machines, not always stable
### Count
```yaml
VMs-per-machine: 1
machines: 15
max-VMs: 15
```
<details>
    <summary>Hostnames</summary>
    
```yaml
- n3655.bwcloud.privat
- n3656.bwcloud.privat
- n3651.bwcloud.privat
- n3650.bwcloud.privat
- n3654.bwcloud.privat
- n3652.bwcloud.privat
- n3653.bwcloud.privat
- n3668.bwcloud.privat
- n3669.bwcloud.privat
- n3670.bwcloud.privat
- n3666.bwcloud.privat
- n3672.bwcloud.privat
- n3665.bwcloud.privat
- n3667.bwcloud.privat
- n3671.bwcloud.privat
```
    
</details>

## c1.c36m900
### Description
'Old' Intel machines, not always stable
### Count
```yaml
VMs-per-machine: 1
machines: 1
max-VMs: 1
```
```yaml
- n3658.bwcloud.privat
```

## c1.c36m975
### Description
'Old' Intel machines, not always stable
### Count
```yaml
VMs-per-machine: 1
machines: 14
max-VMs: 14
```
<details>
    <summary>Hostnames</summary>
    
```yaml
- n3659.bwcloud.privat
- n3660.bwcloud.privat
- n3664.bwcloud.privat
- n3663.bwcloud.privat
- n3661.bwcloud.privat
- n3662.bwcloud.privat
- n3673.bwcloud.privat
- n3679.bwcloud.privat
- n3674.bwcloud.privat
- n3680.bwcloud.privat
- n3676.bwcloud.privat
- n3675.bwcloud.privat
- n3678.bwcloud.privat
- n3677.bwcloud.privat
```
    
</details>

## c1.c60m1975
### Description
'Old' Intel machines, our machine with the biggest memory
### Count
```yaml
VMs-per-machine: 1
machines: 1
max-VMs: 1
```
```yaml
- n3681.bwcloud.privat
```

## c1.c125m225
### Description
'New' AMD machines, 256 cores / machine
### Count
```yaml
VMs-per-machine: 2
machines: 5
max-VMs: 10
```
<details>
    <summary>Hostnames</summary>
    
```yaml
- n4686.bwcloud.privat
- n4685.bwcloud.privat
- n4684.bwcloud.privat
- n4688.bwcloud.privat
- n4687.bwcloud.privat
```
    
</details>

## c1.c125m425
### Description
'New' AMD machines, 256 cores each.
### Count
```yaml
VMs-per-machine: 2
machines: 19
max-VMs: 38
```
<details>
    <summary>Hostnames</summary>
    
```yaml
hosts:
- n3803.bwcloud.privat
- n3804.bwcloud.privat
- n3807.bwcloud.privat
- n3805.bwcloud.privat
- n3806.bwcloud.privat
- n3808.bwcloud.privat
- n3801.bwcloud.privat
- n3802.bwcloud.privat
- n4678.bwcloud.privat
- n4673.bwcloud.privat
- n4682.bwcloud.privat
- n4680.bwcloud.privat
- n4675.bwcloud.privat
- n4679.bwcloud.privat
- n4676.bwcloud.privat
- n4677.bwcloud.privat
- n4674.bwcloud.privat
- n4681.bwcloud.privat
- n4683.bwcloud.privat
```
    
</details>

# GPU Nodes

## g1.c7m20g1
### Description
Node with 8 Tesla T4 GPUs
### Count
```yaml
VMs-per-machine: 8
machines: 1
max-VMs: 8
```
```yaml
- gput4.bwcloud.privat
```

## g1.c8m20g1
### Description
'New' AMD machines, one GPU and 256 cores each
### Count
```yaml
VMs-per-machine: 1
machines: 10
max-VMs: 10
```
<details>
    <summary>Hostnames</summary>
    
```yaml
- n4679.bwcloud.privat
- n4678.bwcloud.privat
- n4675.bwcloud.privat
- n4677.bwcloud.privat
- n4682.bwcloud.privat
- n4676.bwcloud.privat
- n4674.bwcloud.privat
- n4680.bwcloud.privat
- n4681.bwcloud.privat
- n4673.bwcloud.privat
```
    
</details>


## g1.c36m100g1
### Description
'Old' Intel machines, one GPU per host
### Count
```yaml
VMs-per-machine: 1
machines: 2
max-VMs: 2
```
```yaml
- n3611.bwcloud.privat
- n3612.bwcloud.privat
```
