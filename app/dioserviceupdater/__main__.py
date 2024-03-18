# -*- coding: utf-8 -*-

import argparse
import configparser
import copy
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import logging
import os
import re
import yaml

from dioserviceupdater.registryclients import (
    RegistryAbstractClient,
    GitHubClient,
    DockerHubClient,
)
from dioserviceupdater.versionparsers import (
    AbstractParser,
    GitHubParser,
    DockerHubParser,
)
from .statics import (
    main_compose_file,
    config_file_path,
    service_section,
    local_images,
    service_directory_path,
    output_version_file,
)


@dataclass
class DockerRepoInfo:
    repository: str
    organization: str
    package: str
    version_var: str


@dataclass
class RegistryParser:
    client: RegistryAbstractClient
    parser: AbstractParser


class SearchMethod(Enum):
    TAG_MATCH = 1
    MOST_RECENT = 2


ServicesDockerRepoInfo = dict[str, DockerRepoInfo]


def parse_command_line_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="dioserviceupdater",
        description="Find preferred version number for Dionysus active services and store them in an environment file",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print update command results to screen without modifying file",
    )
    return parser.parse_args()


def parse_compose_file_for_docker_info(compose_file: str) -> ServicesDockerRepoInfo:
    assert os.path.isfile(
        compose_file
    ), f"compose file '{compose_file}' does not exists"
    services_info = ServicesDockerRepoInfo()
    pattern = re.compile(r"^([^/]*)/([^/]*)/([^:]*):\$\{(.*)\}$")

    with open(compose_file) as stream:
        content = yaml.safe_load(stream)

        for key, value in content["services"].items():
            match = pattern.match(value["image"])
            assert (
                match is not None
            ), f"Failed to parse image for service '{key}' using regexp {pattern.pattern}"

            services_info[key] = DockerRepoInfo(
                repository=match.group(1),
                organization=match.group(2),
                package=match.group(3),
                version_var=match.group(4),
            )

    return services_info


def get_services_docker_info(
    config: configparser.ConfigParser,
) -> ServicesDockerRepoInfo:
    services_info = parse_compose_file_for_docker_info(main_compose_file)

    for service_name in config[service_section]:
        if (
            config[service_section][service_name] != "true"
            or service_name in local_images
        ):
            continue

        service_compose_file = os.path.join(
            service_directory_path, service_name, "compose.override.yml"
        )
        services_info.update(parse_compose_file_for_docker_info(service_compose_file))

    return services_info


###############################################################################
#################################### MAIN #####################################
###############################################################################
args = parse_command_line_args()
config = configparser.ConfigParser()
config.read(config_file_path)
services_docker_info = get_services_docker_info(config)
services_version: dict[str, str] = dict()
logger = logging.getLogger("dioserviceupdater")
logging.basicConfig(level=logging.INFO)

registry_parsers = {
    "ghcr.io": RegistryParser(GitHubClient(), GitHubParser()),
    # lscr currently redirect to Github so let's use its API instead
    "lscr.io": RegistryParser(GitHubClient(), GitHubParser()),
    # I didn't find a way to to authenticate to elastic docker repo so I use DockerHub instead because image is also published there
    # This is hacky and I also need to override organization for this to work
    "docker.elastic.co": RegistryParser(DockerHubClient(), DockerHubParser()),
}

default_service_config = {
    "include": "true",
    "search_method": "TAG_MATCH",
    "target_tag": "latest",
    "organization_override": None,
    "force_version": None,
}

for service_name, docker_info in services_docker_info.items():
    key = f"update.{service_name}"
    service_config = (
        {**default_service_config, **dict(config[key])}
        if key in config.sections()
        else default_service_config
    )

    if service_config["include"] != "true":
        logger.info(f"Skipping version info for {service_name} based on configuration.")
        continue

    if service_config["organization_override"] is not None:
        curated_docker_info = copy.deepcopy(docker_info)
        curated_docker_info.organization = service_config["organization_override"]
    else:
        curated_docker_info = docker_info

    try:
        registry_parser = registry_parsers[curated_docker_info.repository]
    except:
        logger.warning(
            f"Unsupported registry '{curated_docker_info.repository}' for service '{service_name}'"
        )
        continue

    if service_config["force_version"] is not None:
        services_version[service_name] = (
            f"{docker_info.version_var}={service_config['force_version']}"
        )
    else:
        service_versions = registry_parser.client.get_versions(
            curated_docker_info.organization, curated_docker_info.package
        )

        search_method = SearchMethod[service_config["search_method"]]

        if search_method == SearchMethod.TAG_MATCH:
            version = registry_parser.parser.get_version_alias_from_tag(
                service_config["target_tag"], service_versions
            )
        else:  # search_method == SearchMethod.MOST_RECENT
            version = registry_parser.parser.get_most_recent_version(service_versions)

        services_version[service_name] = f"{docker_info.version_var}={version}"

if args.dry_run:
    for service_name, version_info in services_version.items():
        print(f"{services_version[service_name]}")
else:
    if os.path.exists(output_version_file):
        os.rename(
            output_version_file,
            f'{output_version_file}.{datetime.now().strftime("%Y%m%d%H%M%S")}',
        )

    with open(output_version_file, "w") as filestream:
        filestream.write("# This is a file generated by dioserviceupdater\n")
        for service_name, version_info in services_version.items():
            filestream.write(f"{services_version[service_name]}\n")
