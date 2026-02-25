# Container Resolvers
This is a brief summary of what @kysrpex found in https://github.com/usegalaxy-eu/infrastructure-playbook/pull/1904

## General
If `cache_directory` is not set, it defaults to `database/container_cache/singularity/explicit`.

## `explicit`
### Requirements
- Only works if `docker_enabled: true` and/or `singularity_enabled: true` is set in the respective destination.
- The tool wrapper must contain either `<container type="singularity">` or `<container type="docker">`.

### Behaviour
The container image is `pulled` directly from a registry; in other words, Galaxy writes a URI in the job script, *not* a path from a cached image.
If the requested container engine is not enabled, the resolver fails.
Otherwise, the tool executes using the requested container engine.
If a tool requires `type=singularity` and specifies a Docker container URI, the container is converted to `sif` on the fly.

## `explicit_singularity`
### Requirements
- Only works if `singularity_enabled: true` is set in the respective destination.
- The tool wrapper must contain either `<container type="singularity">` or `<container type="docker">`.

### Behaviour
The container image is `pulled` directly from a registry; in other words, Galaxy writes a URI in the job script, *not* a path from a cached image.
The tool executes using Singularity, regardless of tool wrappers specifying `<container type="docker">`.

## `cached_explicit_singularity`
### Requirements
- Only works if `singularity_enabled: true` is set in the respective destination.
- The tool wrapper must contain either `<container type="singularity">` or `<container type="docker">`.

### Behaviour
The resolver attempts to resolve the container requirement from a cache.
The tool executes using Singularity, regardless of tool wrappers specifying `<container type="docker">`.

## `mulled`
### Requirements
- Only works if `docker_enabled: true` is set in the respective destination.
- The tool must specify a `package` requirement.

### Behaviour
The resolver attempts to resolve package requirements by computing a "mulled hash" and then searching for it in a container registry.
If successful, the tool runs in a mulled container using Docker.
`auto_install: true` is not possible because the images are Docker image blobs, not sif files, so they cannot be stored in a standard filesystem.

## `cached_mulled`
### Requirements
- Only works if `docker_enabled: true` is set in the respective destination.
- The tool must specify a `package` requirement.

### Behaviour
The resolver attempts to resolve package requirements by computing a "mulled hash" and then searching for it in `docker images`.
If successful, the tool runs in a mulled container using Docker by specifying the Docker container URI, so the image will be pulled if not present in the Docker daemon of the respective worker node.

## `mulled_singularity`
### Requirements
- Only works if `singularity_enabled: true`.
- The tool must specify a `package` requirement.

### Behaviour
The resolver attempts to resolve package requirements by computing a "mulled hash" and then searching for it in a container registry.
If successful, the tool runs in a mulled container using Singularity.
If `auto_install: true`, the resolver will *always* return a URI and the job will pull the image. Additionally, if the container is not in the cache, it attempts to cache the container.
If `auto_install: false` and the container is not cached, the resolver returns a URI and attempts to cache the container.
If `auto_install: false` and the container is cached, the resolver returns a path to the container sif file and will *not* pull an image.

## `cached_mulled_singularity`
### Requirements
- Only works if `singularity_enabled: true`.
- The tool must specify a `package` requirement.

### Behaviour
The resolver attempts to resolve package requirements by computing a "mulled hash" and then searching for it in a local cache.
If successful, the tool runs in a mulled container using Singularity.