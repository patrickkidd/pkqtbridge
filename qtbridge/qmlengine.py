from .pyqt import QQmlEngine
from . import Debug, util, qmlutil


class QmlEngine(QQmlEngine, Debug):
    """ The global singleton; Manage global objects.
    
    Sets `util` app globals for qml; mapped in qmlutil.py application globals to root qml context.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        for path in util.QML_IMPORT_PATHS:
            self.addImportPath(path)
        self.util = qmlutil.QmlUtil(self)
        self.rootContext().setContextProperty('util', self.util)
        self.util.initColors()
