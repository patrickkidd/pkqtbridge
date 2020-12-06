import os, sys
import pytest


for part in ('..',):
    sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), part))
from qtbridge import Debug, version, util, document, objects, Application, DocumentModel
from qtbridge.pyqt import *


version.IS_ALPHA = False
version.IS_BETA = False
version.IS_ALPHA_BETA = False
util.IS_TEST = True
util.ANIM_DURATION_MS = 0
util.QML_LAZY_DELAY_INTERVAL_MS = 0 # total lazy loading
DATA_ROOT = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data')


def pytest_addoption(parser):
    parser.addoption("--attach", action="store_true", help="Wait for an attached debugger before running test")


def pytest_generate_tests(metafunc):
    # The offscreen platform is great for unit tests & CI/CD.
    # but it is more sensitive to widgets not being big enough to
    # expose widgets to mouse events. You can debug this by calling dumpWidget()
    # to see if the thing you are trying to click works.
    os.environ['QT_QPA_PLATFORM'] = 'offscreen'
    attach = metafunc.config.getoption("attach")
    if attach and pytest_generate_tests._first_call:
        util.wait_for_attach()
        pytest_generate_tests._first_call = False
pytest_generate_tests._first_call = True


def dumpWidget(widget):
    global DATA_ROOT
    import os.path, time
    pixmap = QPixmap(widget.size())
    widget.render(pixmap)
    fileDir = os.path.realpath(os.path.join(DATA_ROOT, '..'))
    pngPath = os.path.join(fileDir, 'dump_%s.png' % time.time())
    if not os.path.isdir(fileDir):
        os.mkdir(fileDir)
    pixmap.save(pngPath)
    Debug('Dumped widget to:', pngPath)
    # os.system('open "%s"' % pngPath)


@pytest.yield_fixture(scope='session')
def _qApp_session(request):

    
    yield app
    
    # util.stopProfile()
    app.deinit()


@pytest.yield_fixture
def qApp(_qApp_session, tmp_path, monkeypatch):
    """ Per-unit wrapper around _qApp_session session fixture. """

    app = Application(sys.argv)
    # util.startProfile()

    _path = str(tmp_path)
    monkeypatch.setattr(util, 'appDataDir', lambda: _path)
    yield _qApp_session

    


#####################################################
##
##  App fixtures
##
#####################################################



from pytestqt.qtbot import QtBot

