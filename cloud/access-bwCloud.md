---
title: Accessing bwCloud with Terraform in a Seperate Project
---
# Accessing bwCloud with Terraform
With the help of this tutorial, you will learn how to access the bwCloud via Terraform.
Make sure you can log in to [portal.bwCloud.org](portal.bwCloud.org) using your university login credentials.
You should see your personal dashboard.

Next make sure to install OpenStack and Terraform to your machine.
Create a new directory for your project.

## Create Keyfile
First of all, we want to crate a key pair to use with our VMs to use SSH.
In your bwCloud overview click on 'Key Pairs' and then on 'Create Key Pair'. Name it and select 'SSH' as type.
After approving, your browser will download a private keyfile automatically. Move that keyfile to your project directory we created earlier. Open a shell and set it's permissions:

`sudo chmod 600 [your private keyfile]`

## Create Application Credentials
Unless many tutorial-pages might tell you, you can not access bwCloud by using username and password with terraform. That means you have to create environment variables.

Click on 'Identity' and then on 'Application Credentials' in your bwCloud dashboard. Create a new entry and give it only a name. After approving it should show a window with the secret and ID. Save these in a file on your computer (but make sure to include it in .gitignore). Then click on 'Download openrc file' and move that file to you project directory.

Open a shell there and type:

`source [name of the openrc file]`

Now that you have exported your environment variables, you can use Terraform without specifing any provider properties.

## Use Terraform

Create a file named 'providers.tf' with the following content:

```hc1

terraform {

  required_version = ">=1.1.9"

  required_providers {
    openstack = {
      source = "terraform-provider-openstack/openstack"
      version = ">= 1.35.0"
    }
  }
}

provider "openstack" {
}
```

You can now specify VMs and more lie the following in a separate .tf file:

```hc1

resource "openstack_compute_instance_v2" "VM-Name" {
  name            = "VM Name"
  image_name      = "the image name"
  key_pair        = "keypair-name"
  security_groups = ["default"]
  region          = "your-region (eg. 'Freiburg'"
	flavor_name = "eg. m1.small"

  network {
    name = "public"
  }
}
```
Flavors specify the size of the machine, beware of not exceeding your quota.
You can find the available flavors [here](https://www.bw-cloud.org/de/bwcloud_scope/flavors)
And the available images [here](https://www.bw-cloud.org/de/bwcloud_scope/images)
Also look up the default username of the image you chose, as we will need that in the next step.

## Test SSH Login

If the Terraform apply command was successful, you can see your instances now on your dasboard under 'Instances'.
Copy the IP address, open a shell in your project directory and type the following to ssh in your VM:

`ssh -i [name of your private keyfile] [default user]@[ip address]`