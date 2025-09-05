import glob
import os
import shutil
import h5py
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
from plico.utils.timestamp import Timestamp


class InterferometerWCFClient(AbstractInterferometerClient):

    def __init__(self, ipaddr, port,
                 timeout=2,
                 name='PhaseCam6110',
                 data_path_on_4d_computer: os.PathLike=None,
                 data_path_on_local_computer: os.PathLike=None,
                 **_):
        self._name = name
        self.ipaddr = ipaddr
        self.port = port
        self._i4d = WCFInterfacer(ipaddr, port)
        self.timeout = timeout
        self.logger = Logger.of('PhaseCam6110')
        self.data_path_on_4d_computer = data_path_on_4d_computer
        self.data_path_on_local_computer = data_path_on_local_computer

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

    def capture(self,
                how_many: int,
                tn: os.PathLike=None):
        '''
        Capture raw interferometer images on disk.
        Images are saved on the 4D compute disk
        '''
        if how_many < 2:
            raise ValueError('how_many must be minimum 2 frames')

        if self.data_path_on_4d_computer is None:
            raise ValueError('data_path_on_4d_computer has not been set')
        if tn is None:
            tn = Timestamp().asNowString()
        dest_folder = os.path.join(self.data_path_on_4d_computer, "capture", tn)
        self._i4d.burst_frames_to_specific_directory(dest_folder, how_many)
        return tn

    def produce(self,
                tn: os.PathLike,
                as_masked_array: bool=True,
                remove_after_produce: bool=True):
        r'''
        Convert captured raw images into wavefront measurements.
        This fuction needs a network mount of the 4D disk
        in order to access "produce_path_on_4d_computer", which is
        seen on the local computer as "produce_path_on_local_computer"
        
        Parameters:
        tn: str or os.PathLike
          the tracking number directory containing the *.4D files to convert
        data_path_on_4d_computer: str or os.PathLike
          directory on 4D computer where captured and converted files are stored.
        data_path_on_local_computer: str or os.PathLike
          directory on the local computer where "data_path_on_4d_computer" is accessible
        
        If this routine is run on the 4D computer, "data_path_on_4d_computer"
        is the same as "data_path_on_local_computer" and can be left to the defalt value of None.

        If this routine is run on a different computer, two options are possible:
            data_path_on_4d_computer:  local path like "C:\data4d\"
            data_path_on_local_computer: network path like "\\pc4d\data4d" or local mounted path like "/data/4d_data"

        or with a network share in the other direction:
            data_path_on_4d_computer:  network path like "\\plico_pc\\data4d"
            data_path_on_local_computer: local path like "/data/4d_data"

        '''
        if self.data_path_on_4d_computer is None:
            raise ValueError('data_path_on_4d_computer has not been set')

        if self.data_path_on_local_computer is None:
            local_path = self.data_path_on_4d_computer
        else:
            local_path = self.data_path_on_local_computer
        self._i4d.set_timeout(60) # TODO should be a function of the number of images
        self._i4d.convert_raw_frames_in_directory_to_measurements_in_destination_directory(
                os.path.join(self.data_path_on_4d_computer, "produce", tn),
                os.path.join(self.data_path_on_4d_computer, "capture", tn),
            )
        filelist = glob.glob(os.path.join(local_path, "produce", tn, '*.4D'))
        images = []
        for filename in filelist:
            image = fromPhaseCamAutodetect(filename, as_masked_array=as_masked_array)
            images.append(image)
        
        if remove_after_produce:
            shutil.rmtree(os.path.join(local_path, "produce", tn))
        return np.stack(images)


def fromPhaseCam4020(h5filename: str,
                     as_masked_array: True):
    """
    Adapted from labott/opticalib/ground/osutils.py

    Convert PhaseCam4020 files from .4D to numpy array/masked array

    Parameters
    ----------
    h5filename: string
        Path of the h5 file to convert

    Returns
    -------
    ima: numpy masked array
        Masked array image
    """
    file = h5py.File(h5filename, "r")
    genraw = file["measurement0"]["genraw"]["data"]
    data = np.array(genraw)
    if as_masked_array:
        mask = np.zeros(data.shape, dtype=bool)
        mask[np.where(data == data.max())] = True
        ima = np.ma.masked_array(data * 632.8e-9, mask=mask)
    else:
        ima = data
    return ima

def fromPhaseCam6110(i4dfilename: str,
                     as_masked_array: True):
    """
    Adapted from labott/opticalib/ground/osutils.py

    Convert PhaseCam6110 files from .4D to numpy array/masked array

    Parameters
    ----------
    i4dfilename: string
        Path of the 4D file to convert

    Returns
    -------
    ima: numpy masked array
        Masked array image
    """
    with h5py.File(i4dfilename, "r") as ff:
        data = ff.get("/Measurement/SurfaceInWaves/Data")
        data = data[:]
        if as_masked_array:
            mask = np.invert(np.isfinite(data))
            image = np.ma.masked_array(data * 632.8e-9, mask=mask)
        else:
            image = data
    return image

def fromPhaseCamAutodetect(h5filename: str,
                           as_masked_array: True):
    
    file = h5py.File(h5filename, "r")
    if "measurement0" in file:
        return fromPhaseCam4020(h5filename, as_masked_array)
    else:
        return fromPhaseCam6110(h5filename, as_masked_array)

