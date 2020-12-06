from .pyqt import pyqtSignal
from . import util, widgets
from .qmlwidgethelper import QmlWidgetHelper


class QmlDrawer(widgets.Drawer, QmlWidgetHelper):

    QmlWidgetHelper.registerQmlMethods([
        { 'name': 'onInspect' },
        { 'name': 'removeSelection' },
        { 'name': 'setCurrentTab' },
        { 'name': 'currentTab', 'return': True }
    ])

    canInspectChanged = pyqtSignal()
    
    def __init__(self, source,
                 parent=None,
                 resizable=True,
                 propSheetModel=None,
                 objectName=None,
                 documentModel=None): # dev
        super().__init__(parent=parent, resizable=resizable)
        if objectName is not None:
            self.setObjectName(objectName)
        if util.isInstance(parent, 'DocumentView'):
            self._documentView = parent
        else:
            self._documentView = None
        self.propSheetModel = propSheetModel
        self.initQmlWidgetHelper(source, documentModel=documentModel)
        self.checkInitQml()

    def documentView(self):
        return self._documentView

    def onInitQml(self):
        super().onInitQml()
        self.qml.rootObject().done.connect(self.onDone)
        if hasattr(self.qml.rootObject(), 'resize'):
            self.qml.rootObject().resize.connect(self.onResize)
        if hasattr(self.qml.rootObject(), 'canInspectChanged'):
            self.qml.rootObject().canInspectChanged.connect(self.canInspectChanged)
        if hasattr(self.qml.rootObject(), 'isDrawerOpenChanged'):
            self.qml.rootObject().isDrawerOpenChanged.connect(self.onIsDrawerOpenChanged)
        self.qml.rootObject().setProperty('expanded', self.expanded)

    def deinit(self):
        super().deinit()
        if hasattr(self, 'qml'):
            model = self.rootProp(self.propSheetModel)
            if model and model.items:
                model.resetItems()
            if model and model.document:
                model.resetDocument()

    def show(self, items=[], tab=None, **kwargs):
        if not type(items) == list:
            items = [items]
        self.checkInitQml()
        super().show(**kwargs)
        if self.propSheetModel:
            if not self.isQmlReady():
                raise RuntimeError('QmlWidgetHelper not initialized for', self)
            self.rootProp(self.propSheetModel).items = items
        self.qml.setFocus()
        self.setCurrentTab(tab)

    def hide(self, **kwargs):
        passedCB = kwargs.get('callback')
        def onHidden():
            if self.isQmlReady():
                self.qml.rootObject().forceActiveFocus()
                focusResetter = self.qml.rootObject().property('focusResetter')
                if focusResetter:
                    focusResetter.forceActiveFocus()
                if self.propSheetModel:
                    self.rootProp(self.propSheetModel).reset('items')
                if hasattr(self.qml.rootObject(), 'hidden'):
                    self.qml.rootObject().hidden.emit()
            if passedCB:
                passedCB()
        _kwargs = dict(kwargs)
        _kwargs['callback'] = onHidden
        super().hide(**_kwargs)

    def onExpandAnimationFinished(self):
        super().onExpandAnimationFinished()
        if hasattr(self, 'qml'):
            self.qml.rootObject().setProperty('expanded', self.expanded)

    def setCurrentTabIndex(self, x):
        self.checkInitQml()
        if self.hasItem('stack'):
            self.setItemProp('stack', 'currentIndex', x)

    def nextTab(self):
        if self.hasItem('tabBar'):
            x = self.itemProp('tabBar', 'currentIndex')
            count = self.itemProp('tabBar', 'count')
            currentIndex = min(x + 1, count - 1)
            self.setCurrentTabIndex(currentIndex)

    def prevTab(self):
        if self.hasItem('tabBar'):
            x = self.itemProp('tabBar', 'currentIndex')
            count = self.itemProp('tabBar', 'count')
            currentIndex = max(x - 1, 0)
            self.setCurrentTabIndex(currentIndex)
        
    def onIsDrawerOpenChanged(self):
        x = self.qml.rootObject().property('isDrawerOpen')
        self.setLockResizeHandle(x)


        
def __test__(document, parent):
    from .modelhelper import ModelHelper
    w = QmlPropertySheet(parent)
    model = ModelHelper()
    w.initQml(":/qml/Test.qml", model=model)
    util.printQObject(w)
    parent.resize(800, 600)
    return w
