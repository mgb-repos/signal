import asyncio

from signal import iterator


class IterInstance:
    def __init__(self, manager: iterator.iter_manager.IterManager):
        self.value_queue = asyncio.Queue()

        self.manager = manager
        self.manager.register_instance(self)

        self.it = self.gen()

    def __del__(self):
        self.manager.deregister_instance(self)

    async def gen(self):
        while True:
            value = await self.value_queue.get()
            self.value_queue.task_done()
            if value is iterator.ITER_END:
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
