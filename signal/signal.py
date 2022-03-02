import asyncio

from signal.iterator import *
from signal.iterator.iter_manager import IterManager
from signal.iterator.iter_instance import IterInstance


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
            results = [ITER_INITVAL] * len(async_its)
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
                    map(lambda v: v is not ITER_INITVAL, results)
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
