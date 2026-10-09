# Adding a new VM

1. If needed, build a new base image with the VGCN image build pipeline and add a `libvirt_volume` for it in [images.tf](https://github.com/usegalaxy-eu/kvm-infrastructure/blob/master/images.tf)
2. Add an entry to the `locals.vms` map in [vms.tf](https://github.com/usegalaxy-eu/kvm-infrastructure/blob/master/vms.tf) (pick a free IP in `10.4.68.0/24`, sizes, base image and data disk mount) and  make a pull  request against  the repository.
3. Review the terraform plan in jenkins [CI](https://build.galaxyproject.eu/job/usegalaxy-eu/job/kvm-infrastructure-pr/) 
4. Merge the PR.  This will trigger the  CI and  make  the terraform  apply.