class PKQtBot(QtBot, Debug):

    def waitActive(self, w, timeout=1000):
        w.activateWindow()
        QApplication.instance().processEvents() # ugh....
        super().waitActive(w, timeout)

    def keyClicks(self, *args, **kwargs):
        QTest.keyClicks(*args, **kwargs)

    def qWait(self, ms):
        QTest.qWait(ms)

    def __keyClicks(self, *args, **kwargs):
        w = args[0]
        QTest.mouseClick(w, Qt.LeftButton, Qt.NoModifier) # focus in
        QTest.keyClicks(*args, **kwargs)
        if not isinstance(args[0], QPlainTextEdit):
            QTest.keyClick(w, Qt.Key_Tab) # focus out
            self.waitUntil(lambda: not w.hasFocus())
            # self.qWait(100)
        else:
            w.clearFocus()
            # # just try to focus out
            # aw = QApplication.activeWindow()
            # if aw is None:
            #     w.activateWindow()
            #     QApplication.setActiveWindow(w.window())
            # QApplication.activeWindow().setFocus()

    def keyClicksClear(self, w, unfocus=True):
        """ Clear text in widget. """
        self.mouseClick(w, Qt.LeftButton)
        w.selectAll()
        self.keyClick(w, Qt.Key_Backspace)
        w.editingFinished.emit() # punt
        # if isinstance(w, QLineEdit) and unfocus:
        #     self.keyClick(w, Qt.Key_Tab)
        # else:
        #     w.clearFocus()

    def keyClicksDateEdit(self, dateEdit, s, inTable=False):
        le = dateEdit.lineEdit()
        self.mouseClick(le, Qt.LeftButton)
        self.keyClick(le, Qt.Key_A, Qt.ControlModifier)
        self.keyClick(le, Qt.Key_Backspace)
        super().keyClicks(le, s)
        if inTable:
            self.keyClick(le, Qt.Key_Enter)
        else:
            le.clearFocus()
        if inTable:
            self.wait(10) # processEvents()

    def printTable(self, view, selectedCol=0):
        import sys
        fmt = '{:<20s}'
        print()
        model = view.model()
        selectedRows = set([i.row() for i in view.selectionModel().selectedIndexes()])
        nCols = model.columnCount()
        for col in range(nCols):
            label = model.headerData(col, Qt.Horizontal)
            s = fmt.format(label)
            if col < nCols-1:
                s = s + '| '
            if col == 0:
                iS = ''.ljust(4)
            else:
                iS = ''
            sys.stdout.write('%s %s' % (iS, s))
        sys.stdout.write('\n')
        nCols = model.columnCount()
        for row in range(model.rowCount()):
            if view.isRowHidden(row):
                continue
            for col in range(nCols):
                index = model.index(row, col)
                s = model.data(index, Qt.DisplayRole)
                if isinstance(s, QVariant) and s.isNull():
                    s = ''
                else:
                    s = str(s)
                if view.selectionModel().isSelected(index):
                    x = '[%s]' % s
                else:
                    x = s
                z = fmt.format(x)
                if col < nCols-1:
                    z = z + '| '
                if col == 0:
                    iS = ('%i:' % row).ljust(4)
                else:
                    iS = ''
                sys.stdout.write('%s %s' % (iS, z))
            sys.stdout.write('\n')
        sys.stdout.flush()

    def selectTableViewItem(self, tv, s, column=0, modifiers=Qt.NoModifier):
        foundItems = {}
        for row in range(tv.model().rowCount()):
            index = tv.model().index(row, column)
            tv.scrollTo(index)
            itemP = tv.visualRect(index).center()
            itemS = tv.model().index(row, column).data(Qt.DisplayRole)
            foundItems[row] = itemS
            if not itemP.isNull() and itemS == s:
                self.mouseClick(tv.viewport(), Qt.LeftButton, modifiers, itemP)
        if not s in foundItems.values():
            self.printTable(tv, column)
        assert s in foundItems.values()


    def clickTabWidgetPage(self, tabWidget, iPage):
        self.mouseClick(tabWidget.tabBar(), Qt.LeftButton, Qt.NoModifier, tabWidget.tabBar().tabRect(iPage).center())

    def assertNoTableViewItem(self, tv, text, column):
        count = 0
        for row in range(tv.model().rowCount()):
            index = tv.model().index(row, column)
            itemS = tv.model().index(row, column).data(Qt.DisplayRole)
            if itemS == text:
                count += 1
        assert count == 0

    def qWaitForMessageBox(self, action, contains=None, handleClick=None):
        from PyQt5.QtWidgets import QAbstractButton
        msgBoxAccepted = util.Condition()
        def acceptMessageBox():
            # def isWindowUp():
            #     return bool(QApplication.activeModalWidget())
            # self.waitUntil(isWindowUp, 2000)
            widget = QApplication.activeModalWidget()
            if widget:
                if contains:
                    assert contains in widget.text()
                if handleClick and handleClick():
                    msgBoxAccepted()
                    msgBoxAccepted.timer.stop()
                elif isinstance(widget, QMessageBox):
                    okButton = widget.button(QMessageBox.Ok)
                    widget.buttonClicked[QAbstractButton].connect(msgBoxAccepted)
                    msgBoxAccepted()
                    self.mouseClick(okButton, Qt.LeftButton)
                    msgBoxAccepted.timer.stop()
        msgBoxAccepted.timer = QTimer(QApplication.instance())
        msgBoxAccepted.timer.timeout.connect(acceptMessageBox)
        msgBoxAccepted.timer.start(100)
        action()
        assert msgBoxAccepted.wait() == True
    
    def clickYesAfter(self, action):
        def doClickYes():
            widget = QApplication.activeModalWidget()
            if isinstance(widget, QMessageBox):
                button = widget.button(QMessageBox.Yes)
                assert button
                self.mouseClick(button, Qt.LeftButton)
                return True
        self.qWaitForMessageBox(action, handleClick=doClickYes)
        
    def clickNoAfter(self, action):
        def doClickNo():
            widget = QApplication.activeModalWidget()
            if isinstance(widget, QMessageBox):
                button = widget.button(QMessageBox.No)
                assert button
                self.mouseClick(button, Qt.LeftButton)
                return True
        self.qWaitForMessageBox(action, handleClick=doClickNo)
            
    def clickOkAfter(self, action):
        def doClickOk():
            widget = QApplication.activeModalWidget()
            if isinstance(widget, QMessageBox):
                button = QApplication.activeModalWidget().button(QMessageBox.Ok)
                assert button
                self.mouseClick(button, Qt.LeftButton)
                return True
        self.qWaitForMessageBox(action, handleClick=doClickOk)
        
    def hitEscapeAfter(self, action):
        def doHitEscape():
            widget = QApplication.activeModalWidget()
            if isinstance(widget, QMessageBox):
                self.keyClicks(QApplication.activeModalWidget(), Qt.Key_Escape)
                return True
        self.qWaitForMessageBox(action, handleClick=doHitEscape)

@pytest.yield_fixture
def qtbot(qApp, request):
    """ Overridden to use our qApp, because the old one was calling abort(). """
    result = PKQtBot(request)
    util.qtbot = result
    
    yield result


@pytest.fixture
def simpleDocument(qApp, request):
    s = document.Document()
    p1 = objects.Person(name='p1')
    p2 = objects.Person(name='p2')
    m = objects.Marriage(p1, p2)
    p = objects.Person(name='p')
    p.setParents(m)
    s.addItem(p1)
    s.addItem(p2)
    s.addItem(m)
    s.addItem(p)
    def cleanup():
        s.deinit()
    request.addfinalizer(cleanup)
    return s

