from dataclasses import dataclass


@dataclass
class ClusterOptions:
    workers: int


@dataclass
class ServerOptions:
    port: int
    host: str
    restart_failed: bool
