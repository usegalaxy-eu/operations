# Conda, (Bio)Containers and Galaxy

overview provided by @bgruening

for an overview picture, see: https://github.com/BioContainers/singularity-build-bot/blob/master/README.md#broader-context

but lets start from the beginning.

## Overview of important ecosystem components

1. [involucro](https://github.com/involucro)

   - The basis for any conversion of software packages to containers performed anywhere in the ecosystem
   - Developed and maintained by \@thrigon (Jonas Weber)
   - Can build containers (docker or singularity ones) from any kind of software package, but only the conda packaging format is relevant for this topic.
   - involucro is configurable through lua extension scripts

2. conda

   A programming language and OS-agnostic package management sytem.
   
   Conda packages are hosted at https://anaconda.org and are organized into so-called *"channels"* to avoid name conflicts.
   
   In the following, only the **bioconda** and the **conda-forge** channels are important.

3. Contributing conda packages to the conda-forge or bioconda channels

   The contribution workflow differs a lot between conda-forge and bioconda.

   These channels are managed by separate communities that have a good relationship with each other, but make their own decisions on how to organize themselves and on the contribution process.
   
   **conda-forge**
   
   On the conda-forge side, there is a dedicated github repo for development of each individual package recipe.

   The conda-forge contribution process is described at https://conda-forge.org/.

   Once a pull request against any conda-forge package's development repo gets accepted, a new version of that package gets built and deposited under the conda-forge channel at anaconda.org. No further building of artifacts happens on the conda-forge side.
   
   **bioconda**
   
   The bioconda community has organized all of their channel's package recipes as folders within a single github repo at https://github.com/bioconda/bioconda-recipes.

   The bioconda contribution workflow is described at https://bioconda.github.io/.

   When a pull request against the bioconda-recipes repo gets merged, packages touched by the PR get built and deposited under the bioconda channel at anaconda.org.

   However, more is going on in this case as described in the next section.

4. Automated container builds from bioconda

   The bioconda test framework tests new commits in any PR by
   
   1. building the corresponding conda package(s)
   2. building docker containers from those packages using involucro
      (Instead of running involucro directly bioconda accesses its functionality through the galaxy-tool-util python package maintained by the Galaxy community.)
   3. running the tests defined in the package recipes against the docker containers
   
   This process ensures that the package tests succeed in an isolated environment without silently relying on undeclared dependencies found on the host system.
   
   When a PR gets merged, the bioconda CI pushes the corresponding docker container(s), one per updated package, to https://quay.io/organization/biocontainers.
   
   These single-package containers are free to use for anybody looking for better isolation than what a conda package install of the same single package can provide.

   Detail: Note that bioconda-recipes defines a [build-fail-blacklist file](https://github.com/bioconda/bioconda-recipes/blob/master/build-fail-blacklist), for which it will never try to build packages and containers.

5. Multi-package containers

   *Single-package* containers like those built by bioconda are nice, but are not enough in cases (like for many Galaxy tool wrappers) where more than one bioconda package is needed.
   
   This situation is covered by *multi-package* containers and the [biocontainers/multi-package-containers](github.com/BioContainers/multi-package-containers) github repo is the simplest way to have those built.
   
   **Open to anyone**

   Anyone who needs a container featuring a combination of bioconda or conda-forge packages, can open a pull request against the repo, in which they add a line to the [combinations/hash.tsv](https://github.com/BioContainers/multi-package-containers/blob/master/combinations/hash.tsv).
   This line consists of the following, tab-separated elements:
   
   - a comma-separated list of all, version-pinned packages that should become included in the container
   - the identifier of the base image that the new container should be based on
   
     Currently, quay.io/bioconda/base-glibc-busybox-bash:latest is the base image that should be used unless you have very specific requirements.

   - A build number for the container
   
     This should be `0` for new containers and the next unused build number when "updating" an existing container.

   quay.io/bioconda/base-glibc-busybox-bash:latest and `0` are the defaults for base image and build number, respectively, so if you are creating a new (build number `0`) container that can use the default base image, you only need to provide the package list and can omit the other two columns.
   
   The tests of such PRs:
   
   - use the conda package management system to find the specified packages in the conda-forge or bioconda channels (prioritizing conda-forge over bioconda)
   - test the build of a docker container with the packages using involucro via the galaxy-tool-util package (analogous to what bioconda does)
   - test the build of a singularity container from the docker container
   
   When the PR gets merged:
   
   - the docker container gets uploaded to https://quay.io/organization/biocontainers
   - the singularity image gets pushed to https://depot.galaxyproject.org/singularity/
   
   **Hash-based container names**
   
   Single-package containers like those built by bioconda have `package_name:version` in their name.
   
   For multi-package containers, the biocontainers CI calculates:
   
   - a hash from the normalized, sorted package names that will become part of the container
   - another hash for the corresponding versions
   
   and builds a container with `pkg_names_hash:versions_hash` in its name.
   
   Preceeding this part is a `v1-` or `v2-` depending on which version of the hashing logic was used, and `-build_number` gets attached to the end of the name.
   
   **Used heavily by the Galaxy project**
   
   CI in [galaxyproject/planemo-monitor](https://github.com/galaxyproject/planemo-monitor) checks the repo's lists of relevant Galaxy tool development repos. If it finds new tools in any of these repos, it:
   
   - checks their requirement sections
   - calculates the hashes of those exact dependencies
   - checks against quay.io to see if a mulled container image with this hash already exists
   - if not, creates pull requests against the biocontainers/multi-package-containers under the bot account @dockerhub-toolshed.
   
     These PRs do not touch the combinations/hash.tsv file like manually created PRs, but instead create a dedicated file per container, like e.g. [here](https://github.com/BioContainers/multi-package-containers/pull/3899/changes), but when they get merged the cause docker and singularity image uploads like for manually created PRs.

   Overall, this mechanism ensures that every Galaxy tool wrapper has corresponding containers satisfying its requirements.

   **Recommended way to get containers for conda-forge packages**
   
   As said earlier conda-forge does not build containers for its packages like bioconda does. You can use the multi-package-containers machinery to build conda-forge single-package containers. Also planemo-monitor uses this to build containers for tool wrappers that specify a single conda-forge package as their only requirement. An example can be found [here](https://github.com/BioContainers/multi-package-containers/pull/3897/changes).

6. Singularity images of everything

You may have noted from the above discussion that bioconda does not build singularity images, so single-package containers for bioconda packages get pushed to quay.io in docker format, but singularity versions are not automatically produced.

This gap is filled by the [biocontainers/singularity-build-bot](https://github.com/biocontainers/singularity-build-bot) repo. This repo defines CI that runs regularly (multiple times a day and compares the containers available through https://quay.io/organization/biocontainers to those stored in singularity format on https://depot.galaxyproject.org/singularity/. It will then build missing singularity images from the corresponding docker images. Not only will this generate the singularity images for bioconda-generated docker containers, but the mechanism also provides images that might be missing due to transient issues with https://depot.galaxyproject.org/singularity/ encountered by the multi-package-containers CI.

Detail: Note however that the singularity-build-bot also has a skip.list file of hashes of containers it will never try to build.

7. Synchronizing singularity images via cvmfs

Images stored on https://depot.galaxyproject.org/singularity/ are moved to the Stratum 0 server of the Galaxy Project's public cvmfs. This is the only part of the entire ecosystem the automation of which is not public, but the end result is that any Galaxy server and also any other interested party can access all singularity images via cvmfs.
