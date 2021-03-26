from changes import ChangesInterface


class ChangeProcessingInterface:
    def apply(self, change: ChangesInterface):
        raise NotImplementedError

    def add(self, change):
        raise NotImplementedError

    def remove(self, change):
        raise NotImplementedError

    def modify(self, change):
        raise NotImplementedError

    def increment_id(self):
        raise NotImplementedError
