import os
import json
import utils
from ui_util import QtCore, QtGui, QtWidgets
from py_ui.settings import Ui_MainWindow


class ConfigureMachine:
    def __init__(self, argv: list) -> None:
        super(ConfigureMachine, self).__init__()
        self.argv = argv
        self.machine = os.getenv('__MACHINE_TO_CONFIGURE')
        self.machine_path = os.path.join(utils.machines_dir, self.machine + '.json')
        self.config = json.loads(open(self.machine_path, 'r', encoding='utf-8').read())
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
        cpus, cpuid = utils.get_qemu_cpus()
        self.all_devices_split, self.all_devices = utils.get_qemu_devices()
        for device_name in self.all_devices_split['0']:
            self.ui.device1List.addItem(device_name)
        for device_name in self.all_devices_split['1']:
            self.ui.device2List.addItem(device_name)
        self.current_device = ''
        self.devices = self.config.get('devices') or {}
        self.cpu_id = self.config.get('cpuid') or {cpu_id: 0 for cpu_id in cpuid}
        for cpu in cpus.keys():
            self.ui.cpuBox.addItem(cpu)
        self.ui.cpuidList.addItems(cpuid)
        self.ui.cpuidList.setCurrentItem(self.ui.cpuidList.item(0))
        for elem_name in self.config:
            if elem_name.endswith('Edit'):
                getattr(self.ui, elem_name).setText(self.config[elem_name])
            elif elem_name.endswith('Check'):
                getattr(self.ui, elem_name).setChecked(self.config[elem_name])
            elif elem_name.endswith('Box'):
                getattr(self.ui, elem_name).setCurrentIndex(self.config[elem_name][1])
                getattr(self.ui, elem_name).setCurrentText(self.config[elem_name][0])
            elif elem_name.endswith('Num'):
                getattr(self.ui, elem_name).setValue(self.config[elem_name])
        self.window.setWindowTitle(f'Configure {self.machine}')
        self.setup_events()
        self.window.show()
        self.exit_code = self.app.exec()

    def setup_events(self) -> None:
        self.ui.cancelButton.clicked.connect(self.window.close)
        self.ui.applyButton.clicked.connect(self.apply_config)
        self.ui.cpuonButton.clicked.connect(lambda: self.cpuid_set_state(1))
        self.ui.cpuoffButton.clicked.connect(lambda: self.cpuid_set_state(-1))
        self.ui.cpudefaultButton.clicked.connect(lambda: self.cpuid_set_state(0))
        self.ui.cpuresetButton.clicked.connect(lambda: self.cpuid_set_state(-2))
        self.ui.biosButton.clicked.connect(self.select_bios)
        self.ui.device1List.currentTextChanged.connect(self.current_device_change)
        self.ui.device2List.currentTextChanged.connect(self.current_device_change)
        self.ui.deviceenableShow.clicked.connect(self.check_device_check)
        self.ui.deviceotherChange.textChanged.connect(self.device_other_change)
        self.ui.fdaButton.clicked.connect(lambda: self.open_drive('fda'))
        self.ui.fdbButton.clicked.connect(lambda: self.open_drive('fdb'))
        self.ui.hdaButton.clicked.connect(lambda: self.open_drive('hda'))
        self.ui.hdbButton.clicked.connect(lambda: self.open_drive('hdb'))
        self.ui.hdcButton.clicked.connect(lambda: self.open_drive('hdc'))
        self.ui.hddButton.clicked.connect(lambda: self.open_drive('hdd'))
        self.ui.cdromButton.clicked.connect(lambda: self.open_drive('cdrom'))
        self.ui.fdasButton.clicked.connect(lambda: self.open_shared_drive('fda'))
        self.ui.fdbsButton.clicked.connect(lambda: self.open_shared_drive('fdb'))
        self.ui.hdasButton.clicked.connect(lambda: self.open_shared_drive('hda'))
        self.ui.hdbsButton.clicked.connect(lambda: self.open_shared_drive('hdb'))
        self.ui.hdcsButton.clicked.connect(lambda: self.open_shared_drive('hdc'))
        self.ui.hddsButton.clicked.connect(lambda: self.open_shared_drive('hdd'))
        self.ui.cdromsButton.clicked.connect(lambda: self.open_shared_drive('cdrom'))

    def open_drive(self, drive_name: str) -> None:
        result = QtWidgets.QFileDialog.getOpenFileName(
            self.window,
            'Open Image...',
            utils.get_last_path(),
            '*'
        )[0]
        getattr(self.ui, drive_name + 'Edit').setText(result)
        if not result.strip():
            return
        utils.set_last_path(os.path.dirname(result))

    def open_shared_drive(self, drive_name: str) -> None:
        result = QtWidgets.QFileDialog.getExistingDirectory(
            self.window,
            'Open Folder...',
            utils.get_last_path()
        )
        if not result.strip():
            return
        utils.set_last_path(result)
        getattr(self.ui, drive_name + 'Edit').setText(
            ('fat::' if drive_name == 'cdrom' else 'fat::rw:') + result
        )

    def check_device_check(self, is_checked: bool) -> None:
        if not self.current_text:
            return
        if not is_checked:
            if self.devices.get(self.current_text):
                del self.devices[self.current_text]
            return
        self.devices[self.current_text] = {
            'other': self.ui.deviceotherChange.text()
        }

    def device_other_change(self, new_text: str) -> None:
        if not self.current_text:
            return
        if not self.devices.get(self.current_text):
            return
        self.devices[self.current_text]['other'] = new_text or ''

    def current_device_change(self, new_device: str) -> None:
        if not new_device:
            self.current_text = ''
            return
        self.current_text = new_device
        self.ui.deviceenableShow.setChecked(bool(self.devices.get(new_device)))
        self.ui.devicedeskLabel.setText('Description: ' + self.all_devices[new_device]['desc'])
        self.ui.devicebusLabel.setText('Bus: ' + self.all_devices[new_device]['bus'])
        self.ui.deviceotherChange.setText((self.devices.get(new_device) or {'other': ''})['other'])

    def apply_config(self) -> None:
        for elem_name in dir(self.ui):
            elem = getattr(self.ui, elem_name)
            if elem_name.endswith('Edit'):
                self.config[elem_name] = elem.text()
            elif elem_name.endswith('Box'):
                self.config[elem_name] = [elem.currentText(), elem.currentIndex()]
            elif elem_name.endswith('Check'):
                self.config[elem_name] = elem.isChecked()
            elif elem_name.endswith('Num'):
                self.config[elem_name] = elem.value()
        self.config['cpuid'] = self.cpu_id
        self.config['devices'] = self.devices
        open(self.machine_path, 'w', encoding='utf-8').write(json.dumps(self.config))
        self.window.close()

    def select_bios(self) -> None:
        result = QtWidgets.QFileDialog.getOpenFileName(
            self.window,
            'Open Bios...',
            utils.global_config['l_path'] or utils.global_config['qemu_path'],
            '*'
        )[0]
        self.ui.biosEdit.setText(result.strip())

    def cpuid_set_state(self, sender: int) -> None:
        if sender == -2:
            self.cpu_id = {cpu_id: 0 for cpu_id in utils.get_qemu_cpus()[1]}
            return
        cpu_id = self.ui.cpuidList.currentItem().text()
        self.cpu_id[cpu_id] = sender
