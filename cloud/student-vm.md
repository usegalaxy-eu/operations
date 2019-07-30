---
title: Launching a Student VM
---

Launching VMs under the `freiburg_galaxy` account can be a nice workaround to requesting more quota for students, one-by-one. This can be done with the [`infrastructure`](https://github.com/usegalaxy-eu/infrastructure) repository which we use to manage all of the single VMs that we launch to run different services (e.g. apollo, stats, etc.)

Here is an example instance, this launched an Ubuntu 18.04 instance with flavour m1.medium, and the keypair of `student-hr1025`. I've used the format `student-<uniid>` but it does not need to be specifically in this format (allowed characters `[A-Za-z0-9-_]`). Maybe this makes it easier to keep track of which students have access to which instances and make it easy to figure out which should be removed when their project is complete? The important thing is that it should be consistent between:

- the resource ID (last part before `{`)
- the server name
- the key pair
- the keypair ID
- the key pair name

(These do not truly need to be equivalent but it will make your life easier and less confusing!)


```hcl
resource "openstack_compute_instance_v2" "student-hr1025" {
  name            = "student-hr1025"
  image_name      = "Ubuntu 18.04"
  flavor_name     = "m1.medium"
  key_pair        = "student-hr1025"
  security_groups = "${var.sg_webservice-pubssh}"

  network {
    name = "public"
  }
}
```

You will need to add a keypair for them like this in the [`keypairs.tf` file](https://github.com/usegalaxy-eu/infrastructure/blob/master/keypairs.tf):

```hcl
resource "openstack_compute_keypair_v2" "student-hr1025" {
  name       = "student-hr1025"
  public_key = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQDV7gfNbNN5O8v..."
}
```

Commiting these changes to this repository should immediately trigger a run of [terraform in Jenkins](https://build.galaxyproject.eu/job/usegalaxy-eu/job/infrastructure/).
