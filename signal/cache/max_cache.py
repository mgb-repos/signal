from signal.cache.discrete_cache import DiscreteCache
from datetime import datetime
from sortedcontainers import SortedList


class MaxCache(DiscreteCache):
    def __init__(self):
        super().__init__()

        def _key(x):
            return x[0]

        self.values = SortedList(key=_key)

    def __len__(self):
        return len(self.values)

    def _get_update_by_index(self, idx: int):
        self._assert_index(idx)
        return self.values[idx]

    def _get_update_by_timestamp(self, ts: datetime):
        for pair in self.values.irange_key(None, ts, reverse=True):
            return pair
        return None

    def _get_updates_by_slice(self, sl: slice):
        return self.values.irange_key(sl.start, sl.stop)

    def _add_update_by_timestamp(self, ts: datetime, val):
        self.values.add((ts, val))

    def _add_update_by_index(self, idx: int, pair):
        self._assert_index(idx)
        self.values[idx] = pair

    def _remove_update_by_timestamp(self, ts: datetime):
        for pair in self.values.irange_key(ts, ts):
            self.values.discard(pair)

    def _remove_update_by_index(self, idx: int):
        self._assert_index(idx)
        self.values.pop(idx)

    def _remove_update_by_slice(self, sl: slice):
        for pair in self._get_updates_by_slice(sl):
            self.values.discard(pair)

    def __iter__(self):
        return self.values.__iter__()

