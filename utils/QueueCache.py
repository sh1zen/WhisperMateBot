from utils.utility import md5


class QueueCache:
    __slots__ = ('max_size', 'items', 'len', 'queue', 'debug')

    def __init__(self, max_size=1000):
        self.max_size = max_size
        self.debug = True
        self.items = {}
        self.queue = []
        self.len = 0

    @staticmethod
    def key(*args):
        return md5(''.join(str(arg) for arg in args))

    def has(self, name):
        if name in self.items:
            if self.debug:
                print('#cache > ' + str(self.items.get(name)))
            return self.items.get(name)

        return None

    def add(self, item, value):
        if self.len > self.max_size:
            self.items.pop(self.queue.pop(0))
            self.len -= 1

        self.len += 1
        self.queue.append(item)
        self.items.update({item: value})

    def remove(self, item):
        if item in self.items:
            return self.items.pop(item)

        return None

    def clear(self):
        self.items = {}
        self.queue = []
        self.len = 0

    def __contains__(self, item):
        return item in self.items

    def __str__(self):
        return str(self.items)

    def update(self, item, value):
        return self.items.update({item: value})
