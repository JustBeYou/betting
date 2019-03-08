from multiprocessing import Manager

class Cache(object):
    cache_dict = None
    manager = None

    def init():
        if Cache.cache_dict == None:
            Cache.manager = Manager()
            Cache.cache_dict = Cache.manager.dict()

    def get_store():
        Cache.init()
        return Cache.cache_dict
