# Container Resolvers
This is just a brief summary of what @kysrpex found in https://github.com/usegalaxy-eu/infrastructure-playbook/pull/1904
## General
If `cache_directory` is not set, it defaults to`database/container_cache/singularity/explicit`.

## `explicit`
### Requirements
- Only works if `docker_enabled: true` and/or `singularity_enabled: true` is present in the respective destination.
- Tool wrapper must contain either `<container type="singularity">` or `<container type="docker">`.
### Behaviour
The container image is `pulled` from a registry directly, in other words, Galaxy will write an URI in the job script, *not* a path from a cached image.
If the requested container engine is not enabled, the resolver fails.
Otherwise the tool is executed using the requested container engine.
If a tool requires `type=singularity` and specifies a Docker container URI, the container is converted to `sif` on the fly.

## `explicity_singularity`
### Requirements
- Only works if `singularity_enabled: true` is present in the respective destination.
- Tool wrapper must contain either `<container type="singularity">` or `<container type="docker">`.
### Behaviour
The container image is `pulled` from a registry directly, in other words, Galaxy will write an URI in the job script, *not* a path from a cached image.
The tool is executed using Singularity, with no respect to tool wrappers specifing `<container type="docker">`.

## `cached_explicit_singularity`
### Requirements
- Only works if `singularity_enabled: true` is present in the respective destination.
- Tool wrapper must contain either `<container type="singularity">` or `<container type="docker">`.
### Behaviour
Tries to resolve the container requirement from a cache.
The tool is executed using Singularity, with no respect to tool wrappers specifing `<container type="docker">`.

## `mulled`
### Requirements
- Only works if `docker_enabled: true` is present in the respective destination.
- Tool must specify a `package` requirement
### Behaviour
Tries to resolve package requirements by computing a "mulled hash" and then searching for it in a container registry.
If successful, runs the tool in a mulled container using Docker.
`auto_install: true` is not possible, because the Images are Docker image blobs and not sif files, so they can not be stored in a "normal" filesystem.

## `cached_mulled`
### Requirements
- Only works if `docker_enabled: true` is present in the respective destination.
- Tool must specify a `package` requirement
### Behaviour
Tries to resolve package requirements by computing a "mulled hash" and then searching for it in `docker images`.
If successful, runs the tool in a mulled container using Docker and by specifiying the Docker container URI, so the image will be pulled if not present in the Docker deamon of the respective worker node.

## `mulled_singularity`
### Requirements
- Only works if `singularity_enabled: true`.
- Tool must specify a `package` requirement
### Behaviour
Tries to resolve package requirements by computing a "mulled hash" and then searching for it in a container registry.
If successful, runs the tool in a mulled container using Singularity.
If `auto_install: true`, the resolver will *always* return a URI and the job will pull the image. Additionally if the container is not on the cache, tries to cache the container.
If `auto_install: false` and if the container is not cached, the resolver returns a URI and tries to cache the container.
If `auto_install: false` and if the container is cached, the resolver returns a path to the container sif file and will *not* pull an image.

## `cached_mulled_singularity`
### Requirements
- Only works if `singularity_enabled: true`.
- Tool must specify a `package` requirement
### Behaviour
Tries to resolve package requirements by computing a "mulled hash" and then searching for it in a local cache.
If successful, runs the tool in a mulled container using Singularity.
