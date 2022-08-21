import os
import sys
import subprocess
try:
    from PyQt6 import QtCore, QtGui, QtWidgets
    is_qt6 = True
    qt_version = 6
except ImportError:
    from PyQt5 import QtCore, QtGui, QtWidgets
    is_qt6 = False
    qt_version = 5


cwd = os.path.dirname(__file__) or os.getcwd()
qt_ui_dir = os.path.join(cwd, 'qt_ui')
py_ui_dir = os.path.join(cwd, 'py_ui')


def compile_ui() -> None:
    for ui_name_ext in os.listdir(qt_ui_dir):
        if os.path.isdir(ui_name_ext):
            continue
        ext = ui_name_ext.split('.')[-1].lower()
        if not ext == 'ui':
            continue
        ui_name = '.'.join(ui_name_ext.split('.')[:-1])
        print(f'Compiling: {ui_name.title()}')
        result = subprocess.call([
            f'pyuic{qt_version}',
            # '--execute',
            '--output',
            f'py_ui/{ui_name}.py',
            f'qt_ui/{ui_name}.ui'
        ])
        if result:
            print(f'Failed to compile {ui_name.title()}: 0x{hex(result)[2:].upper()}')
            sys.exit(1)
    os.chdir(cwd)


if not os.path.isdir(py_ui_dir):
    os.mkdir(py_ui_dir)
    compile_ui()
elif __name__ == '__main__':
    compile_ui()
