#!/bin/sh

export HOME="${HOME:-/opt/galaxy}"
export VIRTUAL_ENV="${VIRTUAL_ENV:-/opt/galaxy/venv}"
export PATH="${PATH:+$PATH:}/opt/galaxy/venv/bin:/usr/local/bin:/bin:/usr/bin:/usr/local/sbin:/usr/sbin:/sbin"
export DOCUTILSCONFIG="${DOCUTILSCONFIG-''}"
export PYTHONPATH="${PYTHONPATH:+$PYTHONPATH:}/opt/galaxy/server/lib"
export GALAXY_VIRTUAL_ENV="${GALAXY_VIRTUAL_ENV:-/opt/galaxy/venv}"
export GALAXY_LIB="${GALAXY_LIB:-/opt/galaxy/server/lib}"

# Execute the Python script with all arguments passed through
python "$(dirname "$0")/container_resolvers.py" "$@"
