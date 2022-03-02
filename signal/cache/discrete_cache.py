from datetime import datetime


class DiscreteCache:
    def __init__(self):
        pass

    def __len__(self):
        return 0

    def _assert_key_type(self, key):
        key_type = type(key)
        if key_type == int or key_type == slice or key_type == datetime:
            return key_type
        else:
            raise TypeError("Invalid cache key type: %s" % key_type)

    def _assert_index(self, idx: int):
        if idx < 0 or idx >= len(self):
            raise IndexError(
                "Cache index out of range. Cache length: %s, Index: %s"
                % (len(self), idx)
            )

    def _get_update_by_index(self, idx: int):
        self._assert_index(idx)

    def _get_update_by_timestamp(self, ts: datetime):
        return None

    def _get_updates_by_slice(self, sl: slice):
        return iter([])

    def _add_update_by_index(self, idx: int, val):
        pass

    def _add_update_by_timestamp(self, ts: datetime, val):
        pass

    def _add_updates_by_slice(self, sl: slice, oth):
        self._delete_updates_by_slice(sl)
        if type(oth) == DiscreteCache:
            for ts, val in oth._get_updates_by_slice(sl):
                self._add_update_by_timestamp(ts, val)
        else:
            raise TypeError("Invalid slice update value type: %s" % type(oth))

    def _remove_update_by_index(self, idx: int):
        pass

    def _remove_update_by_timestamp(self, ts: datetime):
        pass

    def _remove_update_by_slice(self, sl: slice):
        pass

    def __getitem__(self, key):
        key_type = self._assert_key_type(key)
        if key_type == int:
            return self._get_update_by_index(key)
        elif key_type == slice:
            return self._get_updates_by_slice(key)
        else:  # key_type == datetime:
            update = self._get_update_by_timestamp(key)
            return update[1] if update != None else None

    def __setitem__(self, key, val):
        key_type = self._assert_key_type(key)
        if key_type == int:
            self._add_update_by_index(key, val)
        elif key_type == slice:
            self._add_updates_by_slice(key, val)
        else:  # key_type == datetime:
            self._add_update_by_timestamp(key, val)

    def __delitem__(self, key):
        key_type = self._assert_key_type(key)
        if key_type == int:
            self._remove_update_by_index(key)
        elif key_type == slice:
            self._remove_updates_by_slice(key)
        else:  # key_type == datetime:
            self._remove_update_by_timestamp(key)

    def __iter__(self):
        return self

    def __next__(self):
        raise StopIteration

