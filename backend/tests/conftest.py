import socket

import pytest


class NetworkAccessDuringTests(RuntimeError):
    pass


@pytest.fixture(autouse=True)
def block_network_access(monkeypatch):
    def refuse(*args: object, **kwargs: object) -> None:
        raise NetworkAccessDuringTests(
            "Tests must not open network connections; mock the transport instead"
        )

    monkeypatch.setattr(socket.socket, "connect", refuse)
    monkeypatch.setattr(socket.socket, "connect_ex", refuse)
    monkeypatch.setattr(socket, "create_connection", refuse)
