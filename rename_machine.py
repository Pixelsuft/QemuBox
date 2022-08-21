import os
import utils
from ui_util import QtCore, QtGui, QtWidgets
from py_ui.rename import Ui_MainWindow


class RenameMachine:
    def __init__(self, manager: any) -> None:
        super(RenameMachine, self).__init__()
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
        self.ui.nameEdit.setText(self.manager.current_text)
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
        current_index = all_machines.index(self.manager.current_text)
        all_machines[current_index] = self.ui.nameEdit.text()
        os.rename(
            os.path.join(utils.machines_dir, self.manager.current_text + '.json'),
            os.path.join(utils.machines_dir, self.ui.nameEdit.text() + '.json')
        )
        self.manager.current_text = self.ui.nameEdit.text()
        utils.set_machines_list(all_machines)
        utils.check_all_machines()
        self.manager.update_machines_list()
        self.window.close()
