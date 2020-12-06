import sys, os, os.path, subprocess
from functools import wraps

from . import pyqt
from .pyqt import *


from PyQt5.QtCore import QSysInfo
IS_TEST = 'pytest' in sys.modules
IS_WINDOWS = os.platform() == 'Windows'
IS_APPLE = os.platform() == 'Darwin'
IS_IOS = not (not hasattr(QSysInfo, 'macVersion') or not QSysInfo.macVersion() & QSysInfo.MV_IOS))
IS_APPLE_DARK_MODE = False # you have to figure out a way to change this if possible. I did it in C++


if IS_IOS:
    HARDWARE_UUID = '<ios>' # no device-id protection required on iOS
elif 'nt' in os.name:
    #s = subprocess.check_output('wmic csproduct get uid')
    #self.hardwareUUID = s.split('\n')[1].strip().decode('utf-8').strip()
    HARDWARE_UUID = subprocess.check_output('wmic csproduct get name,identifyingnumber,uuid').decode('utf-8').split()[-1]
elif os.uname()[0] == 'Darwin':
    HARDWARE_UUID = subprocess.check_output("system_profiler SPHardwareDataType | awk '/UUID/ { print $3; }'", shell=True).decode('utf-8').strip()
else:
    HARDWARE_UUID = None
MACHINE_NAME = QSysInfo.machineHostName()



##
## Constants
##


EXTENSION = 'xx'
DOT_EXTENSION = '.' + EXTENSION

#
FONT_FAMILY = 'SF Pro Text'
FONT_FAMILY_TITLE = 'SF Pro Display'
TEXT_FONT_SIZE = IS_IOS and 14 or 12 # ios default: 17
HELP_FONT_SIZE = IS_IOS and 13 or 11 # ios default: 15
# ANIM_TIMER_MS = 16.66 # 60Hz = 16.66ms
ANIM_TIMER_MS = 10
ANIM_DURATION_MS = 250
ANIM_EASING = QEasingCurve.OutQuad

PEN = QPen(QBrush(Qt.black), 3, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)

# Common color constants for Python/C++. Should be QColor
WINDOW_BG = None
CONTROL_BG = None
SELECTION_COLOR = None
SELECTION_PEN = None
SELECTION_BRUSH = None
HIGHLIGHT_TEXT_COLOR = None
HOVER_COLOR = None
HOVER_PEN = None
HOVER_BRUSH = None
TEXT_COLOR = None
DROP_SHADOW_COLOR = None
ACTIVE_TEXT_COLOR = None
INACTIVE_TEXT_COLOR = None
GRID_COLOR = None

# Common color constants for Qml items. Should be a string
QML_ITEM_BG = ''
QML_HEADER_BG = ''
QML_WINDOW_BG = ''
QML_CONTROL_BG = ''
QML_TEXT_COLOR = ''
QML_SELECTION_TEXT_COLOR = ''
QML_HIGHLIGHT_TEXT_COLOR = '' # synonym for 'CURRENT', not same as QPalette.HighlightedText
QML_ACTIVE_TEXT_COLOR = ''
QML_INACTIVE_TEXT_COLOR = ''
QML_HIGHLIGHT_COLOR = '' # synonym for 'CURRENT'
QML_SELECTION_COLOR = ''
QML_ITEM_ALTERNATE_BG = ''
QML_ITEM_BORDER_COLOR = '' # '#d0cfd1'
# Qml misc constants
QML_MARGINS = 20
QML_SPACING = 10
QML_HEADER_HEIGHT = 40
QML_ITEM_HEIGHT = IS_IOS and 44 or 30 # iOS portait: 44, iOS landscape: 32
QML_ITEM_LARGE_HEIGHT = 44
QML_TITLE_FONT_SIZE = QML_ITEM_HEIGHT * 1.2 * .85 # iOS portait: 44, iOS landscape: 32
QML_SMALL_TITLE_FONT_SIZE = IS_IOS and (QML_ITEM_HEIGHT * .4) or (QML_ITEM_HEIGHT * .50) # iOS portait: 44, iOS landscape: 32
QML_DROP_SHADOW_COLOR = ''
QML_IMPORT_PATHS = [ ":/qml" ]
QML_SMALL_BUTTON_WIDTH = 50


# Need prefixes that change depending on whether this app is deployed (release)
# or running form source (dev).
QRC = QFileInfo(__file__).absolutePath() + '/resources/'
QRC_QML = 'qrc:/demo/resources/' if QRC.startswith(':') else QRC


def isInstance(o, className):
    """ To avoid an import or circular import reference. """
    return bool(o.__class__.__name__ == className)



def blocked(f):
    """ Decorator to block access to every method in a class when one is called.
    
    Useful for preventing loops in event handlers.
    """
    @wraps(f)
    def go(self, *args, **kwargs):
        if not hasattr(self, '_blocked'):
            self._blocked = False
        elif self._blocked:
            return
        was = self._blocked
        self._blocked = True
        ret = None
        if args and kwargs:
            ret = f(self, *args, **kwargs)
        elif args and not kwargs:
            ret = f(self, *args)
        elif not args and kwargs:
            ret = f(self, **kwargs)
        else:
            ret = f(self)
        self._blocked = was
        return ret
    go.__name__ = f.__name__
    return go


def fblocked(f):
    """ Decorator to block access to a single method in a class when that method is called.
    
    Useful for preventing loops in event handlers.    
    """
    @wraps(f)
    def go(self, *args, **kwargs):
        if f._blocked:
            return
        was = f._blocked
        f._blocked = True
        ret = None
        if args and kwargs:
            ret = f(self, *args, **kwargs)
        elif args and not kwargs:
            ret = f(self, *args)
        elif not args and kwargs:
            ret = f(self, **kwargs)
        else:
            ret = f(self)
        f._blocked = was
        return ret
    f._blocked = False
    go.__name__ = f.__name__
    return go


class Unblocker:
    """ instantiate to stack frame to temporarily unblock object or method that is blocked
    with the `blocked` or `fblocked` decorators. """
    def __init__(self, o):
        self.o = o
        self.was = self.o._blocked
        self.o._blocked = False
        
    def __del__(self):
        self.o._blocked = self.was
        