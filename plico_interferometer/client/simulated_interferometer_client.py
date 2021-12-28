from plico_interferometer.client.abstract_interferometer_client import \
    AbstractInterferometerClient
from plico.utils.decorator import override, returns
from plico_interferometer.types.interferometer_status import \
    InterferometerStatus
from plico.utils.snapshotable import Snapshotable
import numpy as np


class SimulatedInterferometerClient(AbstractInterferometerClient):

    SIZE_W = 512
    SIZE_H = 480

    def __init__(self):
        self._name = 'mySimulatedInterferometer'

    @override
    def wavefront(self):
        data = np.ones()
        return np.ma.masked_array()

    @override
    def snapshot(self, prefix):
        status = self.status()
        return Snapshotable.prepend(prefix, status.as_dict())

    @override
    @returns(InterferometerStatus)
    def status(self):
        status = InterferometerStatus(
            self._name,
            )
        return status
