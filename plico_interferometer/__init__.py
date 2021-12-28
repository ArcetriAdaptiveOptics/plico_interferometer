from plico_interferometer.utils.constants import Constants


def _getDefaultConfigFilePath():
    from plico.utils.config_file_manager import ConfigFileManager
    cfgFileMgr = ConfigFileManager(Constants.APP_NAME,
                                   Constants.APP_AUTHOR,
                                   Constants.THIS_PACKAGE)
    return cfgFileMgr.getConfigFilePath()


default_config_file_path = _getDefaultConfigFilePath()


def interferometer(hostname, port):

    from plico_interferometer.client.interferometer_client import InterferometerClient
    from plico.rpc.zmq_remote_procedure_call import ZmqRemoteProcedureCall
    from plico.rpc.zmq_ports import ZmqPorts
    from plico.rpc.sockets import Sockets

    rpc = ZmqRemoteProcedureCall()
    zmqPorts = ZmqPorts(hostname, port)
    sockets = Sockets(zmqPorts, rpc)
    return InterferometerClient(rpc, sockets)
