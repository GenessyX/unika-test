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


class Service:
    def __init__(self, server_options, cluster_options=None):
        self._server_options = server_options
        self._cluster_options = cluster_options
        self._is_cluster_mode = False if cluster_options is None else True
        self._is_master = True
        self._cluster = []

    async def start(self):
        if self._is_cluster_mode:
            if self._is_master:
                await self.start_cluster()
            else:
                await self.start_worker()
        else:
            await self.start_worker()

    async def start_worker(self):
        # TODO логика запуска обработчика запросов
        pass

    async def start_cluster(self):
        # TODO логика запуска дочерних процессов
        pass
