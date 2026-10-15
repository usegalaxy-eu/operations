import argparse
import os
import sys
import yaml

sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, "lib")))

from galaxy.tool_util.deps.container_resolvers.explicit import ExplicitContainerResolver, ExplicitSingularityContainerResolver, CachedExplicitSingularityContainerResolver
from galaxy.tool_util.deps.container_resolvers.mulled import CachedMulledDockerContainerResolver, CachedMulledSingularityContainerResolver, MulledDockerContainerResolver, MulledSingularityContainerResolver
from galaxy.tool_util.deps.containers import ContainerRegistry
from galaxy.tool_util.deps.dependencies import AppInfo, ToolInfo
from galaxy.tool_util.deps.requirements import ContainerDescription, DEFAULT_CONTAINER_TYPE, DEFAULT_CONTAINER_RESOLVE_DEPENDENCIES, DEFAULT_CONTAINER_SHELL, DEFAULT_REQUIREMENT_TYPE, DEFAULT_REQUIREMENT_VERSION, ToolRequirement
from galaxy.util import asbool


def parse_container_resolvers_config_dict(config_dict):
    app_info = AppInfo(
        container_resolvers_config_dict=config_dict,
        involucro_auto_init=False,
        enable_mulled_containers=True,
    )
    registry = ContainerRegistry(app_info=app_info)
    return registry.container_resolvers


def container_requirement_from_dict(container_dict):
    identifier = container_dict["identifier"]
    type = container_dict.get("type", DEFAULT_CONTAINER_TYPE)
    resolve_dependencies = asbool(container_dict.get("resolve_dependencies", DEFAULT_CONTAINER_RESOLVE_DEPENDENCIES))
    shell = container_dict.get("shell", DEFAULT_CONTAINER_SHELL)
    return ContainerDescription(
        identifier=identifier,
        type=type,
        resolve_dependencies=resolve_dependencies,
        shell=shell,
    )


def package_requirement_from_dict(package_dict):
    name = package_dict["name"]
    type = package_dict.get("type", DEFAULT_REQUIREMENT_TYPE)
    version = package_dict.get("version", DEFAULT_REQUIREMENT_VERSION)
    return ToolRequirement(name=name, type=type, version=version)


def test_resolvers(container_resolvers, containers, packages, enabled_container_types=["docker", "singularity"], install=False):
    print("---- Tool requirements ----")
    for container in containers:
        print("Container:")
        print(f"  identifier: {container['identifier']}")
        for attribute in ["type", "resolve_dependencies", "shell"]:
            if container.get(attribute):
                print(f"  {attribute}: {container[attribute]}")
    for package in packages:
        print("Package:")
        print(f" name: {package['name']}")
        for attribute in ["type", "version"]:
            if package.get(attribute):
                print(f"  {attribute}: {package[attribute]}")

    tool_info = ToolInfo(
        container_descriptions=[container_requirement_from_dict(container) for container in containers],
        requirements=[package_requirement_from_dict(package) for package in packages]
    )

    print()
    for container_resolver in container_resolvers:
        container_description = container_resolver.resolve(enabled_container_types=enabled_container_types,
                                                           tool_info=tool_info, install=install)
        print(container_resolver, container_description)


def parse_key_value_pairs(kv_string):
    items = {}
    for pair in kv_string.split():
        if '=' not in pair:
            raise argparse.ArgumentTypeError(f"Invalid key=value pair: '{pair}'")
        key, value = pair.split('=', 1)
        items[key] = value
    return items


def main():
    arg_parser = argparse.ArgumentParser(description="Test Galaxy container resolvers")
    arg_parser.add_argument(
        "--config", required=True, help="Path to YAML file containing container resolvers config"
    )
    arg_parser.add_argument(
        "--container",
        action="append",
        type=parse_key_value_pairs,
        help="Container specification as key=value pairs (can be specified multiple times)"
    )
    arg_parser.add_argument(
        "--package",
        action="append",
        type=parse_key_value_pairs,
        help="Package specification as key=value pairs (can be specified multiple times)"
    )
    arg_parser.add_argument(
        "--enabled-container-types",
        nargs="+",
        default=["docker", "singularity"],
        help="Enabled container types (default: docker singularity)"
    )
    arg_parser.add_argument(
        "--install",
        action="store_true",
        help="Install containers (download/cache images if needed)"
    )
    args = arg_parser.parse_args()

    if args.container:
        containers = args.container
    else:
        containers = []

    if args.package:
        packages = args.package
    else:
        packages = []

    if not containers and not packages:
        arg_parser.error("At least one --container or --package must be specified")

    with open(args.config) as f:
        config_dict = yaml.safe_load(f)

    container_resolvers = parse_container_resolvers_config_dict(config_dict)
    #print(container_resolvers)
    test_resolvers(container_resolvers, containers, packages, args.enabled_container_types, args.install)


if __name__ == "__main__":
    main()
