# -*- coding: utf-8 -*-

import logging

from dioserviceupdater.statics import (
    github_personal_token,
    github_personal_token_env_var,
)
from dioserviceupdater.registryclients import (
    HttpException,
    AuthenticationException,
    RegistryAbstractClient,
)


class GitHubClient(RegistryAbstractClient):
    _github_host = "api.github.com"
    _base_headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "Authorization": f"Bearer {github_personal_token}",
    }
    logger = logging.getLogger("dioserviceupdater.GitHubClient")

    def __init__(self):
        super().__init__(GitHubClient._github_host, GitHubClient._base_headers)
        logger = logging.basicConfig(level=logging.INFO)

        try:
            assert github_personal_token is not None
        except AssertionError:
            raise AuthenticationException(
                f"Please define environment variable {github_personal_token_env_var} with your github personnal access token"
            )

    def get_versions(self, organization: str, package_name: str) -> object:
        try:
            package_versions = self.json_request(
                "GET",
                f"/orgs/{organization}/packages/container/{package_name}/versions",
            )
        except HttpException as e:
            error_message = f"Github API error: Cannot retrieve version for package {organization}/{package_name}"

            if e.status != 404:
                self.logger.error(error_message)
                raise

            # fallback on user API if organization doesn't work
            package_versions = self.json_request(
                "GET",
                f"/users/{organization}/packages/container/{package_name}/versions",
                on_error=lambda *args: self.logger.error(error_message),
            )

        return package_versions
