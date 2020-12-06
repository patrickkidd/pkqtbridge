import os, os.path, sys, traceback
from . import util, version
from .pyqt import *
from .debug import Debug
from .qmlengine import QmlEngine


class Application(QApplication, Debug):
    """ Python prefs, exception logging, abort() prevention, etc. """

    @classmethod
    def prefs():
        return Application.instance()._prefs

    @classmethod
    def onPreConstructor():
        """ Class-virtual. Useful for makign calls before QApplication.__init__() is called. """

    def __init__(self, *args, **kwargs):

        util._prefs = QSettings('mydomain', 'myapp')
        self.prefs().setAutoSave(True)
        self.prefs().setValue('lastVersion', version.VERSION)
        # prefsPath = QFileInfo(self.prefs().fileName()).filePath()

        # Log file

        if not util.IS_DEV and not util.IS_IOS:
            dirPath = os.path.join(util.appDataDir(), util.APP_NAME) # uses applicationName() but it's empty before qApp ctor
            logFilePath = os.path.join(dirPath, 'log.txt')
            if not os.path.isdir(dirPath):
                os.makedirs(dirPath)
            self.logFile = open(logFilePath, 'a+')
            Debug.WRITE = qDebug
        else:
            self.logFile = None

        # Final endpoint for logging

        def qtMessageHandler(msgType, context, msg):
            GREP = [
                # Add in strings here to filter out lines in the log file.
            ]
            for line in GREP:
                if line in msg:
                    return

            # context.file, context.function
            s = qFormatLogMessage(msgType, context, msg) + '\n'
            if (context.file and 'debug.py' in context.file) and context.function == "here":
                s = s.replace('<embedded>(32) ', '')

            sys.stdout.write(s)
            sys.stdout.flush()

            if self.logFile:
                dateString = QDateTime.currentDateTime().toString(Qt.ISODate)
                s = "%s: %s" % (dateString, s)
                # if s[-1] == '\n':
                #     self.logFile.write(s)
                # else:
                #     self.logFile.write(s + '\n')
                self.logFile.write(s)
                self.logFile.flush()
            # Debug(s, newline=True, frame=False)
            # print('%s:%d:%s(): %s' % (
            #     context.file, context.line, context.function, msg))
        qInstallMessageHandler(qtMessageHandler)

        ## Python exception handling

        def no_abort(etype, value, tb):
            """ Prevent a call to abort on exception """
            # global _exc
            # from .mainwindow import MainWindow
            lines = traceback.format_exception(etype, value, tb)
            for line in lines:
                Debug(line[:-1], frame=False)
            #if BUNDLE:
            #    reportException(etype, value, tb)
            # self._excepthook_was(etype, value, tb)
            # if mw and not mw.isInit: # b/c MainWindow isn't shown yet, app hangs.
            #     sys.exit(-1)
            # QMessageBox.critical(mw, 'Internal error', 'An internal error was raised:\n\n' + ''.join(lines))
            # if IS_BUNDLE:
            #     _exc = lines, etype, value, tb
            #     def do_post():
            #         if mw:
            #             mw.post_exception(etype, value, tb)
            #     QTimer.singleShot(100, do_post)
            #     Debug('submitting exception report...')
        self._excepthook_was = sys.excepthook
        sys.excepthook = no_abort

        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True) # before app creation

        self.onPreConstructor()

        super().__init__(*args, **kwargs)

        # Normal init

        self._qmlEngine = QmlEngine(self) # this is always a singleton anyway, so add it here.
        self.osOpenedFile = None

    def deinit(self):
        def iCloudDevPostInit():
            iCloudRoot = CUtil.instance().iCloudDocsPath()
            if iCloudRoot:
                lastiCloudPath = self.prefs().value('lastiCloudPath', defaultValue=None)
                if iCloudRoot != lastiCloudPath:
                    self.prefs().setValue('lastiCloudPath', iCloudRoot)
        iCloudDevPostInit()
        CUtil.instance().deinit()
        CUtil.shutdown()

        sys.excepthook = self._excepthook_was
        self._excepthook_was = None

        if self.logFile:
            self.logFile.close()
            self.logFile = None

    # def onPaletteChanged(self):
    #     self.here(CUtil.isAppleDarkMode())

    def qmlEngine(self):
        return self._qmlEngine

    def event(self, e):
        """ Port to C++ for speed? There aren't many events coming through here actually..."""
        if e.type() == QEvent.FileOpen:
            if util.suffix(e.file()) != util.EXTENSION:
                return False
            # open it up later to avoid a crash
            self.osOpenedFile = e.file()
            commands.trackApp('Open file from Dock')
            return True
        return super().event(e)
