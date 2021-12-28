import abc
from six import with_metaclass
from plico.utils.decorator import returns, returnsForExample
from plico_interferometer.types.interferometer_status import \
    InterferometerStatus


class AbstractInterferometerClient(with_metaclass(abc.ABCMeta, object)):

    @abc.abstractmethod
    def wavefront(self, how_many=1):
        '''
        Parameters
        -----------
        how_many: int (default=1)
            return the average of how_many measurements.

        Returns
        -------
        wavefront: ~numpy.masked.array
            wavefront map in meters

        '''
        assert False

    @abc.abstractmethod
    @returnsForExample({'MY_4D.NAME: "Runas 4D"'})
    def snapshot(self, prefix='MY_4D'):
        '''
        Parameters
        -----------
        prefix: string
            prefix to be prepended to the snapshot dict

        Returns
        -------
        snapshot: dict
            snapshot of the device to be used as FITS header
        '''
        assert False

    @abc.abstractmethod
    @returns(InterferometerStatus)
    def status(self):
        '''
        Returns
        -------
        status: InterferometerStatus
            status of the device
        '''
        assert False

# def _proposed_interface():
#     i4d = plico_interferometer.client('ip', port=port)
#     wf_image = i4d.wavefront()
#
#     # status. A given field can be InterferometerClient.NOT_AVAILABLE
#     # if the interferometer is
#     # not providing the info.
#     status = x.status()
#
#     # snapshot is like status in a dictionary form ready for FITS headers
#     dicto = x.snapshot('MY_DEV')
#     assert dicto['MY_DEV.NAME'] == 'the name of my device'
#     # and so on for each status' fields
#
#     # boh... nice to have. Need to modify config file on server side.
#     i4d.use_mask(mask)
#

