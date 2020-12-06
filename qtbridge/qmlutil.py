#####################################################
##
##  Qml
##
#####################################################

import time
from .pyqt import *
from . import util
from .qobjecthelper import QObjectHelper


def find_global_type(attr):
    value = getattr(util, attr)
    if isinstance(value, int): # true for int's and PyQt enums
        return int
    else:
        return type(value)


class QmlUtil(QObject, QObjectHelper):
    """ Maps the `util` module as an app-level global in qml. """

    CONSTANTS = [
        'QRC', 'QRC_QML',
        'IS_MAC', 'IS_IOS', 'IS_WINDOWS'
        'ANIM_DURATION_MS',
        'ANIM_EASING',
        'FONT_FAMILY',
        'FONT_FAMILY_TITLE',
        'TEXT_FONT_SIZE',
        'HELP_FONT_SIZE',
        'QML_MARGINS',
        'QML_SPACING',
        'QML_TITLE_FONT_SIZE',
        'QML_SMALL_TITLE_FONT_SIZE',
        'QML_ITEM_HEIGHT',
        'QML_ITEM_LARGE_HEIGHT',
        'QML_SMALL_BUTTON_WIDTH',
        'QML_HEADER_HEIGHT',
        'QML_ITEM_BG',
        'QML_HEADER_BG',
        'QML_WINDOW_BG',
        'QML_CONTROL_BG',
        'QML_TEXT_COLOR',
        'QML_DROP_SHADOW_COLOR',
        'QML_SELECTION_TEXT_COLOR',
        'QML_HIGHLIGHT_TEXT_COLOR',
        'QML_ACTIVE_TEXT_COLOR',
        'QML_INACTIVE_TEXT_COLOR',
        'QML_HIGHLIGHT_COLOR',
        'QML_SELECTION_COLOR',
        'QML_ITEM_ALTERNATE_BG',
        'QML_ITEM_BORDER_COLOR',
        'QML_SAME_DATE_HIGHLIGHT_COLOR',
    ]
    QObjectHelper.registerQtProperties([ { 'attr': attr,
                                           'global': True,
                                           # 'constant': True,
                                           'type': find_global_type(attr)
                                           } for attr in CONSTANTS], globalContext=util.__dict__)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('util')
        QApplication.instance().paletteChanged.connect(self.initColors)
        self._httpReplies = {}
        self._lastHttpRequestId = 0
        self._httpRequests = []
        self.initQObjectHelper()

    def initColors(self):
        util.IS_APPLE_DARK_MODE = util.isAppleDarkMode()
        util.HIGHLIGHT_COLOR = None
        if QApplication.instance():
            util.SELECTION_COLOR = CUtil.instance().appleControlAccentColor() # requires app instance?
            # attempt to make very light selection colors show up better on white background
            # if not IS_APPLE_DARK_MODE and luminanceOf(SELECTION_COLOR) > .7:
            #     SELECTION_COLOR = QColor(255, 0, 0, 150) # from 1.0.0b9
            util.HIGHLIGHT_COLOR = util.lightenOpacity(util.SELECTION_COLOR, .5)
            if QApplication.activeWindow():
                palette = QApplication.activeWindow().palette()
            else:
                palette = QApplication.palette() # should probably replace with
        else:
            util.SELECTION_COLOR = QColor(255, 0, 0, 150) # from 1.0.0b9
            palette = QPalette()
        # QColor
        # util.TEXT_COLOR = palette.color(QPalette.Text)
        # util.ACTIVE_TEXT_COLOR = palette.color(QPalette.Active, QPalette.Text)
        if util.IS_APPLE_DARK_MODE:
            util.TEXT_COLOR = QColor(Qt.white)
            util.ACTIVE_TEXT_COLOR = QColor(Qt.white)
        else:
            util.TEXT_COLOR = QColor(Qt.black)
            util.ACTIVE_TEXT_COLOR = QColor(Qt.black)
        util.PEN = QPen(QBrush(util.TEXT_COLOR), 3, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        if util.HIGHLIGHT_COLOR is None:
            util.HIGHLIGHT_COLOR = palette.color(QPalette.Highlight)
        if util.SAME_DATE_HIGHLIGHT_COLOR is None:
            util.SAME_DATE_HIGHLIGHT_COLOR = lightenOpacity(util.SELECTION_COLOR, .7)
        util.SELECTION_TEXT_COLOR = util.contrastTo(util.SELECTION_COLOR)
        util.HIGHLIGHT_TEXT_COLOR = util.contrastTo(util.HIGHLIGHT_COLOR)
        util.HOVER_COLOR = util.SELECTION_COLOR
        # Dark mode theming
        if util.IS_APPLE_DARK_MODE:
            util.WINDOW_BG = QColor('#1e1e1e')
            util.SNAP_PEN = QPen(util.SELECTION_COLOR.lighter(150), .5)
            util.GRID_COLOR = QColor('#767676')
            util.NODAL_COLOR = QColor('#fcf5c9')
            util.QML_ITEM_BG = '#373534'
            util.QML_ITEM_ALTERNATE_BG = '#2d2b2a'
            util.QML_ITEM_BORDER_COLOR = '#4d4c4c'
            util.QML_HEADER_BG = '#323232'
            util.CONTROL_BG = QColor(util.QML_ITEM_ALTERNATE_BG)
            # util.INACTIVE_TEXT_COLOR = palette.color(QPalette.Disabled, QPalette.Text) # doesn't work
            util.INACTIVE_TEXT_COLOR = util.CONTROL_BG.lighter(160) # workaround
            util.DROP_SHADOW_COLOR = QColor(util.QML_HEADER_BG).lighter(110)
        else:
            util.WINDOW_BG = QColor('white')
            util.CONTROL_BG = QColor('#e0e0e0')
            util.GRID_COLOR = QColor('lightGrey')
            util.SNAP_PEN = QPen(QColor(0, 0, 255, 100), .5)
            util.NODAL_COLOR = QColor('pink')
            util.QML_ITEM_BG = 'white'
            util.QML_ITEM_ALTERNATE_BG = '#eee'
            util.QML_ITEM_BORDER_COLOR = 'lightGrey'
            util.QML_HEADER_BG = 'white'
            # util.QML_CONTROL_BG = '#ffffff'
            # util.INACTIVE_TEXT_COLOR = palette.color(QPalette.Disabled, QPalette.Text) # doesn't work
            util.INACTIVE_TEXT_COLOR = QColor('grey') # workaround
            util.DROP_SHADOW_COLOR = QColor(util.QML_HEADER_BG).darker(105)
        util.SELECTION_PEN = QPen(util.SELECTION_COLOR, 3)
        # c = QColor(util.SELECTION_COLOR.lighter(150))
        # c.setAlpha(30)
        util.SELECTION_BRUSH = QBrush(util.HIGHLIGHT_COLOR)
        util.HOVER_PEN = util.SELECTION_PEN
        util.HOVER_BRUSH = util.SELECTION_BRUSH
        # Qml
        util.QML_WINDOW_BG = util.WINDOW_BG.name()
        util.QML_CONTROL_BG = util.CONTROL_BG.name()
        util.QML_TEXT_COLOR = util.TEXT_COLOR.name()
        util.QML_DROP_SHADOW_COLOR = util.DROP_SHADOW_COLOR.name()
        util.QML_INACTIVE_TEXT_COLOR = util.INACTIVE_TEXT_COLOR.name()
        util.QML_ACTIVE_TEXT_COLOR = util.ACTIVE_TEXT_COLOR.name()
        util.QML_SELECTION_COLOR = util.SELECTION_COLOR.name()
        util.QML_SELECTION_TEXT_COLOR = util.SELECTION_TEXT_COLOR.name()
        util.QML_HIGHLIGHT_TEXT_COLOR = util.HIGHLIGHT_TEXT_COLOR.name()
        util.QML_HIGHLIGHT_COLOR = util.HIGHLIGHT_COLOR.name() # also current
        #
        self.refreshAllProperties()

    @pyqtSlot(QVariant, str, result=QVariant)
    def pyCall(self, o, attr):
        x = getattr(o, attr)
        if callable(x):
            return x()
        else:
            return x

    @pyqtSlot(QItemSelectionModel, QModelIndex, QModelIndex, int)
    def doItemSelection(self, selectionModel, fromIndex, toIndex, flags):
        """ Don't know how to call `select(selection, flags)` from Qml. """
        _flags = QItemSelectionModel.SelectionFlags(flags)
        selectionModel.select(QItemSelection(fromIndex, toIndex), _flags)

    @pyqtSlot(QItemSelectionModel, list, int)
    def doRowsSelection(self, selectionModel, rows, flags):
        _flags = QItemSelectionModel.SelectionFlags(flags)
        model = selectionModel.model()
        selection = QItemSelection()
        for row in rows:
            index = model.index(row, 1)
            selection.select(index, index)
        selectionModel.select(selection, _flags)

    @pyqtSlot(QItemSelectionModel, int, result=bool)
    def isRowSelected(self, selectionModel, row):
        if row >= selectionModel.model().rowCount(): # occurs on deinit
            return False
        else:
            return selectionModel.isRowSelected(row, selectionModel.model().index(-1, -1))

    @pyqtSlot(QAbstractItemModel)
    def printModel(self, model):
        util.printModel(model)

    @pyqtSlot(result=float)
    def time(self):
        return time.time()

    @pyqtSlot(bool, bool, bool, result=str)
    def itemBgColor(self, selected, current, alternate):
        """ Dynamic color depends on item disposition. """
        if selected:
            return self.QML_SELECTION_COLOR
        elif current:
            return self.QML_HIGHLIGHT_COLOR
        elif alternate:
            return self.QML_ITEM_ALTERNATE_BG
        else:
            return self.QML_ITEM_BG
    
    @pyqtSlot(bool, bool, result=str)
    def textColor(self, selected, current):
        """ Dynamic color depends on item disposition. """
        if selected:
            return self.QML_SELECTION_TEXT_COLOR
        elif current:
            return self.QML_HIGHLIGHT_TEXT_COLOR
        else:
            return self.QML_TEXT_COLOR

    @pyqtSlot(QColor, result=QColor)
    def contrastTo(self, color):
        return util.contrastTo(color)

    ## QMessageBox accessors

    @pyqtSlot(str, str, result=bool)
    def questionBox(self, title, text):
        btn = QMessageBox.question(QApplication.activeWindow(), title, text)
        return btn == QMessageBox.Yes

    @pyqtSlot(str, str)
    def informationBox(self, title, text):
        QMessageBox.information(QApplication.activeWindow(), title, text)

    @pyqtSlot(str, str)
    def criticalBox(self, title, text):
        QMessageBox.critical(QApplication.activeWindow(), title, text)

