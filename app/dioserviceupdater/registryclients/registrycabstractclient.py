# -*- coding: utf-8 -*-
from abc import abstractmethod, ABC

from dioserviceupdater.registryclients import BaseHttpsClient


class RegistryAbstractClient(BaseHttpsClient, ABC):
    @abstractmethod
    def get_versions(self, organization: str, package_name: str) -> object:
        raise NotImplementedError
