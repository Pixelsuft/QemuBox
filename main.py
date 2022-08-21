import os
import sys
import wintheme


argv_offset = 1  # for something shitty like pyinstaller


if not os.getenv('__BORDER_THEME'):
    os.environ['__BORDER_THEME'] = str(wintheme.get_apps_theme())
if len(sys.argv) <= argv_offset:
    from manager import Manager
    target = Manager
elif sys.argv[argv_offset] == '--configure-machine':
    os.environ['__MACHINE_TO_CONFIGURE'] = sys.argv[argv_offset + 1]
    from settings import ConfigureMachine
    target = ConfigureMachine
else:
    print(f'Unknown target: {sys.argv[argv_offset]}')
    sys.exit(1)

sys.exit(target(sys.argv).exit_code)
