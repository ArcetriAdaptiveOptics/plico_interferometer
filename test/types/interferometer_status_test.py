import unittest
from plico_interferometer.types.interferometer_status import \
    InterferometerStatus
from plico_interferometer.client.snapshot_entry import SnapshotEntry


class Test(unittest.TestCase):

    def setUp(self):
        self.ms = InterferometerStatus('pippo')

    def test_as_dict(self):
        wanted_keys = (
            SnapshotEntry.INTERFEROMETER_NAME,)
        got = self.ms.as_dict()
        self.assertCountEqual(got.keys(), wanted_keys)


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
