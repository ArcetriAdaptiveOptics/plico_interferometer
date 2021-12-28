import sys

import plico_interferometer
from guietta import Gui, _


class Runner(object):

    def __init__(self):
        pass

    def _setUp(self, host, port):
        self._interferometer = plico_interferometer.interferometer(host, int(port))
        print(dir(self._interferometer))

        def moveby(gui):
            nsteps = int(gui.nstepsby)
            self._interferometer.move_by(nsteps)

        def moveto(gui):
            nsteps = int(gui.nstepsto)
            self._interferometer.move_to(nsteps)

        def getstatus(gui):
            try:
                gui.pos = self._interferometer.position()
                gui.status = self._interferometer.status().as_dict()
            except Exception as e:
                gui.pos = str(e)

        self.gui = Gui(
             [  'Pos:'     , 'pos'       , _       ],
             [ ['Move to'] , '__nstepsto__', 'steps' ],
             [ ['Move by'] , '__nstepsby__', 'steps' ],
             [ 'Status:'   , 'status'    , _       ]
        )
        self.gui.Moveby = moveby
        self.gui.Moveto = moveto
        self.gui.timer_start(getstatus, 0.1)

    def run(self, argv):
        host = 'localhost'
        port = 7300
        if len(argv) == 1:
            host = argv[0]
        if len(argv) == 2:
            port = argv[1]

        self._setUp(host, port)
        self.gui.run()

    def terminate(self, signal, frame):
        pass


if __name__ == '__main__':
    runner = Runner()
    sys.exit(runner.run(sys.argv[1:]))

