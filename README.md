# plico_interferometer

client of an interferometer controlled under the plico environment 

## How to use it

### Server/client
Before using the client, it is necessary to start the server on the interferometer machine.
On the client side, in order to use the interferometer, installation of the plico_interferometer package is required.
The steps required for the startup are

- Have a Python working environment (no specific version is required, but preferably higher than 3)

- Install the Python library using the command pip install plico_interferometer

- Open a terminal and execute the following commands
```
import plico_interferometer
interf = plico_interferometer.interferometer(hostServer, portServer)
```
- Use standard command as interf.wavefront(n_images)
- For burst acquisition (implemented only for interferometers using WCF) use the command interf.burst_and_return_average(n_images, timeout).

  NOTE: in this case it is necessary to specify the timeout time (expressed in seconds) as the standard of 10s is usually not sufficient for the acquisition of more than a dozen images.

### Direct connection with WCF 4D
To connect to 4Ds with WCF (such as the 6110), for which it is not strictly necessary to have a plico server because the 4D SW itself implements a server and responds to json requests, it is possible to follow this steps directly from the client

- Have a Python working environment (no specific version is required, but preferably higher than 3)

- Install the Python library using the command pip install plico_interferometer

- Open a terminal and execute the following commands
```
import plico_interferometer
interf = plico_interferometer.interferometer_4SightFocus_client(ip, port)
```
- Use standard command as interf.wavefront(n_images)

If you want to use the burst frame acquisition option you have to use the standard server/client structure: please refer to the previous paragraph.



 ![Python package](https://github.com/ArcetriAdaptiveOptics/plico_interferometer/workflows/Python%20package/badge.svg)
 [![codecov](https://codecov.io/gh/ArcetriAdaptiveOptics/plico_interferometer/branch/main/graph/badge.svg?token=ApWOrs49uw)](https://codecov.io/gh/ArcetriAdaptiveOptics/plico_interferometer)
 [![Documentation Status](https://readthedocs.org/projects/plico_interferometer/badge/?version=latest)](https://plico_interferometer.readthedocs.io/en/latest/?badge=latest)
 [![PyPI version](https://badge.fury.io/py/plico-interferometer.svg)](https://badge.fury.io/py/plico-interferometer)


plico_interferometer is an application to control motors under the [plico][plico] environment.

[plico]: https://github.com/ArcetriAdaptiveOptics/plico
