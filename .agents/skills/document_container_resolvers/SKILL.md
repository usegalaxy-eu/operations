---
name: "document_container_resolvers"
description: "Update the documentation of a container resolver, or document a
  new one."
metadata:
  author: José Manuel Domínguez
---

# Documenting container resolvers

This document explains to update the documentation of a container resolver (or
create it if it does not exist yet).

The documentation page for container resolvers is located at the moment in the
container_resolvers.md file.

> [!TIP]
> Always double-check the location of the container resolvers documentation
> page, it may have been moved without this skill having been updated.

The documentation page starts with an introduction, which is very unlikely to
need updates if the goal is to update/create the documentation of a container
resolver.

Rather, the corresponding section for the container resolver that is being
documented should be updated/created. There is a structure that such sections
should follow:

- A heading with the name of the container resolver, which is usually the same
  as the identifier of the container resolver.
- Some resolvers are meant to receive a list of package requirements as an
  input, while others are meant to take a container image reference and
  container engine pair (that means that the resolver result is `None` for
  different inputs). The section should start with a sentence such as "This
  resolver is meant to receive a container image reference and container engine
  pair as inputs." or "This resolver is meant to
  receive a list of package requirements as input" if the resolver is meant to
  work with only one type of input.
 - A "free text" description of the container resolver, which should explain
   what the resolver does and how it works. This description should be written
   in a similar style to that used for the other container resolvers.
 - Two tables enumerating the inputs and outputs of the container resolvers
   (see the existing tables). Read below for information on how to generate
   these tables yourself.

## Generating the input and output tables for a container resolver

This skill includes a helper script container_resolvers.sh to generate the
tables that enumerate the inputs and the outputs of the container resolvers.

```shell
usage: container_resolvers.py [-h] --config CONFIG [--container CONTAINER] [--package PACKAGE]
                              [--enabled-container-types ENABLED_CONTAINER_TYPES [ENABLED_CONTAINER_TYPES ...]] [--install]

Test Galaxy container resolvers

options:
  -h, --help            show this help message and exit
  --config CONFIG       Path to YAML file containing container resolvers config
  --container CONTAINER
                        Container specification as key=value pairs (can be specified multiple times)
  --package PACKAGE     Package specification as key=value pairs (can be specified multiple times)
  --enabled-container-types ENABLED_CONTAINER_TYPES [ENABLED_CONTAINER_TYPES ...]
                        Enabled container types (default: docker singularity)
  --install             Install containers (download/cache images if needed)
```

A few usage examples are shown below. 

```shell
(venv) galaxy@sn09:~$ /opt/galaxy/tmp/scripts/container_resolvers.sh --config /tmp/container_resolvers_test.yml --package "name=scikit-image version=0.25.2" --package "name=numpy version=2.3.5" --package "name=tifffile version=2025.5.10" --package "name=giatools version=0.1.2"
---- Tool requirements ----
Package:
 name: scikit-image
  version: 0.25.2
Package:
 name: numpy
  version: 2.3.5
Package:
 name: tifffile
  version: 2025.5.10
Package:
 name: giatools
  version: 0.1.2

ExplicitContainerResolver[] None
```

```shell
(venv) galaxy@sn09:~$ /opt/galaxy/tmp/scripts/container_resolvers.sh --config /tmp/container_resolvers_test.yml --container "identifier=quay.io/qiime2/amplicon:2026.1 type=docker" --enabled-container-types docker
---- Tool requirements ----
Container:
  identifier: quay.io/qiime2/amplicon:2026.1
  type: docker

ExplicitContainerResolver[] ContainerDescription[identifier=quay.io/qiime2/amplicon:2026.1,type=docker]
(venv) galaxy@sn09:~$ /opt/galaxy/tmp/scripts/container_resolvers.sh --config /tmp/container_resolvers_test.yml --container "identifier=quay.io/qiime2/amplicon:2026.1 type=singularity" --enabled-container-types docker
---- Tool requirements ----
Container:
  identifier: quay.io/qiime2/amplicon:2026.1
  type: singularity

ExplicitContainerResolver[] None
(venv) galaxy@sn09:~$ /opt/galaxy/tmp/scripts/container_resolvers.sh --config /tmp/container_resolvers_test.yml --container "identifier=quay.io/qiime2/amplicon:2026.1 type=docker" --enabled-container-types singularity
---- Tool requirements ----
Container:
  identifier: quay.io/qiime2/amplicon:2026.1
  type: docker

ExplicitContainerResolver[] None
(venv) galaxy@sn09:~$ /opt/galaxy/tmp/scripts/container_resolvers.sh --config /tmp/container_resolvers_test.yml --container "identifier=quay.io/qiime2/amplicon:2026.1 type=singularity" --enabled-container-types singularity
---- Tool requirements ----
Container:
  identifier: quay.io/qiime2/amplicon:2026.1
  type: singularity

ExplicitContainerResolver[] ContainerDescription[identifier=quay.io/qiime2/amplicon:2026.1,type=singularity]
(venv) galaxy@sn09:~$ /opt/galaxy/tmp/scripts/container_resolvers.sh --config /tmp/container_resolvers_test.yml --container "identifier=quay.io/qiime2/amplicon:2026.1 type=docker" --enabled-container-types docker singularity
---- Tool requirements ----
Container:
  identifier: quay.io/qiime2/amplicon:2026.1
  type: docker

ExplicitContainerResolver[] ContainerDescription[identifier=quay.io/qiime2/amplicon:2026.1,type=docker]
(venv) galaxy@sn09:~$ /opt/galaxy/tmp/scripts/container_resolvers.sh --config /tmp/container_resolvers_test.yml --container "identifier=quay.io/qiime2/amplicon:2026.1 type=singularity" --enabled-container-types docker singularity
---- Tool requirements ----
Container:
  identifier: quay.io/qiime2/amplicon:2026.1
  type: singularity

ExplicitContainerResolver[] ContainerDescription[identifier=quay.io/qiime2/amplicon:2026.1,type=singularity]
```

> [!TIP]
> Always double-check the that the usage instructions for the
> container_resolvers.sh script are up to date, they may have been changed
> without this skill having been updated.

> [!IMPORTANT]
> The script will not work if a couple of environment variables are not set
> properly. Make sure to have read the script and adjusted the environment
> variables before attempting to execute it.

The script expects the caller to provide a list of package requirements or a
container image reference and container engine pair.

> [!IMPORTANT]
> The script container_resolvers.sh requires a copy of the
> [Galaxy project code](https://github.com/galaxyproject/galaxy) to run.

> [!IMPORTANT]
> This repository documents Galaxy EU, therefore the Galaxy code should be
> retrieved from the default branch of
> [usegalaxy-eu/galaxy](https://github.com/usegalaxy-eu/galaxy).
