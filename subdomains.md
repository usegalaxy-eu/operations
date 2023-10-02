---
title: Custom Galaxy Subdomain
---

First, choose a name. In this tutorial we'll use `example` which will be `example.usegalaxy.eu`, with a brand of "Example". Remember to change as appropriate for your name.

## Galaxy Configuration

1. [Add your site](https://github.com/usegalaxy-eu/infrastructure-playbook/blob/master/group_vars/custom-sites.yml). It should look something like:

    ```yaml
    - name: example
      brand: Example
    ```

    Name is an id used in creation of several filenames internally and in the website repository. It should match `[a-z]+`

2. Make a PR with these changes

In the website repository:

1. [Create an index page like this one](https://github.com/usegalaxy-eu/website/blob/master/index-metagenomics.md) in the website repository. Above we specified that `name: example`, so you should create `index-example.md` in the root of the website repository.
2. Make a PR with these changes

## DNS Changes

1. Add your domain to [this list](https://github.com/usegalaxy-eu/infrastructure/blob/main/dns.tf#L24) under `subdomain`, and increase the `count` parameter below by one.
2. Make a PR with these changes.

### To add GxIT privileges

To allow or grant your domain the GxIT privileges, the following needs to be done,

1. Create a PR, adding your domains IT wildcard to the [sn06.yml playbook](https://github.com/usegalaxy-eu/infrastructure-playbook/blob/5ecffc1153fefc8f4ff1e44855ebf66a73c0593d/sn06.yml#L34) like done in [this PR](https://github.com/usegalaxy-eu/infrastructure-playbook/pull/916)
2. Create a PR with the CNAME records routing to `usegalaxy.eu` in the [dns.tf file](https://github.com/usegalaxy-eu/infrastructure/blob/0bd0f81bd9d5ada2ac382da415adea6a910adec1/dns.tf) by adding your domain to [this list](https://github.com/usegalaxy-eu/infrastructure/blob/0bd0f81bd9d5ada2ac382da415adea6a910adec1/dns.tf#L244-L270) under `it-subdomain`, and increase the [`count` parameter below](https://github.com/usegalaxy-eu/infrastructure/blob/0bd0f81bd9d5ada2ac382da415adea6a910adec1/dns.tf#L276) by one. Refer to [this PR](https://github.com/usegalaxy-eu/infrastructure/pull/178)
3. Expand the SSL certificate following the [manual here](https://github.com/usegalaxy-eu/operations/blob/main/ssl_certificate_expansion.md) (only EU admins can do this step, talk to them)


## Customizing Tools

1. Edit [global_host_filter.py](https://github.com/usegalaxy-eu/infrastructure-playbook/blob/master/templates/galaxy/config/global_host_filters.py.j2), you'll want to edit both functions to define appropriate values for your galaxy subdomain.

## How it works internally

There is a [nginx location directive](https://github.com/usegalaxy-eu/infrastructure-playbook/blob/d14a9497cdaeab1fabda723083fb79340cc6c7ec/templates/nginx/galaxy-main.j2#L130) that redirects the front page request from the `subdomain/welcome.html` to the file `/opt/multisite-css/$host.html`, hosted locally into the Galaxy server.

This mechanism rely on the default value of the [welcome_url](https://github.com/galaxyproject/galaxy/blob/ae89745bfc1646ae231dfd8a42b6f20ae2399f80/lib/galaxy/config/sample/galaxy.yml.sample#L1034) variable in the Galaxy configuration. If you change it, then you have to modify the nginx location directive accordingly.
