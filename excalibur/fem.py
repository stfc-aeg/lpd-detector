#from excalibur import fem_api
#import excalibur.fem_api_stub as fem_api
import importlib

class ExcaliburFemError(Exception):

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class ExcaliburFem(object):

    FEM_RTN_OK = 0
    FEM_RTN_UNKNOWNOPID = 1
    FEM_RTN_ILLEGALCHIP = 2
    FEM_RTN_BADSIZE = 3
    FEM_RTN_INITFAILED = 4

    use_stub_api = False
    api_stem = 'excalibur.fem_api'
    _fem_api = None

    def __init__(self, fem_id, fem_address, fem_port, data_address):

        self.fem_handle = None

        if ExcaliburFem._fem_api is None:
            api_module = ExcaliburFem.api_stem
            if ExcaliburFem.use_stub_api:
                api_module = api_module + '_stub'

            try:
                ExcaliburFem._fem_api = importlib.import_module(api_module)
            except ImportError as e:
                raise ExcaliburFemError('Failed to load API module: {}'.format(e))
            else:
                self._fem_api = ExcaliburFem._fem_api

        try:
            self.fem_handle = self._fem_api.initialise(
                fem_id, fem_address, fem_port, data_address
            )
        except self._fem_api.error as e:
            raise ExcaliburFemError(str(e))

    def close(self):

        try:
            self._fem_api.close(self.fem_handle)
        except self._fem_api.error as e:
            raise ExcaliburFemError(str(e))

    def get_id(self):

        try:
            fem_id = self._fem_api.get_id(self.fem_handle)
        except self._fem_api.error as e:
            raise ExcaliburFemError(str(e))

        return fem_id

    def get_int(self, chip_id, param_id, size):

        try:
            rc = self._fem_api.get_int(self.fem_handle, chip_id, param_id, size)
        except self._fem_api.error as e:
            raise ExcaliburFemError(str(e))

        return rc

    def set_int(self, chip_id, param_id, values):

        try:
            rc = self._fem_api.set_int(self.fem_handle, chip_id, param_id, values)
        except self._fem_api.error as e:
            raise ExcaliburFemError(str(e))

        return rc

    def cmd(self, chip_id, cmd_id):

        try:
            rc = self._fem_api.cmd(self.fem_handle, chip_id, cmd_id)
        except self._fem_api.error as e:
            raise ExcaliburFemError(str(e))

        return rc
