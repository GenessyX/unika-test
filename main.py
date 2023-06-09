# Класс является асинхронным TCP сервером.
# В конструктор передаются настройки сервера и кластеризации.
# Сервер может работать как в одном процессе, так и порождать для обработки запросов дочерние процессы.
# Задача дописать недостающие части и по необходимости рефакторить существующий код.
# Для реализации использовать сторонние библиотеки не нужно, достаточно стандартных библиотек python.

# Ожидается увидеть реализацию работы с межпроцессным взаимодействием в том виде, в котором Вы сможете.
# Контроль жизни дочерних процессов должен присутствовать в качестве опции.
# Должна присутствовать опция пересоздание процессов в случае падения.
# Предпочтительно реализовать различные режимы балансировки входящих запросов.
# Будет плюсом задействование статической типизации.
# Привести примеры использования готового сервиса с различными параметрами.

import asyncio
import multiprocessing
import logging
import argparse
import signal
import sys
import time
from typing import Optional
import socket
import os
import contextlib

from models import ClusterOptions, ServerOptions

DEFAULT_PORT = 8888

logging.getLogger().setLevel(logging.INFO)


class Service:
    def __init__(
        self,
        server_options: Optional[ServerOptions] = None,
        cluster_options: Optional[ClusterOptions] = None,
        name: Optional[str] = None,
        socket: Optional[socket.SocketType] = None,
    ):
        self._server_options = (
            ServerOptions(port=DEFAULT_PORT, host="127.0.0.1", restart_failed=True)
            if not server_options
            else server_options
        )
        self._cluster_options = cluster_options
        self._is_cluster_mode = False if cluster_options is None else True
        self._name = name or ("master" if self._is_cluster_mode else "worker-0")
        self._is_master = True
        self._cluster: list[multiprocessing.Process] = []
        self.alive = False
        if self._server_options.reuse_port:
            self.sock = None
        else:
            self.sock = socket if socket else self.init_socket()

    def init_socket(self):
        family = socket.AF_INET
        sock = socket.socket(family=family)
        try:
            sock.bind((self._server_options.host, self._server_options.port))
        except OSError as exc:
            logging.error(exc)
            sys.exit(1)
        return sock

    def init_signals(self):
        signal.signal(signal.SIGINT, self.handle_quit)

    def handle_quit(self, sig, frame):
        self.alive = False
        if self._is_master and self.sock:
            with contextlib.suppress(OSError):
                self.sock.close()
        time.sleep(0.1)
        sys.exit(0)

    async def start(self):
        self.loop = asyncio.get_event_loop()
        if self._is_cluster_mode:
            if self._is_master:
                await self.start_cluster()
            else:
                await self.start_worker()
        else:
            await self.start_worker()

    async def echo_server(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ):
        raw_message = await reader.readline()
        message = raw_message.decode("utf-8").strip("\n")
        if message == "quit":
            sys.exit(4)
        writer.write(raw_message + f" served by {self._name}".encode("utf-8"))
        await writer.drain()

    async def start_worker(self):
        # TODO логика запуска обработчика запросов
        logging.info(f"Starting worker: {self._name}")
        self.init_signals()
        if not self.sock:
            server = await asyncio.start_server(
                self.echo_server,
                host=self._server_options.host,
                port=self._server_options.port,
                reuse_port=True,
            )
        else:
            server = await asyncio.start_server(self.echo_server, sock=self.sock)
        await server.start_serving()
        await asyncio.Future()

    async def check_cluster(self):
        while True:
            for (index, process) in enumerate(self._cluster):
                if process.is_alive():
                    continue
                logging.error(f"{process.name} received exit code: {process.exitcode}")
                if self._server_options.restart_failed:
                    worker = self.create_worker(process.name)
                    worker.start()
                    self._cluster[index] = worker
                else:
                    del self._cluster[index]
            await asyncio.sleep(1)

    def create_worker(self, name: str):
        return multiprocessing.Process(
            name=name,
            target=start_service,
            args=(self._server_options, None, name, self.sock),
        )

    async def start_cluster(self):
        # TODO логика запуска дочерних процессов
        logging.info("Starting cluster")
        if not self._cluster_options:
            raise Exception("Provide cluster options.")
        for i in range(self._cluster_options.workers):
            worker = self.create_worker(f"worker-{i}")
            worker.start()
            self._cluster.append(worker)

        asyncio.create_task(self.check_cluster(), name="check-cluster")
        await asyncio.Future()


def start_service(
    server_options: Optional[ServerOptions] = None,
    cluster_options: Optional[ClusterOptions] = None,
    name: Optional[str] = None,
    socket: Optional[socket.SocketType] = None,
):
    service = Service(server_options, cluster_options, name, socket)
    asyncio.run(service.start())


def main():
    parser = argparse.ArgumentParser(prog="Tcp Server")
    parser.add_argument(
        "-p", "--port", type=int, default=DEFAULT_PORT, help="Specify port"
    )
    parser.add_argument(
        "--host", type=str, default="127.0.0.1", help="Specify IP to bind to"
    )
    parser.add_argument(
        "-w",
        "--workers",
        type=int,
        default=os.cpu_count(),
        help="Specify workers count",
    )
    parser.add_argument(
        "-c", "--cluster", action="store_true", help="Start server in cluster mode"
    )
    parser.add_argument(
        "-r",
        "--restart-failed",
        action="store_false",
        default=True,
        help="Disable process restart on failure",
    )
    parser.add_argument(
        "--reuse-port",
        action="store_false",
        default=True,
        help="Disable reuse port socket option",
    )
    args = parser.parse_args()

    cluster_options = ClusterOptions(workers=args.workers) if args.cluster else None

    start_service(
        ServerOptions(
            port=args.port,
            host=args.host,
            restart_failed=args.restart_failed,
            reuse_port=args.reuse_port,
        ),
        cluster_options,
    )


if __name__ == "__main__":
    main()
