from changeprocessing import ChangeProcessingInterface
from changes import ChangesInterface


class NaiveMixtape(ChangeProcessingInterface):
    def __init__(self, mixtape_data):
        self.mixtape = mixtape_data
        self.last_playlist_id = max(item['id'] for item in self.mixtape["playlists"])

    def apply(self, changes: ChangesInterface):
        for change in changes.data:
            if change['operation'] == "add":
                self.add(change['payload'])
                continue
            if change['operation'] == "remove":
                self.remove(change['payload'])
                continue
            if change['operation'] == "modify":
                self.modify(change['payload'])
                continue

    def add(self, payload):
        payload['id'] = self.increment_id()
        self.mixtape['playlists'].append(payload)

    def remove(self, payload):
        playlist = self.__find_playlist_by_id(payload['id'])
        if playlist is not None:
            self.mixtape['playlists'].remove(playlist)
        return playlist

    def modify(self, payload):
        playlist = self.__find_playlist_by_id(payload['id'])
        if playlist is not None:
            for key in payload:
                if type(payload[key]) is list:
                    for song_id in payload[key]:
                        if self.__song_exists(song_id):
                            playlist[key].append(song_id)
                else:
                    playlist[key] = payload[key]

    def increment_id(self):
        # not thread safe
        self.last_playlist_id = int(self.last_playlist_id) + 1
        return self.last_playlist_id

    def __find_playlist_by_id(self, playlist_id):
        # brute-force lookup
        return next((playlist for playlist in self.mixtape['playlists'] if playlist['id'] == playlist_id), None)

    def __song_exists(self, song_id):
        return song_id in (song['id'] for song in self.mixtape['songs'])


class OptimizedMixtape(NaiveMixtape):
    # TODO: convert mixtape to full dictionary so that id lookups are constant time
    # TODO: change all mutating operations so that they enqueue their operation on processing queues
    # TODO: create a background thread pool for the processing queues
    # TODO: Think about ACID properties, and whether we are OK with relaxing them for the sake of performance
    # TODO: Understand read vs. write frequency, because data stores can be optimized according to access patterns

    def __init__(self, mixtape_data):
        super().__init__(mixtape_data)
