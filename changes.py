class ChangesInterface:
    @property
    def data(self):
        raise NotImplementedError


class MixtapeChanges(ChangesInterface):
    def __init__(self, changes):
        self.data = changes

    @property
    def data(self):
        return self.__data

    @data.setter
    def data(self, changes):
        self.__data = changes
