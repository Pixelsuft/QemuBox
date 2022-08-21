import os
import subprocess
import json
import wintheme
from ui_util import QtCore, QtGui, QtWidgets


def write_config(config_name: str, config_content: dict) -> None:
    open(os.path.join(configs_dir, config_name + '.json'), 'w', encoding='utf-8').write(json.dumps(
        config_content,
        indent=4
    ))


def read_config(config_name: str, default_config: dict = None) -> dict:
    config_path = os.path.join(configs_dir, config_name + '.json')
    if not os.path.isfile(config_path):
        write_config(config_name, default_config or {})
        return default_config or {}
    return json.loads(open(config_path, 'r', encoding='utf-8').read())


def read_qss(qss_name: str) -> str:
    return open(os.path.join(qss_dir, qss_name + '.qss'), 'r', encoding='utf-8').read().replace(
        'url(://', f'url(themes/res/'
    )


def get_all_qss() -> tuple:
    return tuple('.'.join(x.split('.')[:-1]) for x in os.listdir(qss_dir) if x.split('.')[-1].lower() == 'qss')


def get_all_presets() -> tuple:
    return tuple('.'.join(x.split('.')[:-1]) for x in os.listdir(presets_dir) if x.split('.')[-1].lower() == 'json')


def get_all_machines() -> tuple:
    return tuple('.'.join(x.split('.')[:-1]) for x in os.listdir(machines_dir) if x.split('.')[-1].lower() == 'json')


def update_style(main_class: any, apply_style: bool = True) -> None:
    main_class.window.setStyleSheet(read_qss(global_config['theme']))
    if int(os.getenv('__BORDER_THEME') or -1) == wintheme.THEME_DARK:
        wintheme.set_window_theme(main_class.hwnd, wintheme.THEME_DARK)
    if not apply_style:
        return
    window_style = global_config['style'].lower()
    if window_style == 'default':
        return
    main_class.app.setStyle(QtWidgets.QStyleFactory.create(window_style))


def read_global_config() -> dict:
    return read_config('qemubox', {
        'theme': 'Default',
        'style': 'Default',
        'qemu_path': '',
        'l_path': ''
    })


def set_machines_list(machines_list: any) -> None:
    write_config('machines', {
        'machines': machines_list
    })


def get_machines_list() -> list:
    return read_config('machines', {
        'machines': []
    })['machines']


def get_qemu_cpus() -> tuple:
    result = read_config('qemu_cpus', {})
    result2 = read_config('qemu_cpuid', {})
    if result and result2:
        return result, result2['all_id']
    output = subprocess.check_output([
        os.path.join(global_config['qemu_path'], 'qemu-system-i386'),
        '-cpu',
        '?'
    ], encoding='utf-8').split('\n')
    desc_start = output[1].index(output[1].split('  ')[-1].strip())
    for line in output[1:output.index('')]:
        cpu_name = line.split(' ')[1]
        cpu_desc = line[desc_start:].strip()
        if 'alias configured' in cpu_desc:
            continue
        if cpu_name.endswith('-v1'):
            cpu_name = cpu_name[:-3]
        if cpu_desc.strip():
            result[cpu_name + ': ' + cpu_desc] = cpu_name
        else:
            result[cpu_name] = cpu_name
    cpuid_flags = []
    for line in output[output.index('') + 2: -2]:
        cpuid_flags += line.strip().split(' ')
    write_config('qemu_cpuid', {'all_id': cpuid_flags})
    write_config('qemu_cpus', result)
    return result, cpuid_flags


def get_qemu_devices() -> tuple:
    result = read_config('qemu_devices', {})
    if result:
        return result, {**result['0'], **result['1']}
    result = {
        '0': {},
        '1': {}
    }
    output = subprocess.check_output([
        os.path.join(global_config['qemu_path'], 'qemu-system-i386'),
        '-device',
        '?'
    ], encoding='utf-8').split('\n')
    current_tab = '-1'
    for line in output:
        if not line.strip():
            continue
        if line.strip().endswith(':'):
            if 'USB' in line or 'Network' in line or 'Input' in line:
                current_tab = '0'
            elif 'Controller' in line or 'Storage' in line or 'Misc' in line:
                current_tab = '1'
            else:
                current_tab = '-1'
            continue
        if current_tab == '-1':
            continue
        tricks = {}
        for trick in line.split(', '):
            tricks[trick.split(' ')[0].lower().strip()] = ' '.join(trick.split(' ')[1:]).replace('"', '').strip()
        if not tricks.get('name'):
            continue
        result[current_tab][tricks['name']] = {
            'desc': tricks.get('desc') or '',
            'bus': tricks.get('bus') or ''
        }
    write_config('qemu_devices', result)
    return result, {**result['0'], **result['1']}


def get_last_path() -> str:
    return read_config('last_path', {'last_path': os.getcwd()})['last_path']


def set_last_path(path: str) -> None:
    write_config('last_path', {'last_path': path})


def check_all_machines() -> None:
    machines_config = get_machines_list()
    all_machines = get_all_machines()
    removed = []
    for machine_name in machines_config:
        if machine_name in all_machines:
            continue
        removed.append(machine_name)
    for machine_name in removed:
        machines_config.remove(machine_name)
    for machine_name in all_machines:
        if machine_name in machines_config or machine_name in removed:
            continue
        machines_config.append(machine_name)
    set_machines_list(machines_config)


def parse_cmdline(cmdline: str) -> tuple:
    result = ['']
    dont_skip_space = True
    for char in cmdline:
        if char == '"':
            dont_skip_space = not dont_skip_space
            continue
        if dont_skip_space and char == ' ':
            result.append('')
            continue
        result[-1] += char
    return tuple(x.strip() for x in result if x.strip())


def stringify_cmdline(cmdline: tuple) -> str:
    result = ''
    for _cmd in cmdline:
        cmd = str(_cmd)
        result += ' '
        if ' ' not in cmd:
            result += cmd
            continue
        result += '"' + cmd + '"'
    return result.strip()


cwd = os.path.dirname(__file__) or os.getcwd()
os.chdir(cwd)
configs_dir = os.path.join(cwd, 'configs')
if not os.path.isdir(configs_dir):
    os.mkdir(configs_dir)
qss_dir = os.path.join(cwd, 'themes')
presets_dir = os.path.join(cwd, 'presets')
machines_dir = os.path.join(cwd, 'machines')
if not os.path.isdir(machines_dir):
    os.mkdir(machines_dir)
check_all_machines()
global_config = read_global_config()
