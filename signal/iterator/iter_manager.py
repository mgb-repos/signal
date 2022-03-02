from typing import AsyncIterable, Iterable
from datetime import datetime
import asyncio

from signal import iterator
from signal.cache import DiscreteCache, MaxCache


class IterManager:
    """
    Given an iterator, caches its return values so that
    they may be observed at arbitrary times after initially
    being recorded, e.g. for cloning or mapping signal 
    objects.
    """

    @staticmethod
    def _force_async(it):
        if isinstance(it, AsyncIterable):
            return it.__aiter__()

        if isinstance(it, Iterable):

            async def _async_iter():
                for i in it:
                    yield i

            return _async_iter()

        raise TypeError(
            "Expected Iterable or AsyncIterable, received %s." % type(iter).__name__
        )

    def __init__(self, it, cache: DiscreteCache = None):
        self.it = self._force_async(it)
        self.instances = set()
        self.cache = MaxCache() if cache == None else cache

        asyncio.create_task(self.loop())

    async def loop(self):
        async for value in self.it:
            ts = datetime.now()
            self.cache[ts] = value
            for instance in self.instances:
                await instance.emit((ts, value))
        await instance.emit(iterator.ITER_END)

    def register_instance(self, instance):
        for pair in self.cache:
            instance.emit(pair)
        self.instances.add(instance)

    def deregister_instance(self, instance):
        self.instances.remove(instance)

    def spawn_instance(self):
        return iterator.iter_instance.IterInstance(self)

    def __aiter__(self):
        return self.spawn_instance()
