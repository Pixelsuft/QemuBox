import os
import shutil
import utils
from ui_util import QtCore, QtGui, QtWidgets
from py_ui.create import Ui_MainWindow


class CreateMachine:
    def __init__(self, manager: any) -> None:
        super(CreateMachine, self).__init__()
        self.manager = manager
        self.window = QtWidgets.QMainWindow()
        self.hwnd = 0
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self.window)
        self.setup_events()

    def run(self) -> None:
        self.hwnd = int(self.window.winId())
        self.window.setWindowFlags(QtCore.Qt.WindowType.WindowCloseButtonHint)
        self.window.setWindowModality(QtCore.Qt.WindowModality.ApplicationModal)
        utils.update_style(self, False)
        self.ui.nameEdit.clear()
        self.ui.applyButton.setEnabled(False)
        self.ui.presetBox.clear()
        for preset in utils.get_all_presets():
            self.ui.presetBox.addItem(preset)
        self.window.show()

    def setup_events(self) -> None:
        self.ui.cancelButton.clicked.connect(self.window.close)
        self.ui.applyButton.clicked.connect(self.apply)
        self.ui.nameEdit.textChanged.connect(self.check_ability)

    def check_ability(self, edit_text: str) -> None:
        edit_text = edit_text.strip()
        if not edit_text:
            return self.ui.applyButton.setEnabled(False)
        if edit_text.lower() in tuple(x.lower() for x in utils.get_all_machines()):
            return self.ui.applyButton.setEnabled(False)
        for elem in ('/', '\\', ':', '*', '?', '"', '<', '>', '|'):
            if elem in edit_text:
                return self.ui.applyButton.setEnabled(False)
        return self.ui.applyButton.setEnabled(True)

    def apply(self) -> None:
        all_machines = list(utils.get_machines_list())
        current_text = self.manager.current_text
        current_index = (all_machines.index(current_text) + 1) if current_text else len(all_machines)
        all_machines.insert(current_index, self.ui.nameEdit.text())
        shutil.copy(
            os.path.join(utils.presets_dir, self.ui.presetBox.currentText() + '.json'),
            os.path.join(utils.machines_dir, self.ui.nameEdit.text() + '.json')
        )
        utils.set_machines_list(all_machines)
        utils.check_all_machines()
        self.manager.update_machines_list()
        self.window.close()
