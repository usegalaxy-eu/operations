# Container Resolvers

> [!NOTE]
> This is a summary of what @domgz found in 
> https://github.com/usegalaxy-eu/infrastructure-playbook/pull/1904. 
>

Galaxy can run tools in [Docker](https://www.docker.com/) and
[Apptainer](https://docs.sylabs.io/guides/3.5/user-guide/introduction.html)
(former Singularity) containers.

If containers are enabled for a destination, Galaxy will try to resolve the
container
[image reference](https://docs.docker.com/engine/containers/run/#image-references)
using so-called
["container resolvers"](https://docs.galaxyproject.org/en/latest/admin/container_resolvers.html#container-resolvers-in-galaxy).
Galaxy container resolvers choose a container engine (either `docker` or
`singularity`) and attempt to find a reference for the container image. 

For example, the `explicit` container resolver simply returns the container
image reference specified in the tool wrapper, while the `explicit_singularity`
container resolver in addition forces the use of Singularity as the container
engine. Other resolvers, for example,  attempt to find a container image
reference based on the package requirements specified in the tool wrapper. Each
resolver has different behavior, tailored to a specific use-case.

Container resolvers are defined either on a per-job-destination file or
globally in a container resolver configuration file. Galaxy tries to choose a
container engine and an image reference using each resolver in the order they
are defined. If the resolver returns no reference, Galaxy proceeds to the next
resolver.

Container resolvers take as input either an existing container image reference
and container engine pair (e.g. `"identifier=quay.io/qiime2/amplicon:2026.1
type=singularity`) or a list of package requirements (e.g.
`scikit-image==0.25.2,numpy==2.3.5`). They return a container description,
which is a pair of a container image reference and a container engine (e.g.
`docker://quay.io/biocontainers/fastqc:0.12.1--hdfd78af_0 type=singularity"`).
Additionally, they can accept configuration parameters that allow to fine-tune
their behavior (e.g. some allow defining a cache directory for Apptainer
images).

This page documents the subset of container resolvers built into Galaxy that
are most interesting for production usage.

## `explicit`

This resolver is meant to receive a container image reference and container
engine pair as inputs. The resolved container image reference matches the
input reference, and it is pulled upon job execution.

In other words, Galaxy writes the container image reference in the job script,
*not* a path to a cached image. The tool executes using the requested container
engine (if enabled).

_Note:_ If a tool declares Singularity as container engine but specifies a
Docker container registry URI, then the container is converted to `sif` on the
fly by Apptainer.

**List of package requirements**

| Enabled container engines | Resolver result |
|:--------------------------|:----------------|
| docker                    | `None`          |
| singularity               | `None`          |
| docker singularity        | `None`          |

**Image reference and container engine pair**

| Requested container engine | Enabled container engines | Resolver result                                                                    |
|:---------------------------|:--------------------------|:-----------------------------------------------------------------------------------|
| docker                     | docker                    | `ContainerDescription[identifier=quay.io/qiime2/amplicon:2026.1,type=docker]`      |
| singularity                | docker                    | `None`                                                                             |
| docker                     | singularity               | `None`                                                                             |
| singularity                | singularity               | `ContainerDescription[identifier=quay.io/qiime2/amplicon:2026.1,type=singularity]` |
| docker                     | docker singularity        | `ContainerDescription[identifier=quay.io/qiime2/amplicon:2026.1,type=docker]`      |
| singularity                | docker singularity        | `ContainerDescription[identifier=quay.io/qiime2/amplicon:2026.1,type=singularity]` |

## `explicit_singularity`

This resolver is meant to receive a container image reference and container
engine pair as inputs. The resolved container image reference matches the
input reference, and it is pulled upon job execution.

In other words, Galaxy writes the container image reference in the job script,
*not* a path to a cached image. The tool executes using Singularity (if
enabled), regardless of tool wrapper declaring Docker as container engine.

**List of package requirements**

| Enabled container engines | Resolver result |
|:--------------------------|:----------------|
| docker                    | `None`          |
| singularity               | `None`          |
| docker singularity        | `None`          |

**Image reference and container engine pair**

| Requested container engine | Enabled container engines | Resolver result                                                                             |
|:---------------------------|:--------------------------|:--------------------------------------------------------------------------------------------|
| docker                     | docker                    | `None`                                                                                      |
| singularity                | docker                    | `None`                                                                                      |
| docker                     | singularity               | `ContainerDescription[identifier=docker://quay.io/qiime2/amplicon:2026.1,type=singularity]` |
| singularity                | singularity               | `ContainerDescription[identifier=quay.io/qiime2/amplicon:2026.1,type=singularity]`          |
| docker                     | docker singularity        | `ContainerDescription[identifier=docker://quay.io/qiime2/amplicon:2026.1,type=singularity]` |
| singularity                | docker singularity        | `ContainerDescription[identifier=quay.io/qiime2/amplicon:2026.1,type=singularity]`          |

## `cached_explicit_singularity`

This resolver is meant to receive a container image reference and container
engine pair as inputs. It attempts to find the referenced container image in a
cache. If that fails, then the resolved container image reference matches the
input reference, and it is pulled upon job execution.

The tool executes using Singularity (if enabled), regardless of the tool
wrapper declaring Docker as container engine.

The cache path can be configured using the `cache_directory` parameter,
managed by a `cache_directory_cacher_type` setting such as `dir_mtime`.

> [!TIP]
> See the
> ["Containers in Galaxy"](https://docs.galaxyproject.org/en/latest/admin/container_resolvers.html#parameters)
> page for more details on how the `cache_directory` and
> `cache_directory_cacher_type` configuration parameters work.

Additionally, the `install` parameter can be set to `true` so that the resolver
saves the container image to the cache directory if it is not already present
(this requires the `singularity` command to be present in the node executing
the resolver).

**List of package requirements**

| Enabled container engines | Resolver result |
|:--------------------------|:----------------|
| docker                    | `None`          |
| singularity               | `None`          |
| docker singularity        | `None`          |

**Image reference and container engine pair**

| Requested container engine | Enabled container engines | Resolver result                                                                                                                                                                                          |
|:---------------------------|:--------------------------|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| docker                     | docker                    | `None`                                                                                                                                                                                                   |
| singularity                | docker                    | `None`                                                                                                                                                                                                   |
| docker                     | singularity               | `ContainerDescription[identifier=docker://https://depot.galaxyproject.org/singularity/mulled-v2-6a2891161dcf5f35b38c6a49fff923163de7a66d%3a159a5b483a078f27b97a401b0626abac09e5f2d1-0,type=singularity]` |
| singularity                | singularity               | `ContainerDescription[identifier=https://depot.galaxyproject.org/singularity/mulled-v2-6a2891161dcf5f35b38c6a49fff923163de7a66d%3a159a5b483a078f27b97a401b0626abac09e5f2d1-0,type=singularity]`          |
| docker                     | docker singularity        | `ContainerDescription[identifier=docker://https://depot.galaxyproject.org/singularity/mulled-v2-6a2891161dcf5f35b38c6a49fff923163de7a66d%3a159a5b483a078f27b97a401b0626abac09e5f2d1-0,type=singularity]` |
| singularity                | docker singularity        | `ContainerDescription[identifier=https://depot.galaxyproject.org/singularity/mulled-v2-6a2891161dcf5f35b38c6a49fff923163de7a66d%3a159a5b483a078f27b97a401b0626abac09e5f2d1-0,type=singularity]`          |

## `mulled`

This resolver is meant to receive a list of package requirements as input. It
computes a
["mulled hash"](https://docs.galaxyproject.org/en/latest/admin/special_topics/mulled_containers.html#calculate-a-mulled-hash)
from the package requirements and searches for the corresponding container in
the [quay.io](https://quay.io/) container registry (the registry namespace is
configurable, and it defaults to `biocontainers`).

If successful, the tool runs in a mulled container using Docker (therefore, it
only works if `docker_enabled: true` is set in the respective destination).
`auto_install: true` is not possible because the images are Docker image blobs,
not sif files, so they cannot be stored in a standard filesystem.

> [!WARNING]
> This resolver is not documented yet in detail. Please contribute a
> description and its tables if you have experience with it.

## `cached_mulled`

This resolver is meant to receive a list of package requirements as input. It
computes a
["mulled hash"](https://docs.galaxyproject.org/en/latest/admin/special_topics/mulled_containers.html#calculate-a-mulled-hash)
from the package requirements and then searches for the corresponding container
in the local Docker cache, i.e. `docker images`.

If successful, the tool runs in a mulled container using Docker by specifying
the Docker container URI (therefore, it only works if `docker_enabled: true` is
set in the respective destination). The image will be pulled if not present in
the Docker daemon of the respective worker node.

> [!WARNING]
> This resolver is not documented yet in detail. Please contribute a
> description and its tables if you have experience with it.

## `mulled_singularity`

This resolver is meant to receive a list of package requirements as input. The
resolver computes a
["mulled hash"](https://docs.galaxyproject.org/en/latest/admin/special_topics/mulled_containers.html#calculate-a-mulled-hash)
from the package requirements and searches for the corresponding container in
the [quay.io](https://quay.io/) container registry (the registry namespace is
configurable, and it defaults to `biocontainers`).

- If `auto_install` is `false` and the container is in the cache directory,
  the resolver returns the path to the cached `.sif` file. If it is not in the
  cache directory, then it returns a `docker://` URI, e.g.
  `docker://quay.io/biocontainers/fastqc:0.12.1--hdfd78af_0`.
- Otherwise, if `auto_install` is `true`, the resolver returns the `docker://`
  URI, even if the container is present in the cache directory.

In situations in which `install=True` (e.g. during job preparation or when
using the admin panel), the resolver will attempt to download the container to
the cache, **regardless of the value of `auto_install`**!

_Note_: this requires the `singularity` command to be present in the node
executing the resolver.

The cache path can be configured using the `cache_directory` parameter,
managed by a `cache_directory_cacher_type` setting such as `dir_mtime`.

> [!TIP]
> See the
> ["Containers in Galaxy"](https://docs.galaxyproject.org/en/latest/admin/container_resolvers.html#parameters)
> page for more details on how the `cache_directory` and
> `cache_directory_cacher_type` configuration parameters work.

Additionally, the `install` parameter can be set to `true` so that the resolver
saves the container image to the cache directory if it is not already present
(this requires the `singularity` command to be present in the node executing
the resolver).

**List of package requirements**

| Enabled container engines | Resolver result                                                                             |
|:--------------------------|:--------------------------------------------------------------------------------------------|
| docker                    | `None`                                                                                      |
| singularity               | `ContainerDescription[identifier=docker://quay.io/biocontainers/fastqc:0.12.1--hdfd78af_0,type=singularity]` |
| docker singularity        | `ContainerDescription[identifier=docker://quay.io/biocontainers/fastqc:0.12.1--hdfd78af_0,type=singularity]` |

**Image reference and container engine pair**

| Requested container engine | Enabled container engines | Resolver result |
|:---------------------------|:--------------------------|:----------------|
| docker                     | docker                    | `None`          |
| singularity                | docker                    | `None`          |
| docker                     | singularity               | `None`          |
| singularity                | singularity               | `None`          |
| docker                     | docker singularity        | `None`          |
| singularity                | docker singularity        | `None`          |

## `cached_mulled_singularity`

Like `mulled_singularity`, this resolver is meant to receive a list of package
requirements as input, and resolves them by computing a
["mulled hash"](https://docs.galaxyproject.org/en/latest/admin/special_topics/mulled_containers.html#calculate-a-mulled-hash)
from the package requirements. Unlike `mulled_singularity`, it only searches
for the corresponding container in the local cache directory, which can be
configured with the `cache_directory` parameter and managed by a
`cache_directory_cacher_type` such as `dir_mtime`. It never pulls or caches
anything itself: it returns the path to the cached container if it is in the
cache directory, and `None` if the container is not in the cache directory.

> [!TIP]
> See the
> ["Containers in Galaxy"](https://docs.galaxyproject.org/en/latest/admin/container_resolvers.html#parameters)
> page for more details on how the `cache_directory` and
> `cache_directory_cacher_type` configuration parameters work.

**List of package requirements**

| Enabled container engines | Resolver result                                                                             |
|:--------------------------|:--------------------------------------------------------------------------------------------|
| docker                    | `None`                                                                                      |
| singularity               | `ContainerDescription[identifier=/cvmfs/singularity.galaxyproject.org/all/fastqc:0.12.1--hdfd78af_0,type=singularity]` |
| docker singularity        | `ContainerDescription[identifier=/cvmfs/singularity.galaxyproject.org/all/fastqc:0.12.1--hdfd78af_0,type=singularity]` |

**Image reference and container engine pair**

| Requested container engine | Enabled container engines | Resolver result |
|:---------------------------|:--------------------------|:----------------|
| docker                     | docker                    | `None`          |
| singularity                | docker                    | `None`          |
| docker                     | singularity               | `None`          |
| singularity                | singularity               | `None`          |
| docker                     | docker singularity        | `None`          |
| singularity                | docker singularity        | `None`          |

## `build_mulled`

> [!WARNING]
> This resolver is not documented yet. Please contribute a description and its
> tables if you have experience with it.

## `build_mulled_singularity`

> [!WARNING]
> This resolver is not documented yet. Please contribute a description and its
> tables if you have experience with it.
