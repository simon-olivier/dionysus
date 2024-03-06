# -*- coding: utf-8 -*-
from datetime import datetime, timezone

from dioserviceupdater.versionparsers.abstractparser import (
    AbstractParser,
)


class DockerHubParser(AbstractParser):
    def get_version_alias_from_tag(self, tag_part: str, raw_data: object) -> str:
        # TODO
        raise NotImplementedError

    def get_most_recent_version(self, raw_data: object) -> str:
        most_recent_update = datetime.fromtimestamp(0, timezone.utc)
        version = str()

        for element in raw_data["results"]:
            last_updated = datetime.fromisoformat(element["last_updated"])
            if last_updated > most_recent_update:
                most_recent_update = last_updated
                version = element["name"]

        return version
