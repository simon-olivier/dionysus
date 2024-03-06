# -*- coding: utf-8 -*-

from abc import abstractmethod, ABC


class AbstractParser(ABC):
    @abstractmethod
    def get_version_alias_from_tag(self, tag_part: str, raw_data: object) -> str:
        raise NotImplementedError

    @abstractmethod
    def get_most_recent_version(self, raw_data: object) -> str:
        raise NotImplementedError
