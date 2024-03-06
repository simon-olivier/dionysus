# -*- coding: utf-8 -*-

import http.client
import json
from typing import Callable

from dioserviceupdater import __version__


class HttpException(IOError):
    def __init__(self, status: str, *args, **kwargs):
        self.status = status
        super().__init__(*args, **kwargs)


class AuthenticationException(Exception):
    pass


class BaseHttpsClient:
    def __init__(self, host: str, session_headers: dict[str, str] = dict):
        self.host = host
        self.session_headers = {
            "User-Agent": f"python-dioserviceupdater/{__version__}",
            **session_headers,
        }
        self.connection = http.client.HTTPSConnection(host)

    @staticmethod
    def _verify_response(response: http.client.HTTPResponse):
        http_error_msg = ""

        if 400 <= response.status < 500:
            http_error_msg = f"{response.status} Client Error: {response.read()}"
        elif 500 <= response.status < 600:
            http_error_msg = (
                f"{response.status} Server Error for url: {response.read()}"
            )

        if http_error_msg:
            raise HttpException(response.status, http_error_msg)

    def json_request(
        self,
        method: str,
        url: str,
        additional_headers: dict[str, str] = dict(),
        on_error: Callable[[str], None] = lambda *args: None,
        **kwargs,
    ):
        request_headers = {**self.session_headers, **additional_headers}

        return self._internal_json_request(
            self.connection, method, url, request_headers, on_error, **kwargs
        )

    @staticmethod
    def _internal_json_request(
        connection: http.client.HTTPSConnection,
        method: str,
        url: str,
        request_headers: dict[str, str],
        on_error: Callable[[str], None] = lambda *args: None,
        **kwargs,
    ):
        connection.request(method, url, headers=request_headers, **kwargs)
        response = connection.getresponse()

        try:
            BaseHttpsClient._verify_response(response)
        except HttpException:
            on_error(url)
            raise

        try:
            content = response.read()
            return json.loads(content)
        except json.JSONDecodeError:
            on_error(url)
            raise
