import asyncio
from typing import AsyncIterable, Iterable
from collections import deque


SIGNAL_INIT = {}
SIGNAL_END = {}


class IterManager:
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

    def __init__(self, it):
        self.curr_value = SIGNAL_INIT
        self.it = self._force_async(it)
        self.instances = set()

        asyncio.create_task(self.loop())

    async def loop(self):
        async for value in self.it:
            self.curr_value = value
            print("yielded %s, instances %s" % (value, len(self.instances)))
            for instance in self.instances:
                await instance.emit(value)
        await instance.emit(SIGNAL_END)

    def register_instance(self, instance):
        self.instances.add(instance)

    def deregister_instance(self, instance):
        self.instances.remove(instance)

    def spawn_instance(self):
        return IterInstance(self)

    def __aiter__(self):
        return self.spawn_instance()


class IterInstance:
    def __init__(self, manager: IterManager):
        self.manager = manager
        self.value_queue = asyncio.Queue()
        self.manager.register_instance(self)
        self.it = self.gen()
        self.buffer = deque()

    def __del__(self):
        self.manager.deregister_instance(self)

    async def gen(self):
        if self.manager.curr_value is not SIGNAL_INIT:
            yield self.manager.curr_value
        while True:
            value = await self.value_queue.get()
            self.value_queue.task_done()
            if value is SIGNAL_END:
                break
            yield value

    async def emit(self, value):
        await self.value_queue.put(value)

    def clone(self):
        return self.manager.__aiter__()

    def __aiter__(self):
        return self

    def __anext__(self):
        return self.it.__anext__()


class Signal:
    def __init__(self, it):
        if isinstance(it, IterManager):
            self.it = it.spawn_instance()
        elif isinstance(it, IterInstance):
            self.it = it.clone()
        elif isinstance(it, Signal):
            self.it = it.it.clone()
        else:
            manager = IterManager(it)
            self.it = manager.spawn_instance()

    def __aiter__(self):
        return self

    def __anext__(self):
        return self.it.__anext__()

    @staticmethod
    def _zip_iter(*signals):
        def async_it_to_task(pair):
            signal_idx, signal = pair

            async def _f():
                return signal_idx, await signal.__anext__()

            return asyncio.create_task(_f())

        async def zip_gen():
            async_its = list(map(lambda signal: signal.it.clone(), signals))
            tasks = list(map(async_it_to_task, enumerate(async_its)))
            results = [SIGNAL_INIT] * len(async_its)
            all_stopped = False
            have_all_vals = False
            while not all_stopped:
                done, pending = await asyncio.wait(
                    tasks, return_when=asyncio.FIRST_COMPLETED
                )
                all_stopped = True
                new_tasks = []

                for task in done:
                    try:
                        async_it_idx, results[async_it_idx] = task.result()
                        new_tasks.append(
                            async_it_to_task((async_it_idx, async_its[async_it_idx]))
                        )
                        all_stopped = False
                    except StopAsyncIteration:
                        pass

                if not have_all_vals and all(
                    map(lambda v: v is not SIGNAL_INIT, results)
                ):
                    have_all_vals = True
                if have_all_vals and not all_stopped:
                    yield tuple(results)

                tasks = new_tasks + list(pending)

        return zip_gen()

    @staticmethod
    def zip(*signals):
        return Signal(Signal._zip_iter(*signals))

    @staticmethod
    def _map_iter(f, *signals):
        async def map_gen():
            async for vals in Signal._zip_iter(*signals):
                yield f(vals)

        return map_gen()

    @staticmethod
    def map(f, *signals):
        return Signal(Signal._map_iter(f, *signals))

    def __add__(self, other):
        return Signal.map(lambda a, b: a + b, self, other)


async def main():
    signal_a = Signal([4, 3, 2])
    # print("wow")
    signal_b = Signal(signal_a)
    async for a in signal_a:
        print(a)
    async for a in signal_b:
        print(a)


asyncio.run(main())
