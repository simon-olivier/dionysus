# -*- coding: utf-8 -*-

import urllib

from dioserviceupdater.statics import (
    dockerhub_personal_token,
    dockerhub_personal_token_env_var,
)
from dioserviceupdater.registryclients import (
    AuthenticationException,
    RegistryAbstractClient,
)


class DockerHubClient(RegistryAbstractClient):
    _docker_host = "hub.docker.com"
    _base_headers = {
        "Accept": "application/json",
        "X-GitHub-Api-Version": "2022-11-28",
        "Authorization": f"Bearer {dockerhub_personal_token}",
    }

    def __init__(self):
        super().__init__(DockerHubClient._docker_host, DockerHubClient._base_headers)

        try:
            assert dockerhub_personal_token is not None
        except AssertionError:
            raise AuthenticationException(
                f"Please define environment variable {dockerhub_personal_token_env_var} with your dockerhub personnal access token"
            )

    def get_versions(self, organization: str, package_name: str) -> object:
        params = {
            "page_size": 20,
        }
        # Only work on the 20 first results for now
        return self.json_request(
            "GET",
            f"/v2/namespaces/{organization}/repositories/{package_name}/tags?{urllib.parse.urlencode(params)}",
        )
