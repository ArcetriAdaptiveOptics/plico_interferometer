"""SHSWorks TCP/IP Client
Contains wrapper class for SHSWorks 12.000.1 TCP/IP commands.
Target version: Python 3.6.7
Google Python Style Docstrings
"""
from pathlib import Path
from socket import AF_INET, SOCK_STREAM, socket
from typing import Union

from .answer_processing import (_cam_par_dict_from_str, _get_result,
                                _split_answer, _to_number, process_evaluation,
                                read_out_bool, read_out_cam_settings,
                                read_out_list, read_out_number,
                                read_out_numbers, read_out_parameter,
                                read_out_stats)
from .shsworks_error import (SHSWorksError, UnexpectedAnswerFormatError,
                             UnknownCommandError)


class ShsClient():
    """Wrapper class for SHSWorks 12.000.1 TCP/IP control
    """
    def __init__(self, server_port=29800, quiet=False, server_host='localhost'):
        """Constructor for a ShsClient object.

        Args:
            server_port (int, optional): Server port. Defaults to 29800.
            server_host (str, optional): Server host. Defaults to 'localhost'.
        """
        self.server_port = server_port
        self.server_host = server_host
        self._sockobj = socket(AF_INET, SOCK_STREAM)
        self._is_open = False
        self.sent_last = ''
        self.jid = 0
        self.quiet = quiet
        self.MAX_COMMAND_LENGTH = 4096

    def __repr__(self):
        return ("TCP/IP client object for communication with SHSWorks."
                f"\nServer port: {self.server_port}"
                f"\nServer host: '{self.server_host}'"
                f"\nsocket object: {self._sockobj}"
                f"\njob ID: {self.jid}"
                f"\nConnection established: {self._is_open}")

    def __del__(self):
        """ends connection.
        """
        self._is_open = False
        self._sockobj.close()

    def __enter__(self):
        """Magic method required to be able to use the with statement.
        """
        self.connect()
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        """Magic method required to be able to use the with statement.
        """
        if self._is_open:
            self.close()

    def connect(self):
        """connects to SHSWorks.

        Returns:
            str: Answer string from SHSWorks.

        Raises:
            ConnectionRefusedError
        """
        try:
            if not self._is_open:
                self._sockobj = socket(AF_INET, SOCK_STREAM)
                self._sockobj.connect((self.server_host, self.server_port))
                self._is_open = True
                if not self.quiet:
                    print('TCP/IP connection to SHSWorks established.')
        except ConnectionRefusedError as cre:
            raise ConnectionRefusedError(
                'Please check if SHSWorks is running, TCP/IP is enabled'
                f' and port is {self.server_port}') from cre

    def close(self):
        """Calls __del__() and prints a statement.
        """
        if not self.quiet:
            print('Connection to SHSWorks closed.')
        self.__del__()

    def send_command(self, mid, *args):
        """Sends the command with MID and agruments to SHSWorks.
        JID is incremented automatically.
        Reconnects client if necessary.
        Closes live-mode if necessary.

        Args:
            mid (int): task ID
            args (str): will be converted to str and separated by pipes.

        Returns:
            answer (str): answer from SHSWorks.

        Raises:
            ConnectionResetError: if SHSWorks is closed during command
            UnknownCommandError: if SHSworks doesn't know the command
            SHSWorksError: if the error code in the answer string != 1
            UnexpectedAnswerFormatError: if answer string is not as expected
        """
        if not isinstance(mid, int):
            raise TypeError('mid must be of type int.')
        message = self._command_str(mid, *args)
        self.jid += 1
        if len(message) > self.MAX_COMMAND_LENGTH:
            raise ValueError(
                f'The maximum command length is {self.MAX_COMMAND_LENGTH}.'
                f' The command {message} is too long.')
        if not self._is_open:
            self.connect()
        try:
            answer = self._send(message)
        except ConnectionResetError as cre:
            raise ConnectionResetError(
                f'Connection lost during method {self._last_command()}') from cre
        if any(['Unknown Command' in answer,
                'Unknown command' in answer]):
            raise UnknownCommandError(
                f'Unknown command: {self._last_command()}')
        if 'SHSWorks blocked (live or static mode)!' in answer:
            self.close_live()
            return self.send_command(mid, *args)
        answer_split = _split_answer(answer)
        error_code = answer_split[3]
        if error_code[0:2] != '1=':  # Error Code 1=Ok!
            warning_message = error_code
            try:
                warning_message += ' ' + answer_split[4]
            except IndexError:
                pass
            raise SHSWorksError(
                f'during method {self._last_command()}\n{warning_message}')
        return answer

    def _send(self, string):
        """sends string to SHSWorks and returns result as decoded string.
        """
        self.sent_last = string
        self._sockobj.send(string.encode(encoding='cp1252'))
        answer = b''
        while answer[-2:] != b'\r\n':
            answer += self._sockobj.recv(512)
        return answer.decode(encoding='cp1252')

    def _command_str(self, mid: int, *args):
        """returns string that can be passed to self.send(str)

        Args:
            mid (int): task ID
            args: will be converted to str and separated by |.

        Returns:
            str: formatted as a TCP/IP command for SHSWorks.
        """
        message = 'Start|{0:03d}|{1:02d}'.format(self.jid, mid)
        for arg in args:
            message += '|' + str(arg)
        if len(args) == 0:
            message += '|'
        message += '\r\n'
        return message

    def _last_command(self):
        """returns string with last method used and the exact message sent
        used for error messages.
        """
        s = _split_answer(self.sent_last)
        mid = int(s[2])
        return f'{self.COMMANDS[mid]}(): {self.sent_last[:-2]}'

    # Commands sorted by MID
    # "00"
    def test(self) -> str:
        """ Test; a standard answer is returned without performing frame
        reading or evaluation.

        Returns:
            str: Answer string from SHSWorks.
        """
        return self.send_command(0)

    # "01"
    def open_live(self) -> str:
        """ Opens SHSWorks Live Video; has to be closed with close_live()
        before other commands can be executed.

        Returns:
            str: Answer string from SHSWorks.
        """
        return self.send_command(1)

    # "02"
    def grab_org(self) -> str:
        """ Take frame from camera; original part of active data field
        (default is Measurement field).
        Use method select_field() to select active field.

        Returns:
            str: Answer string from SHSWorks.
        """
        return self.send_command(2)

    # "03"
    def grab_ref(self) -> str:
        """ Take frame from camera; reference part of active data field
        (default is Measurement field).
        Use method select_field() to select active field.

        Returns:
            str: Answer string from SHSWorks.
        """
        return self.send_command(3)

    # "04"
    def evaluation(self) -> dict:
        """ Perform evaluation in SHSWorks

        Returns:
            dict: {pf_index: pf_value} dictionary with the
            pass-fail indices as keys and their values as values.

        Raises:
            SHSWorksError: in case an error code != 1 is returned from SHSWorks.

        Example:
            >>> with ShsClient() as c:
            >>>     result = c.evaluation()
            >>>     names_dict = c.get_pf_names_dict()
            >>> for pfi, value in result.items():
            >>>     name = names_dict[pfi]
            >>>     print(f'{name} = {value}')
        """
        answer = self.send_command(4)
        pf_indices = self.get_pf_indices()
        return process_evaluation(answer, pf_indices)

    # "05"
    def load_setup(self, setup_name: str) -> str:
        """ Load parameter set in SHSWorks (according to 2.5.9)
        set-up with name 'test' is loaded as follows: 'Start|435321|05|test'.

        Args:
            setup_name (str):
                string, must coincide with an existing setup in SHSWorks

        Returns:
            str: Answer string from SHSWorks.
        """
        if not isinstance(setup_name, str):
            raise TypeError('setup_name must be of type str.')
        return self.send_command(5, setup_name)

    # "06"
    def import_par(self, par_name) -> str:
        """ Import parameter set from file (according to manual chapter 2.5.11);

        Args:
            par_name (str / Path):
                Since SHSWorks version 11.22, the command
                also accepts full paths. In case just the name is provided,
                the parameter file has to be stored in the sub folder "config"
                of the SHSWorks program directory if no full path is provided.

        Returns:
            str: Answer string from SHSWorks.

        Example:
            >>> # load parameter-file with name "test.par" in SHSWorks config directory
            >>> with ShsClient() as c:
            >>>     c.import_par('test.par')
        """
        if not (isinstance(par_name, str) or isinstance(par_name, Path)):
            raise TypeError('par_name must be str or Path.')
        return self.send_command(6, str(par_name))

    # "07"
    def get_pf_indices(self) -> list:
        """ Request ID numbers of the Passfail items used.
        This is useful to identify which values are returned in the answer
        string when an evaluation is performed (see "PF_STR" in 6.1.1.2).

        Returns:
            list: List containing indices of all the used pass fail items.
        """
        answer = self.send_command(7)
        pf_indices = read_out_numbers(answer)
        if pf_indices == []:
            self._check_pass_fail_config()
        return pf_indices

    # "08"
    def close_live(self) -> str:
        """ Stop live dialog

        Returns:
            str: Answer string from SHSWorks.
        """
        return self.send_command(8)

    # "09"
    def get_cam_settings(self) -> dict:
        """ Retrieve camera settings together with the tokens that can be
        used to set the parameters via TCP/IP.
        The parameters are sent for SHS and if present also for a VCC.

        Returns:
            dict: Dictionary with keys 'SHS' [and 'VCC' if there is one]
            containing the keys::

                {'BUS': the bus/grabber number,
                'CAM': the camera number,
                'TRI': the trigger mode,
                'ASH': the Autoshutter function. "0" is off, "1" is on,
                'AVE': the frames averaged. Valid values are 1, 2, 4, 8, …, 1024,
                'SHU': shutter time in microseconds,
                'BRI': the "Brightness" parameter,
                'GAI': the "Gain" parameter,
                'TEM': camera temperature for cameras which have an internal temperature sensor}

        Example:
            >>> with ShsClient() as c:
            >>>     camSettings = c.get_cam_settings()
            >>>     print(camSettings['SHS']['AVE'])
            8
            >>> print(camSettings['VCC']['GAI'])
            1.0
        """
        answer = self.send_command(9)
        return read_out_cam_settings(answer)

    # "10"
    def set_cam_setting(self, cam: str, setting: str, value) -> str:
        """Set camera parameters using the tokens.

        Args:
            cam (str): 'SHS' or 'VCC'
            setting (str): setting to be set. Allowed values::

                'BUS': the bus/grabber number,
                'CAM': the camera number,
                'TRI': the trigger mode,
                'ASH': the Autoshutter function. "0" is off, "1" is on,
                'AVE': the frames averaged. Valid values are 1, 2, 4, 8, …, 1024,
                'SHU': shutter time in microseconds,
                'BRI': the "Brightness" parameter,
                'GAI': the "Gain" parameter

            value (float or int): value to be set.

        Returns:
            str: Answer string from SHSWorks.

        Example:
            >>> with ShsClient() as c:
            >>>     c.set_cam_setting('SHS', 'AVE', 8)
        """
        setting_list = ['BUS', 'CAM', 'TRI', 'ASH',
                        'AVE', 'SHU', 'BRI', 'GAI', 'TEM']
        if setting not in setting_list:
            raise KeyError(f"The token {setting} is not valid. Allowed values:"
                           " 'BUS', 'CAM', 'TRI', 'ASH', 'AVE', 'SHU',"
                           " 'BRI', 'GAI', 'TEM'")
        if cam not in ['SHS', 'VCC', 'SVC']:
            raise KeyError(f'{cam} does not correspond to a camera.'
                           ' Allowed values are "SHS" or "VCC".')
        return self.send_command(10, f"{cam}:{setting}={value}")

    # "11"
    def tilt_cal_org(self) -> str:
        """Store current position of the absolute tilt calculation (original part)
        as calibration position.

        Returns:
            str: Answer string from SHSWorks.
        """
        return self.send_command(11)

    # "12"
    def tilt_cal_ref(self) -> str:
        """Store current position of the absolute tilt calculation (reference part)
        as calibration position.
        Works only when "Calibration/Positions of spots of reference" is active.

        Returns:
            str: Answer string from SHSWorks.
        """
        return self.send_command(12)

    # "13"
    def import_spot_data(self, path) -> str:
        """ Import spot data.

        Args:
            path(str / Path): full path of text file.

        Returns:
            str: Answer string from SHSWorks.

        Corresponds to:
            "File/Import spot data…".
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"The specified path does not exist: {path}")
        return self.send_command(13, path)

    # "14"
    def export_spot_data(self, path) -> str:
        """ Export spot data.

        Args:
            path(Path or str): full path of text file.

        Returns:
            str: Answer string from SHSWorks.

        Corresponds to:
            File/Export spot data…
        """
        path = Path(path)
        return self.send_command(14, path)

    # "15"
    def eval_spot_data(self) -> dict:
        """ Evaluation from spot data.

        Returns:
            dict: {pf_index: pf_value}, analogously to evaluation()

        Corresponds to:
            Edit/Evaluation/From spot data
        """
        answer = self.send_command(15)
        pf_indices = self.get_pf_indices()
        return process_evaluation(answer, pf_indices)

    # "16"
    def select_field(self, fieldID: int) -> str:
        """ Select active data field (for reading of camera frames).
        After that use command grab_org() = TCP/IP command '02' to read a
        frame into the original part of that field.

        Args:
            fieldID (int): ID number of the field to be selected.
                Field IDs in SHSWorks::

                    1 – 32: fields of the AUX group
                    33: Measurement field (SHS)
                    34: Dark measurement field
                    35: Meas. - dark meas.
                    36: Vision control camera (VCC)
                    37: VCC processed
                    38: Spot displacement x
                    39: Spot displacement y
                    40: Power density
                    41: Error function
                    42: Wave-front field
                    43: Corr. wave-front field
                    44: Zernike evaluation
                    45: Power map
                    46: Point spread function (PSF)
                    47: Modulation transfer function (MTF)
                    48: Side view camera (SVC)
                    49: Moiré

        Returns:
            str: Answer string from SHSWorks
        """
        if not isinstance(fieldID, int):
            raise TypeError('fieldID must be of type int.')
        return self.send_command(16, fieldID)

    # "17"
    def delete_fields(self) -> str:
        """Deletes all fields both of the SHS group as well as of the AUX group.

        Returns:
            str: Answer string from SHSWorks.
        """
        return self.send_command(17)

    # "18"
    def center_sample(self) -> str:
        """Command for centering the sample in Live-mode. Only possible with
        PI-motorisation functionality of SHSInspect ophthalmic and appropriate
        dongle license.

        Returns:
            str: Answer string from SHSWorks.
        """
        return self.send_command(18)

    # "19"
    def get_center_sample_state(self) -> str:
        """Command for status request of centering the sample in Live-mode.
        Only possible with PI-motorisation functionality of SHSInspect ophthalmic
        and appropriate dongle license.

        Returns:
            str: Answer string from SHSWorks.
        """
        return self.send_command(19)

    # "20"
    def get_pf_names(self) -> list:
        """Retrieve the names of the Passfail items which are switched on.

        Returns:
            list: List containing pass fail item names (strings).
        """
        answer = self.send_command(20)
        pf_names = read_out_list(answer)
        if pf_names == []:
            self._check_pass_fail_config()
        return pf_names

    # "21"
    def get_shsworks_version(self) -> str:
        """ Retrieve version information of SHSWorks.

        Returns:
            str: SHSWorks version in format "12.000.1 (SVN1178) (September 8 2020)"
        """
        answer = self.send_command(21)
        return _get_result(answer)

    # "22"
    def get_first_zernike_index(self) -> int:
        """Retrieve index of first Zernike coefficient in the Passfail list.

        Returns:
            int: index of first Zernike coefficient in the Passfail list
        """
        answer = self.send_command(22)
        return int(_get_result(answer))

    # "23"
    def get_number_of_zernikes(self) -> int:
        """Retrieve number of Zernike coefficients in the Passfail list.

        Returns:
            int: number of Zernike coefficients in the Passfail list.
        """
        answer = self.send_command(23)
        return int(_get_result(answer))

    # "24"
    def get_pf_values(self) -> list:
        """Retrieve the values of the last Passfail evaluation.
        Use in combination with `get_pf_indices()` or `get_pf_names()`

        Returns:
            list: List containing all active passfail values as int or float.

        Raises:
            UserWarning: if Passfail evaluation is turned off.
        """
        answer = self.send_command(24)

        values = read_out_numbers(answer)
        if values == []:
            self._check_pass_fail_config()
        return values

    # "25"
    def get_pf_result(self) -> bool:
        """Retrieve the last total result of the Passfail evaluation

        Returns:
            bool: False = fail, True = pass
        """
        answer = self.send_command(25)
        return read_out_bool(answer)

    # "26"
    def get_par(self, par: str) -> Union[str, float, int, Path]:
        """Retrieve value of parameter par

        Args:
            par (str): name of SHSWorks parameter.

        Returns:
            Value of parameter par as the corresponding datatype.
        """
        answer = self.send_command(26, par)
        value = read_out_parameter(par, answer)
        if value == '':
            return value
        if par in ['cpOperator', 'cpSampleSerialNumber', 'cpSampleType']:
            return value
        if par in ['cpAPP_ImgProc_DXFFile', 'cpRAYFile']:
            return Path(value)
        return _to_number(value)

    # "27"
    def set_par(self, par: str, value) -> str:
        """ Set the value of an individual parameter.
        The names of the parameters are described in manual section 3.4.1.

        Args:
            par (str): parameter name
            value (number or str): valid value for the parameter.

        Returns:
            str: Last part of answer string from SHSWorks.

        Example:
            >>> with ShsClient() as c:
            >>>     # sets the type of reconstruction to LSQ fit.
            >>>     c.set_par('nRECType', 1)

        """
        answer = self.send_command(27, f"{par}={value}")
        read_out_parameter(par, answer)  # check answer
        return answer

    # "28"
    def get_pf_item_value(self, pf_index: int) -> Union[float, int]:
        """ Retrieve value of a specific Passfail item

        Args:
            pfno (int): index of the desired pass fail item.

        Returns:
            str: Answer string from SHSWorks.

        Example:
            >>> with ShsClient() as c:
            >>>     zernikeRMS = c.get_pf_item_value(6)
        """
        if not isinstance(pf_index, int):
            raise TypeError("pfno must be of type int.")
        answer = self.send_command(28, pf_index)
        result_str = _get_result(answer)
        return _to_number(result_str)

    # "29"
    def get_pf_item_result(self, pf_index: int) -> bool:
        """Retrieve Passfail result (0=fail or 1=pass) of a specific Passfail item

        Args:
            pf_index (int): index of the desired pass fail item.

        Returns:
            bool: True means the item passes, False means fail.

        Example:
            >>> # reports if Passfail item 6 (Zernike RMS) is "0" or "1"
            >>> # and thus "Fail" or "Pass".
            >>> with ShsClient() as c:
            >>>     c.get_pf_result(6)
        """
        answer = self.send_command(29, pf_index)
        return read_out_bool(answer)

    # "30"
    def load_file(self, path: Union[Path, str], field_part: str = None) -> str:
        r"""Load file.

        Args:
            path (Path or str): Supported file types are big, bix, shw, shz,
                txt, sha. Full path and filename need to be specified.
            field_part (str):  must be 'BOTH', 'ORG', or 'REF'
                For BIG and TXT "BOTH" is a synonym for "ORG"
                which is also the default if no parameter is added.

        Examples:
            >>> with ShsClient() as c:
            >>>     shz_path = Path(r"c:\temp\collimator.shz")
            >>>     c.load_file(shz_path)  # loads workspace.
            >>>
            >>>     bix_path = Path(r"c:\temp\reference.bix")
            >>>     # loads ORG part of bix into REF part.
            >>>     c.load_file(bix_path, 'REF')


        Returns:
            (str)  # Answer string from SHSWorks.

        Raises:
            FileNotFoundError  # in case path does not exist.
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f'Specified path does not exist: {path}')
        if path.suffix not in ['.big', '.bix', '.shw', '.shz', '.txt', '.sha']:
            raise IOError(f"Invalid SHSWorks extension: {path.suffix}")
        if len(str(path)) > 258:
            raise ValueError(f'The specified path is too long:\n {path}')
        if field_part is None:
            return self.send_command(30, path)
        else:
            if path.suffix in ['.shw', '.shz', '.sha']:
                raise ValueError('It is not possible to specify the field part'
                                 f' for the file type {path.suffix}')
            if field_part not in ['REF', 'ORG', 'BOTH']:
                raise ValueError("field_part must be 'REF', 'ORG' or 'BOTH',"
                                 f" not {field_part}")
            return self.send_command(30, path, field_part)

    # "31"
    def save_file(self, path: Union[Path, str], field_part: str = None) -> str:
        r"""Save measurement to file.

        Args:
            path (Path or str): Supported file types are big, bix, shw, shz, txt,
                sha. Full path and filename need to be specified.
            field_part (str): must be 'BOTH', 'ORG', or 'REF'

        Returns:
            str: Answer string from SHSWorks.

        Example:
            >>> with ShsClient() as c:
            >>>     out_path = Path(r"c:\temp\collimator.bix")
            >>>     c.save_file(out_path, 'REF')
            >>>     # saves the reference field part of the selected field.

        """
        path = Path(path)
        if path.suffix not in ['.big', '.bix', '.shw', '.shz', '.txt', '.sha']:
            raise IOError(f"Invalid extension: {path.suffix}")
        if field_part is None:
            return self.send_command(31, path)
        else:
            if path.suffix in ['.shw', '.shz', '.sha']:
                raise ValueError('It is not possible to specify the field part'
                                 f' for the file type {path.suffix}')
            if field_part not in ['REF', 'ORG', 'BOTH']:
                raise ValueError("field_part must be 'REF', 'ORG' or 'BOTH',"
                                 f" not {field_part}")
            return self.send_command(31, path, field_part)

    # "32"
    def set_output_path(self, path: Union[Path, str]) -> str:
        """Set path for post evaluation file(s).

        Corresponds to the setting:
            Extras/Post evaluation steps…/Auto save and print/Storage path.

        Example:
            >>> with ShsClient() as c:
            >>> c.set_output_path("c:\\temp")  # sets the path to "C:\\temp".
        """
        path = Path(path)
        if not path.is_dir():
            raise NotADirectoryError('path must be a directory.')
        return self.send_command(32, path)

    # "33"
    def set_output_name(self, name: str) -> str:
        """Set base filename for post evaluation file(s).

        Corresponds to the setting:
            Extras/Post evaluation steps…/Auto save and print/base filename.

        Example:
            >>> with ShsClient() as c:
            >>>     c.set_output_name("measurement")
        """
        if not isinstance(name, str):
            raise TypeError('output name must be of type string')
        return self.send_command(33, name)

    # "34"
    def copy_data_from_to(self, from_field: int, to_field: int) -> str:
        """Copy field data from field to field.
        Useful to move data between SHS and AUX fields.

        Args:
            from_field (int): number of field from which data are copied.
                Field IDs in SHSWorks::

                    1 – 32: fields of the AUX group
                    33: Measurement field (SHS)
                    34: Dark measurement field
                    35: Meas. - dark meas.
                    36: Vision control camera (VCC)
                    37: VCC processed
                    38: Spot displacement x
                    39: Spot displacement y
                    40: Power density
                    41: Error function
                    42: Wave-front field
                    43: Corr. wave-front field
                    44: Zernike evaluation
                    45: Power map
                    46: Point spread function (PSF)
                    47: Modulation transfer function (MTF)
                    48: Side view camera (SVC)
                    49: Moiré
            to_field (int): number of field to which data are copied

        Example:
            >>> with ShsClient() as c:
            >>>     c.copy_data_from_to(33, 1)  # copies measurement field to Aux1.
        """
        if not isinstance(from_field, int):
            raise TypeError('from_field should be of type int')
        if not isinstance(to_field, int):
            raise TypeError('to_field should be of type int')
        return self.send_command(34, f"{from_field}-{to_field}")

    # "35"
    def get_field_stats(self, fieldID, field_part='ORG') -> dict:
        """Retrieve statistical field information.

        Args:
            fieldID (int): ID of the field whose stats you need.
                Field IDs in SHSWorks::

                    1 – 32: fields of the AUX group
                    33: Measurement field (SHS)
                    34: Dark measurement field
                    35: Meas. - dark meas.
                    36: Vision control camera (VCC)
                    37: VCC processed
                    38: Spot displacement x
                    39: Spot displacement y
                    40: Power density
                    41: Error function
                    42: Wave-front field
                    43: Corr. wave-front field
                    44: Zernike evaluation
                    45: Power map
                    46: Point spread function (PSF)
                    47: Modulation transfer function (MTF)
                    48: Side view camera (SVC)
                    49: Moiré
            field_part (str): either 'ORG' or 'REF'

        Returns:
            dict: keys are 'XMIN', 'XMAX', 'YMIN', 'YMAX', 'MIN', 'MAX', 'MEAN',
            'PV', 'RMS'.
            Values are doubles.

        Example:
            >>> with ShsClient() as c:
            >>>     c.get_field_stats(42, 'ORG')
            {'XMIN': 0.89784889997,
            'XMAX': 6.5842252665,
            'YMIN': 1.0474903833,
            'YMAX': 6.8835082331,
            'MIN': -9.9467697737,
            'MAX': 3.3661278366,
            'MEAN': -4.5267755879e-17,
            'PV': 13.31289761,
            'RMS': 3.1642929445}
        """
        if not isinstance(fieldID, int):
            raise TypeError('fieldID must be an int.')
        if field_part not in ['ORG', 'REF']:
            raise ValueError('Parameter field_part can only be "ORG" or "REF".'
                             f' Is: {field_part}')
        answer = self.send_command(35, fieldID, field_part)
        return read_out_stats(answer)

    # "36"
    def get_pf_item_use(self, pfID: int) -> bool:
        """ Retrieves the “Use” state of a specific Passfail item.

        Returns:
            bool: True if item is used, False if not.

        Example:
            >>> with ShsClient() as c:
            >>>     c.get_pf_item_use(6)
            False
        """
        answer = self.send_command(36, pfID)
        return read_out_bool(answer)

    # "37"
    def set_pf_item_use(self, pfID: int, state: int) -> str:
        """Sets “Use” state of a specific Passfail item on or off.

        Returns:
            str: Answer string from SHSWorks.

        Example:
            >>> c = ShsClient()
            >>> c.set_pf_item_use(6, 1)
            'Stop|JID=000|OP=;ST=;SN=|1=Ok|1\\r\\n'
            >>> c.get_pf_item_use(6)
            True
            >>> c.set_pf_item_use(6, 0)
            'Stop|JID=002|OP=;ST=;SN=|1=Ok|1\\r\\n'
            >>> c.get_pf_item_use(6)
            False
            >>> c.close()
        """
        if not isinstance(pfID, int):
            raise TypeError('pfID must be of type int.')
        if state not in [0, 1]:
            raise ValueError(f"state must be in [0, 1], not {state}")
        # cast to int because bools pass the assertions and cause errors
        return self.send_command(37, pfID, int(state))

    # "38"
    def save_setup(self, setup_name) -> str:
        """ Saves parameter setup in SHSWorks

        Returns:
            str: Answer string from SHSWorks.
        """
        answer = self.send_command(38, setup_name)
        return answer

    # "39"
    def save_vcc_bmp(self, bmp_path) -> str:
        r""" Saves VCC image as bitmap file
        Full path and filename need to be specified in the command string.

        Example:
            >>> bmp_path = Path(r"c:\myPath\myImage.bmp")
            >>> with ShsClient() as c:
            >>>     c.save_vcc_bmp(bmp_path)
        """
        bmp_path = Path(bmp_path)
        if bmp_path.suffix != '.bmp':
            raise IOError('The suffix of the filename needs to'
                          f' be ".bmp": {bmp_path}')
        answer = self.send_command(39, bmp_path)
        return _get_result(answer)

    # "40"
    def save_radial_power_map(self, n_samples, n_max_avg_points, path) -> str:
        r"""Saves radial power map to CSV file.

        Args:
            n_samples (int): number of sample points of the line data /
                number of concentric circles
            n_max_avg_points (int): number of averaged points on the outer
                circle.
            path (str / int): Full path and filename

        Example:
            >>> csv_path = Path(r'c:\mypath\myFile.csv')
            >>> with ShsClient() as c:
            >>>     c.save_radial_power_map(56, 50, csv_path)
        """
        path = Path(path)
        if path.suffix != '.csv':
            raise IOError('Suffix of path must be ".csv".')
        if not isinstance(n_samples, int):
            raise TypeError('n_samples must be of type int.')
        if not isinstance(n_max_avg_points, int):
            raise TypeError('n_max_avg_points must be of type int.')
        return self.send_command(40, n_samples, n_max_avg_points, path)

    # "41"
    def get_radial_power_map_stats(self, n_samples, n_max_avg_points) -> dict:
        """ Retrieves the radial power map statistic.

        Args:
            n_samples (int): number of sample points of the line data /
                number of concentric Circles
            n_max_avg_points (int): number of averaged points on the
                outer circle

        Returns:
            dict:  keys are 'XMIN', 'XMAX', 'YMIN', 'YMAX',
            'MIN', 'MAX', 'MEAN', 'PV', 'RMS'
        """
        if not isinstance(n_samples, int):
            raise TypeError('n_samples must be of type int.')
        if not isinstance(n_max_avg_points, int):
            raise TypeError('n_max_avg_points must be of type int.')
        answer = self.send_command(41, n_samples, n_max_avg_points)
        return read_out_stats(answer)

    # "42"
    def set_shs_freerun_state(self, state):
        """Sets SHS freerun state.

        Args:
            state (int): 0 (freerun disabled) or 1 (freerun enabled)

        Returns:
            str: Answer string from SHSWorks.
        """
        if not isinstance(state, int):
            raise TypeError('state must be of type int.')
        return self.send_command(42, int(state))

    # "42"
    def get_shs_freerun_state(self) -> bool:
        """Gets SHS freerun state.

        Returns:
            bool: Answer string from SHSWorks.
        """
        answer = self.send_command(42)
        return read_out_bool(answer)

    # "43"
    def open_cameras(self):
        """Opens the connection to the cameras.

        Returns:
            str: Answer string from SHSWorks.
        """
        return self.send_command(43)

    # "44"
    def close_cameras(self):
        """Closes the connection to the cameras.

        Returns:
            str: Answer string from SHSWorks.
        """
        return self.send_command(44)

    # "45"
    def set_improc_cfg_path(self, path=""):
        """Sets the path of the ImProc2.cfg file to be used.

        Args:
            path (Path): Absolute Path or filename. If just a filename is
                provided, it must be located in SHSWorks config folder. If
                this parameter is omitted, it is reset to the default path.

        Returns:
            str: Answer string from SHSWorks.
        """
        return self.send_command(45, path)


    COMMANDS = {
        0: "test",
        1: "open_live",
        2: "grab_org",
        3: "grab_ref",
        4: "evaluation",
        5: "load_setup",
        6: "import_par",
        7: "get_pf_indices",
        8: "close_live",
        9: "get_cam_settings",
        10: "set_cam_setting",
        11: "tilt_cal_org",
        12: "tilt_cal_ref",
        13: "import_spot_data",
        14: "export_spot_data",
        15: "eval_spot_data",
        16: "select_field",
        17: "delete_fields",
        18: "center_sample",
        19: "get_center_sample_state",
        20: "get_pf_names",
        21: "get_shsworks_version",
        22: "get_first_zernike_index",
        23: "get_number_of_zernikes",
        24: "get_pf_values",
        25: "get_total_pf_result",
        26: "get_par",
        27: "set_par",
        28: "get_pf_item_value",
        29: "get_pf_item_result",
        30: "load_file",
        31: "save_file",
        32: "set_output_path",
        33: "set_output_name",
        34: "copy_data_from_to",
        35: "get_field_stats",
        36: "get_pf_item_use",
        37: "set_pf_item_use",
        38: "save_setup",
        39: "save_vcc_bmp",
        40: "save_radial_power_map",
        41: "get_radial_power_map_stats",
        42: "set_shs_freerun_state or get_shs_freerun_state",
        43: "open_cameras",
        44: "close_cameras",
        45: "set_improc_cfg_path",
    }

    # convenience methods
    def get_number_of_pf_items(self):
        """Returns total number of pass fail items.

        Returns:
            int: number of pass fail items
        """
        zernikes = self.get_number_of_zernikes()
        first_zernike = self.get_first_zernike_index()
        return zernikes + first_zernike

    def select_pf_items(self, pf_items: list):
        """Sets use of list of pass fail items to 1 and to 0 for all others.

        Args:
            pf_items (list(int)): list of all indices of pass fail items that
                should be active.

        Example:
            >>> pf_items = [
            >>>     0, 1, 2, 3, 4, 5, 6, 18, 19, 20, 21, 22, 31, 32, 42, 43,
            >>>     44, 45, 46, 47, 48, 49, 50, 72, 73, 79, 80, 81, 82, 83,
            >>>     84, 85, 86, 87, 88, 146, 147, 148, 149, 150, 151, 152,
            >>>     153, 170, 171, 172, 250, 251, 252, 253, 254, 255, 256,
            >>>     257, 258, 259, 260, 261, 262]
            >>> c.select_pf_items(pf_items)
        """
        n_pf_items = self.get_number_of_pf_items()
        for pfi in range(n_pf_items):
            if pfi not in pf_items:
                self.set_pf_item_use(pfi, 0)
            else:
                self.set_pf_item_use(pfi, 1)

    def set_pars(self, par_dict: dict):
        """Sets all pars to the value provided in par_dict.

        Args:
            par_dict (dict): Keys: par-names,  Values: respective values

        Example:
            >>> pars = {'nRECType': 1,
            >>>         'nRECDimWf': 64}
            >>> with Client() as c:
            >>>     c.set_pars(pars)
        """
        for par in par_dict:
            self.set_par(par, par_dict[par])

    def _check_pass_fail_config(self):
        """Check if pass fail evaluation is deactivated or if no items are
        selected.
        """
        if not bool(self.get_par('bPassFail')):
            raise UserWarning('The Passfail evaluation is turned off.')
        else:
            raise UserWarning('No Passfail items are selected.')

    def get_pf_names_dict(self):
        """Returns dictionary like {pf_id: 'pf name'}
        """
        pf_indices = self.get_pf_indices()
        pf_names = self.get_pf_names()
        return dict(zip(pf_indices, pf_names))