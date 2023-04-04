from plico_interferometer.utils.constants import Constants


def _getDefaultConfigFilePath():
    from plico.utils.config_file_manager import ConfigFileManager
    cfgFileMgr = ConfigFileManager(Constants.APP_NAME,
                                   Constants.APP_AUTHOR,
                                   Constants.THIS_PACKAGE)
    return cfgFileMgr.getConfigFilePath()


default_config_file_path = _getDefaultConfigFilePath()


def interferometer(hostname, port):
    '''
    create client of plico interferometer server

    Parameters
    ----------
    hostname: string
        ip address of the computer running the plico interferometer server

    port: integer
        port of the plico interferometer server, specified in the
        config file on the plico interferometer server. Typical = 7300
    '''

    from plico_interferometer.client.interferometer_client import \
        InterferometerClient
    from plico.rpc.zmq_remote_procedure_call import ZmqRemoteProcedureCall
    from plico.rpc.zmq_ports import ZmqPorts
    from plico.rpc.sockets import Sockets

    rpc = ZmqRemoteProcedureCall()
    zmqPorts = ZmqPorts(hostname, port)
    sockets = Sockets(zmqPorts, rpc)
    return InterferometerClient(rpc, sockets)


def interferometer_4SightFocus_client(hostname, port):
    '''
    create client of 4SightFocus

    Parameters
    ----------
    hostname: string
        ip address of the computer running the 4SightFocus software

    port: integer
        port of the 4SightFocus software
    '''
    from plico_interferometer.client.interferometer_WCF_client import \
        InterferometerWCFClient

    interferometer = InterferometerWCFClient(hostname, port)
    return interferometer
