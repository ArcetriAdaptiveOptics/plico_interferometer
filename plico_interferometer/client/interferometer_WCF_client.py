from plico_interferometer.client.abstract_interferometer_client import \
    AbstractInterferometerClient
from plico_interferometer.devices.WCF_interface_for_4SightFocus import \
    WCFInterfacer
from plico.utils.logger import Logger
from plico.utils.decorator import override
import numpy as np
from plico_interferometer.types.interferometer_status import \
    InterferometerStatus
from plico.utils.snapshotable import Snapshotable
from plico_interferometer.utils.timeout import Timeout


class InterferometerWCFClient(AbstractInterferometerClient):

    def __init__(self, ipaddr, port,
                 timeout=2,
                 name='PhaseCam6110',
                 **_):
        self._name = name
        self.ipaddr = ipaddr
        self.port = port
        self._i4d = WCFInterfacer(ipaddr, port)
        self.timeout = timeout
        self.logger = Logger.of('PhaseCam6110')

    @override
    def name(self):
        return self._name

    @override
    def wavefront(self, how_many=1):
        '''
        Parameters
        ----------
        how_many: int
            numbers of frame to acquire

        Returns
        -------
        masked_ima: numpy masked array
            image or mean of the images required
        '''
        if how_many == 1:
            width, height, pixel_size_in_microns, data_array = \
                self._i4d.take_single_measurement()
            masked_ima = self._fromDataArrayToMaskedArray(
                width, height, data_array * 632.8e-9)
        else:
            image_list = []
            for i in range(how_many):
                width, height, pixel_size_in_microns, data_array = \
                    self._i4d.take_single_measurement()
                masked_ima = self._fromDataArrayToMaskedArray(
                    width, height, data_array * 632.8e-9)
                image_list.append(masked_ima)
            images = np.ma.dstack(image_list)
            masked_ima = np.ma.mean(images, axis=2)

        return masked_ima

    def _fromDataArrayToMaskedArray(self, width, height, data_array):
        data = np.reshape(data_array, (width, height))
        idx, idy = np.where(np.isnan(data))
        mask = np.zeros((data.shape[0], data.shape[1]))
        mask[idx, idy] = 1
        masked_ima = np.ma.masked_array(data, mask=mask.astype(bool))
        return masked_ima

    @override
    def status(self):
        serial_number = self._i4d.get_system_info()
        return InterferometerStatus(serial_number)

    @override
    def snapshot(self,
                 prefix,
                 timeout_in_sec=Timeout.GETTER):
        self._logger.notice("Getting snapshot for %s " % prefix)
        return Snapshotable.prepend(prefix, self.status().as_dict())
