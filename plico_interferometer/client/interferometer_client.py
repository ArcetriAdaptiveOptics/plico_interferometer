#!/usr/bin/env python
from plico_interferometer.client.abstract_interferometer_client import \
    AbstractInterferometerClient
from plico.rpc.abstract_remote_procedure_call import \
    AbstractRemoteProcedureCall
from plico.utils.logger import Logger
from plico.utils.decorator import override, returns
from plico.utils.snapshotable import Snapshotable
from plico.client.serverinfo_client import ServerInfoClient
from plico.client.hackerable_client import HackerableClient
from plico_interferometer.types.interferometer_status import \
    InterferometerStatus
from plico_interferometer.utils.timeout import Timeout


class InterferometerClient(AbstractInterferometerClient,
                           HackerableClient,
                           ServerInfoClient):

    def __init__(self,
                 rpcHandler,
                 sockets):
        assert isinstance(rpcHandler, AbstractRemoteProcedureCall)

        self._rpcHandler = rpcHandler
        self._requestSocket = sockets.serverRequest()
        self._statusSocket = sockets.serverStatus()
        self._logger = Logger.of('Interferometer client')
        HackerableClient.__init__(self,
                                  self._rpcHandler,
                                  self._requestSocket,
                                  self._logger)
        ServerInfoClient.__init__(self,
                                  self._rpcHandler,
                                  self._requestSocket,
                                  self._logger)

    @override
    @returns(InterferometerStatus)
    def status(self, timeout_in_sec=Timeout.GETTER):
        return self._rpcHandler.receivePickable(
            self._statusSocket,
            timeout_in_sec)

    @override
    def snapshot(self,
                 prefix,
                 timeout_in_sec=Timeout.GETTER):
        self._logger.notice("Getting snapshot for %s " % prefix)
        status = self.status(timeout_in_sec=timeout_in_sec)
        return Snapshotable.prepend(prefix, status.as_dict())

    @override
    def wavefront(self,
                  how_many=1,
                  timeout_in_sec=Timeout.GETTER):
        self._logger.notice("getting wavefront (average %d)" % how_many)
        return self._rpcHandler.sendRequest(
            self._requestSocket, 'wavefront',
            [how_many],
            timeout=timeout_in_sec)
