import os
import sys
import subprocess
import json
import shutil
import utils
from ui_util import QtCore, QtGui, QtWidgets
from py_ui.manager import Ui_MainWindow
from global_settings import GlobalSettings
from create_machine import CreateMachine
from rename_machine import RenameMachine
from runner import run_machine


class Manager:
    def __init__(self, argv: list) -> None:
        super(Manager, self).__init__()
        self.argv = argv
        self.app = QtWidgets.QApplication(argv)
        self.window = QtWidgets.QMainWindow()
        self.hwnd = int(self.window.winId())
        self.window.setWindowFlags(
            QtCore.Qt.WindowType.WindowCloseButtonHint | QtCore.Qt.WindowType.WindowMinimizeButtonHint
        )
        utils.update_style(self)
        self.current_text = None
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self.window)
        self.ui.machinesList.addItems(utils.get_machines_list())
        self.global_settings = GlobalSettings(self)
        self.create_machine = CreateMachine(self)
        self.rename_machine = RenameMachine(self)
        self.setup_events()
        self.update_buttons_access()
        self.window.show()
        self.exit_code = self.app.exec()

    def setup_events(self) -> None:
        self.ui.machinesList.currentTextChanged.connect(self.text_changed)
        self.ui.exitButton.clicked.connect(lambda: sys.exit(0))
        self.ui.gsetsButton.clicked.connect(self.global_settings.run)
        self.ui.addButton.clicked.connect(self.create_machine.run)
        self.ui.deleteButton.clicked.connect(self.delete_machine)
        self.ui.copyButton.clicked.connect(self.copy_machine)
        self.ui.renameButton.clicked.connect(self.rename_machine.run)
        self.ui.upButton.clicked.connect(self.up_machine)
        self.ui.downButton.clicked.connect(self.down_machine)
        self.ui.setsButton.clicked.connect(self.configure_machine)
        self.ui.runButton.clicked.connect(self.run_machine)

    def run_machine(self) -> None:
        run_machine(json.loads(open(os.path.join(
            utils.machines_dir, self.current_text + '.json'
        ), 'r', encoding='utf-8').read()))

    def configure_machine(self) -> None:
        subprocess.Popen([
            sys.executable,
            os.path.join(utils.cwd, 'main.py'),
            '--configure-machine',
            self.current_text
        ])

    def copy_machine(self) -> None:
        machines = utils.get_machines_list()
        if self.current_text + ' (Copy)' in machines:
            return
        current_index = machines.index(self.current_text) + 1
        machines.insert(current_index, self.current_text + ' (Copy)')
        shutil.copy(
            os.path.join(utils.machines_dir, self.current_text + '.json'),
            os.path.join(utils.machines_dir, self.current_text + ' (Copy).json')
        )
        self.current_text += ' (Copy)'
        utils.set_machines_list(machines)
        self.update_machines_list()

    def delete_machine(self) -> None:
        machines = utils.get_machines_list()
        current_id = machines.index(self.current_text)
        machines.remove(self.current_text)
        os.remove(os.path.join(utils.machines_dir, self.current_text + '.json'))
        self.current_text = machines[current_id - 1] if current_id > 0 else None
        utils.set_machines_list(machines)
        self.update_machines_list()

    def up_machine(self) -> None:
        machines = utils.get_machines_list()
        current_id = machines.index(self.current_text)
        if current_id < 1:
            return
        machines[current_id], machines[current_id - 1] = machines[current_id - 1], machines[current_id]
        utils.set_machines_list(machines)
        self.update_machines_list()

    def down_machine(self) -> None:
        machines = utils.get_machines_list()
        current_id = machines.index(self.current_text)
        if current_id >= len(machines) - 1:
            return
        machines[current_id], machines[current_id + 1] = machines[current_id + 1], machines[current_id]
        utils.set_machines_list(machines)
        self.update_machines_list()

    def update_machines_list(self, current_text: str = None) -> None:
        if not current_text:
            current_text = self.current_text
        self.ui.machinesList.clear()
        machines_list = utils.get_machines_list()
        for machine_name in machines_list:
            self.ui.machinesList.addItem(machine_name)
        if current_text:
            self.ui.machinesList.setCurrentRow(machines_list.index(current_text))
        self.update_buttons_access()

    def text_changed(self, new_text: str) -> None:
        if new_text not in utils.get_all_machines():
            self.current_text = None
            return
        self.current_text = new_text
        self.update_buttons_access()

    def update_buttons_access(self) -> bool:
        should_enable = bool(self.current_text)
        self.ui.runButton.setEnabled(should_enable)
        self.ui.setsButton.setEnabled(should_enable)
        self.ui.renameButton.setEnabled(should_enable)
        self.ui.copyButton.setEnabled(should_enable)
        self.ui.deleteButton.setEnabled(should_enable)
        self.ui.upButton.setEnabled(should_enable)
        self.ui.downButton.setEnabled(should_enable)
        return should_enable
