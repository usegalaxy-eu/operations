---
title: Custom Galaxy Subdomain
---

First, choose a name. In this tutorial we'll use `example` which will be `example.usegalaxy.eu`, with a brand of "Example". Remember to change as appropriate for your name.

## Galaxy Configuration

1. add a folder named like your subdomain (here: example.usegalaxy.com) in this [directory](https://github.com/usegalaxy-eu/infrastructure-playbook/tree/master/files/galaxy/subdomains), with a subfolder called themes containing a yaml file named like your subdomain (if you are not using a theme yet, you can leave the file empty). Have a look at other subdomains to get inspiration to add custom themes or contact us for help.
~~~
└── subdomains/
    ├── ...
    └── example/
        └── themes/
            └── example.yml
~~~

2. [Add your site](https://github.com/usegalaxy-eu/infrastructure-playbook/blob/master/group_vars/sn09.yml) to the key `galaxy_themes_subdomains` . It should look something like:

    ```yaml
    - name: example
    ```

    Name is an id used in creation of several filenames internally and in the website repository. It should match `[a-z]+`

3. Add a line for your Subdomain under the `brand_by_host` key in [group_vars/gxconfig.yml](https://github.com/usegalaxy-eu/infrastructure-playbook/blob/master/group_vars/gxconfig.yml).
~~~
'example.usegalaxy.eu': Example
~~~
4. Add a line to the [global_host_filters.py.j2](https://github.com/usegalaxy-eu/infrastructure-playbook/blob/88827358fb31fe7eb5fc4c835b92a7a35afc685e/templates/galaxy/config/global_host_filters.py.j2#L147) if you want to modify which tool are shown on your subdomain

2. Make a PR with these changes

In the website repository:

1. [Create an index page like this one](https://github.com/usegalaxy-eu/website/blob/master/index-metagenomics.md) in the website repository. Above we specified that `name: example`, so you should create `index-example.md` in the root of the website repository.
2. Make a PR with these changes

## DNS Changes

1. Add your domain to [this list](https://github.com/usegalaxy-eu/infrastructure/blob/main/dns.tf#L24) under `subdomain`, and increase the `count` parameter below by one.
2. Make a PR with these changes.

### To add GxIT privileges

To run Galaxy Interactive Tools (GxIT) in your subdomain, we need to generate wildcard certificates for you. To do so the following needs to be done:

1. Create a PR, adding your domains IT wildcard to the [sn09.yml playbook](https://github.com/usegalaxy-eu/infrastructure-playbook/blob/be8d196b26f46852bc593a0d8a64e66dedde69c5/sn09.yml#L34) like done in [this PR](https://github.com/usegalaxy-eu/infrastructure-playbook/pull/916)
2. Create a PR with the CNAME records routing to `usegalaxy.eu` in the [dns.tf file](https://github.com/usegalaxy-eu/infrastructure/blob/0bd0f81bd9d5ada2ac382da415adea6a910adec1/dns.tf) by adding your domain to [this list](https://github.com/usegalaxy-eu/infrastructure/blob/0bd0f81bd9d5ada2ac382da415adea6a910adec1/dns.tf#L244-L270) under `it-subdomain`, and increase the [`count` parameter below](https://github.com/usegalaxy-eu/infrastructure/blob/0bd0f81bd9d5ada2ac382da415adea6a910adec1/dns.tf#L276) by one. Refer to [this PR](https://github.com/usegalaxy-eu/infrastructure/pull/178)
3. Expand the SSL certificate following the [manual here](https://github.com/usegalaxy-eu/operations/blob/main/ssl_certificate_expansion.md) (only EU admins can do this step, talk to them)


## Customizing Tools

1. Edit [global_host_filter.py](https://github.com/usegalaxy-eu/infrastructure-playbook/blob/master/templates/galaxy/config/global_host_filters.py.j2), you'll want to edit both functions to define appropriate values for your galaxy subdomain.

## How it works internally

There is a [nginx location directive](https://github.com/usegalaxy-eu/infrastructure-playbook/blob/d14a9497cdaeab1fabda723083fb79340cc6c7ec/templates/nginx/galaxy-main.j2#L130) that redirects the front page request from the `subdomain/welcome.html` to the file `/opt/multisite-css/$host.html`, hosted locally into the Galaxy server.

This mechanism rely on the default value of the [welcome_url](https://github.com/galaxyproject/galaxy/blob/ae89745bfc1646ae231dfd8a42b6f20ae2399f80/lib/galaxy/config/sample/galaxy.yml.sample#L1034) variable in the Galaxy configuration. If you change it, then you have to modify the nginx location directive accordingly.
