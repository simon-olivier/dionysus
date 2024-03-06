# -*- coding: utf-8 -*-

import re
import sys

from dioserviceupdater.versionparsers.abstractparser import AbstractParser


class GitHubParser(AbstractParser):
    def get_version_alias_from_tag(self, tag_part: str, raw_data: object) -> str:
        shortest_alias: str = ""
        min_tag_length = sys.maxsize
        contains_target_tag = False
        version_pattern = re.compile(r"[0-9]+\.[0-9]+\.?[0-9]*")

        for element in raw_data:
            assert (
                "metadata" in element
                and "container" in element["metadata"]
                and "tags" in element["metadata"]["container"]
            )

            for tag in element["metadata"]["container"]["tags"]:
                if tag_part in tag:
                    contains_target_tag = True
                    break

            if contains_target_tag:
                for tag in element["metadata"]["container"]["tags"]:
                    if version_pattern.match(tag) and len(tag) < min_tag_length:
                        shortest_alias = tag
                        min_tag_length = len(tag)

        return shortest_alias

    def get_most_recent_version(self, raw_data: object) -> str:
        # TODO
        raise NotImplementedError
