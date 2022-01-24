from __future__ import annotations

from typing import Tuple
import socket

from ..log import logger


class Socket(object):
    """ Connect ADB server with socket """

    def __init__(self, server: Tuple[str, int], timeout: int) -> None:
        logger.debug(f'server: {server}, timeout: {timeout}')
        try:
            self.sock = socket.create_connection(server, timeout=timeout)
            self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        except ConnectionRefusedError:
            logger.error(f'ConnectionRefusedError: {self.server}')

    def __enter__(self) -> Socket:
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback) -> None:
        pass

    def __del__(self) -> None:
        self.close()

    def close(self) -> None:
        """ close socket """
        self.sock and self.sock.close()
        self.sock = None

    def recv_all(self, chunklen: int = 65536) -> bytes:
        data = []
        buf = bytearray(chunklen)
        view = memoryview(buf)
        pos = 0
        while True:
            if pos >= chunklen:
                data.append(buf)
                buf = bytearray(chunklen)
                view = memoryview(buf)
                pos = 0
            rcvlen = self.sock.recv_into(view)
            if rcvlen == 0:
                break
            view = view[rcvlen:]
            pos += rcvlen
        data.append(buf[:pos])
        return b''.join(data)

    def recv_exactly(self, len: int) -> bytes:
        buf = bytearray(len)
        view = memoryview(buf)
        pos = 0
        while pos < len:
            rcvlen = self.sock.recv_into(view)
            if rcvlen == 0:
                break
            view = view[rcvlen:]
            pos += rcvlen
        if pos != len:
            raise EOFError('recv_exactly %d bytes failed' % len)
        return bytes(buf)

    def recv_response(self) -> bytes:
        """ read a chunk of length indicated by 4 hex digits """
        len = int(self.recv_exactly(4), 16)
        if len == 0:
            return b''
        return self.recv_exactly(len)

    def check_okay(self) -> None:
        """ check if first 4 bytes is "OKAY" """
        result = self.recv_exactly(4)
        if result != b'OKAY':
            raise RuntimeError(self.recv_response())

    def send(self, data: bytes) -> Socket:
        """ send data to server """
        self.sock.send(data)
        return self
