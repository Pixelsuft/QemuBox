import utils
from ui_util import QtCore, QtGui, QtWidgets
from py_ui.gsettings import Ui_MainWindow


class GlobalSettings:
    def __init__(self, manager: any) -> None:
        super(GlobalSettings, self).__init__()
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
        self.ui.themeBox.clear()
        for qss_name in utils.get_all_qss():
            self.ui.themeBox.addItem(qss_name)
        self.ui.themeBox.setCurrentText(utils.global_config['theme'])
        self.ui.styleBox.setCurrentText(utils.global_config['style'])
        self.ui.qpathEdit.setText(utils.global_config['qemu_path'])
        self.ui.lpathEdit.setText(utils.global_config['l_path'])
        self.window.show()

    def setup_events(self) -> None:
        self.ui.cancelButton.clicked.connect(self.window.close)
        self.ui.applyButton.clicked.connect(self.apply)
        self.ui.qpathButton.clicked.connect(self.select_qemu_folder)
        self.ui.lpathButton.clicked.connect(self.select_l_folder)

    def select_qemu_folder(self) -> None:
        result = QtWidgets.QFileDialog.getExistingDirectory(
            self.window,
            'Open Qemu Path'
        )
        self.ui.qpathEdit.setText(result.strip())

    def select_l_folder(self) -> None:
        result = QtWidgets.QFileDialog.getExistingDirectory(
            self.window,
            'Open Qemu (-L) Path'
        )
        self.ui.lpathEdit.setText(result.strip())

    def apply(self) -> None:
        utils.write_config('qemubox', {
            'theme': self.ui.themeBox.currentText(),
            'style': self.ui.styleBox.currentText(),
            'qemu_path': self.ui.qpathEdit.text(),
            'l_path': self.ui.lpathEdit.text()
        })
        self.window.close()
        utils.global_config = utils.read_global_config()
        utils.update_style(self.manager)
