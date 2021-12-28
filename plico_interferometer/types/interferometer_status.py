from plico_interferometer.client.snapshot_entry import SnapshotEntry


class InterferometerStatus(object):

    def __init__(self,
                 name,
                 ):
        self.name = name

    def as_dict(self):
        dicto = {}
        dicto[SnapshotEntry.INTERFEROMETER_NAME] = self.name
        return dicto
