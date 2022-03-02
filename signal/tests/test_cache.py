from datetime import datetime

from signal.cache import MaxCache

ts = lambda ms: datetime.utcfromtimestamp(ms)


def test_cache_getset():
    cache = MaxCache()
    cache[ts(10000)] = 10
    cache[ts(30000)] = 30
    cache[ts(20000)] = 50
    assert cache[ts(5000)] == None
    assert cache[ts(9999)] == None
    assert cache[ts(10000)] == 10
    assert cache[ts(15000)] == 10
    assert cache[ts(19998)] == 10
    assert cache[ts(20000)] == 50
    assert cache[ts(25000)] == 50
    assert cache[ts(30000)] == 30
    assert cache[ts(50000)] == 30
    assert cache[ts(99999999999)] == 30


def test_cache_slice():
    cache = MaxCache()
    cache[ts(10000)] = 10
    cache[ts(30000)] = 30
    cache[ts(20000)] = 50
    print(list(cache[ts(5000) : ts(30000)]))

