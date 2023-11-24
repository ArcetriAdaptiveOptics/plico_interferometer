# plico_interferometer

client of an interferometer controlled under the plico environment 

### How to use it
On the client side, in order to use the interferometer, installation of the plico_interferometer package is required.
The steps required for the startup are

- Have a Python working environment (no specific version is required, but preferably higher than 3)

- Install the Python library using the command pip install plico_interferometer

- Open a terminal and execute the following commands
```
import plico_interferometer
interf = plico_interferometer.interferometer(hostServer, portServer)
```
- Use standard command as interf.wavefront(n_images) or interf.burst_and_return_average(n_images)




 ![Python package](https://github.com/ArcetriAdaptiveOptics/plico_interferometer/workflows/Python%20package/badge.svg)
 [![codecov](https://codecov.io/gh/ArcetriAdaptiveOptics/plico_interferometer/branch/main/graph/badge.svg?token=ApWOrs49uw)](https://codecov.io/gh/ArcetriAdaptiveOptics/plico_interferometer)
 [![Documentation Status](https://readthedocs.org/projects/plico_interferometer/badge/?version=latest)](https://plico_interferometer.readthedocs.io/en/latest/?badge=latest)
 [![PyPI version](https://badge.fury.io/py/plico-interferometer.svg)](https://badge.fury.io/py/plico-interferometer)


plico_interferometer is an application to control motors under the [plico][plico] environment.

[plico]: https://github.com/ArcetriAdaptiveOptics/plico
