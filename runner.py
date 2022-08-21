import os
import sys
import subprocess
import utils
try:
    import wintheme  # type: ignore
    import win32gui  # type: ignore
    import win32process  # type: ignore
except ImportError:
    pass
from threading import Thread, Timer
from ui_util import QtCore, QtGui, QtWidgets


def debug_qemu(a) -> None:
    # TODO: fix it
    result = subprocess.check_output(
        a,
        shell=True,
        encoding='utf-8',
        stderr=subprocess.PIPE
    )
    QtWidgets.QMessageBox.information(
        None,
        'Log',
        utils.stringify_cmdline(a) + ': \n' + result.strip() or 'None'
    )


def dark_qemu(pid: int) -> None:
    def callback(hwnd: int, _: None) -> bool:
        ct_id, cp_id = win32process.GetWindowThreadProcessId(hwnd)
        if pid not in (ct_id, cp_id):
            return True
        wintheme.set_window_theme(hwnd, wintheme.THEME_DARK)
        return True

    win32gui.EnumWindows(callback, None)


def run_machine(c: dict) -> None:
    a = []
    if c['sudoCheck'] and not sys.platform == 'win32':
        a.append('sudo')
    a.append('qemu-system-')
    if utils.global_config['qemu_path']:
        a[-1] = utils.global_config['qemu_path'] + a[-1]
    a[-1] += 'x86_64' if c['bitCheck'] else 'i386'
    if sys.platform == 'win32' and c['mwinCheck']:
        a[-1] += 'w'
    a.append('-cpu')
    a.append(c['cpuBox'][0].split(': ')[0])
    for cpuid in c['cpuid']:
        if c['cpuid'][cpuid]:
            a[-1] += ',' + cpuid + '=' + ('on' if c['cpuid'][cpuid] == 1 else 'off')
    if c['accelBox'][1] > 0:
        a.append('-accel')
        a.append([
            'tcg',
            'tcg,thread=single',
            'tcg,thread=multi',
            'whpx',
            'hax',
            'kvm'
        ][c['accelBox'][1]])
    if not c['acpiCheck']:
        a.append('-no-acpi')
    if not c['hpetCheck']:
        a.append('-no-hpet')
    a.append('-m')
    a.append(c['memoryEdit'])
    if utils.global_config['l_path'].strip():
        a.append('-L')
        a.append(utils.global_config['l_path'])
    if c['biosEdit'].strip():
        a.append('-bios')
        a.append(c['biosEdit'])
    if c['cpuNum'] > 0:
        a.append('-smp')
        a.append(c['cpuNum'])
    if c['speedNum'] >= 0:
        a.append('-rtc')
        a.append('base=localtime,clock=vm')
        a.append('-icount')
        a.append(f'shift={c["speedNum"]},align=off,sleep=off')
    if c['videoBox'][1] > 0:
        a.append('-device')
        a.append([
            'none',
            'VGA' if c['vpciCheck'] else 'isa-vga',
            'bochs-display',
            'virtio-vga',
            'virtio-gpu-pci' if c['vpciCheck'] else 'virtio-gpu',
            'qxl-vga',
            'qxl',
            'cirrus-vga' if c['vpciCheck'] else 'isa-cirrus-vga',
            'ati-vga,model=rage128p',
            'ati-vga,model=rv100',
            'vmware-svga',
            'ramfb'
        ][c['videoBox'][1]])
        if c['videoBox'][1] in (1, 5, 6, 7, 8, 9, 10):
            a[-1] += f',vgamem_mb={c["vmemNum"]}'
    if c['sgaCheck']:
        a.append('-machine')
        a.append('graphics=off')
    if c['nographicCheck']:
        a.append('-nographic')
    if c['displayBox'][1] > 0:
        a.append('-display')
        a.append([
            'none',
            'gtk',
            'sdl,grab-mod=rctrl' if c['ctrlgrabCheck'] else 'sdl',
            f'vnc={c["vncEdit"]}',
            'curses'
        ][c['displayBox'][1]])
    if c['monitorBox'][1] > 0:
        a.append('-monitor')
        a.append('vc' if c['monitorBox'][1] >= 2 else 'stdio')
    if c['serialBox'][1] > 0:
        a.append('-serial')
        a.append('vc' if c['serialBox'][1] >= 2 else 'stdio')
    if c['parallelBox'][1] > 0:
        a.append('-parallel')
        a.append('vc' if c['parallelBox'][1] >= 2 else 'stdio')
    for i in ('ac97Check', 'adlibCheck', 'cs4231aCheck', 'es1370Check', 'gusCheck', 'sb16Check'):
        if c[i]:
            a.append('-device')
            a.append(i[:-5])
    if c['hdadCheck']:
        a.append('-device')
        a.append('hda-duplex')
    if c['hdamCheck']:
        a.append('-device')
        a.append('hda-micro')
    if c['hdaoCheck']:
        a.append('-device')
        a.append('hda-output')
    if c['hdaich9Check']:
        a.append('-device')
        a.append('ich9-intel-hda')
    if c['hdaich6Check']:
        a.append('-device')
        a.append('intel-hda')
    if c['subaudioCheck']:
        a.append('-device')
        a.append('usb-audio')
    for i in ('fda', 'fdb', 'hda', 'hdb', 'hdc', 'hdd', 'cdrom'):
        if c[i + 'Edit'].strip():
            a.append('-' + i)
            a.append(c[i + 'Edit'].strip())
    a.append('-boot')
    a.append('menu=' + ('on' if c['splashNum'] > 0 else 'off'))
    a[-1] += ',order=' + [
        'acd',
        'adc',
        'cad',
        'cda',
        'dca',
        'dac'
    ][c['orderBox'][1]]
    if c['splashNum'] > 0:
        if c['splashEdit']:
            a[-1] += ',splash=' + c['splashEdit'].replace('$(QemuBox)', utils.cwd)
        a[-1] += f',splash-time={c["splashNum"]}'
    if c['usbCheck']:
        a.append('-usb')
    a += utils.parse_cmdline(c['otherEdit'])
    for device_name in c['devices']:
        a.append('-device')
        a.append(device_name)
        if c['devices'][device_name]['other']:
            a += ',' + c['devices'][device_name]['other']
    print(utils.stringify_cmdline(tuple(a)))
    try:
        if c['runBox'][1] == 0:
            proc = subprocess.Popen(a)
            if c['darkifyNum'] > 0 and sys.platform == 'win32' and\
                    int(os.environ['__BORDER_THEME']) == wintheme.THEME_DARK:
                Timer(c['darkifyNum'] / 1000, lambda: dark_qemu(proc.pid)).start()
        elif c['runBox'][1] == 1:
            Thread(target=lambda: debug_qemu(a)).start()
        elif c['runBox'][1] == 2:
            Thread(target=lambda: os.system(utils.stringify_cmdline(tuple(a)))).start()
    except Exception as err:
        print('Failed to QEMU: ' + str(err))
