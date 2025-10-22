# Small runner to launch the GUI for a quick smoke test
import sys
from gui.qt_compat import QtWidgets
from gui.main_window import MainWindow

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    win = MainWindow()
    win.show()
    # exec name differs between PySide (exec) and older PyQt (exec_)
    if hasattr(app, 'exec'):
        rc = app.exec()
    else:
        rc = app.exec_()
    sys.exit(rc)

