from .pyqt import QObject, QVariant, pyqtSlot, pyqtSignal, QItemSelectionModel, QDateTime, QMessageBox, QApplication, qmlRegisterType
from . import misc, commands
from .document import Document
from .modelhelper import ModelHelper
from .tagsmodel import TagsModel


class DocumentModel(QObject, ModelHelper):


    PROPERTIES = objects.Item.adjustedClassProperties(Document, [
        { 'attr': 'hasActiveLayers', 'type': bool }, # read-only mapping to Document.hasActiveLayers()
    ])

    ModelHelper.registerQtProperties(PROPERTIES)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._nullTimelineModel = TimelineModel(self)
        self._nullTimelineModel.setObjectName('nullTimelineModel')
        self._nullPeopleModel = PeopleModel(self)
        self._nullPeopleModel.setObjectName('nullPeopleModel')
        self.initModelHelper(storage=True)

    def get(self, attr):
        ret = None
        if attr == 'hasActiveLayers':
            if self._document:
                ret = self._document.hasActiveLayers
            else:
                ret = False
        else:
            ret = super().get(attr)
        return ret

    def set(self, attr, value):
        if attr == 'document':
            if self._document:
                self._document.activeLayersChanged.disconnect(self.onActiveLayersChanged)
        super().set(attr, value)
        if attr == 'document':
            if self._document:
                self._document.activeLayersChanged.connect(self.onActiveLayersChanged)
                items = [self._document]
            else:
                items = []
            self._blockRefresh = True
            self.set('items', items)
            self._blockRefresh = False
            self.refreshAllProperties()

    def onActiveLayersChanged(self):
        self.refreshProperty('hasActiveLayers')

    @pyqtSlot(int, result=QVariant)
    def tagsModelForLayer(self, row):
        """ Construct a new TagsModel for each ListView delegate. """
        if row < 0 or row >= self.layerModel.rowCount():
            return None
        layer = self.layerModel.layerForRow(row)
        model = TagsModel(self) # Cache per layer??
        model.document = layer.document()
        model.items = [layer]
        return model



qmlRegisterType(DocumentModel, 'PK.Models', 1, 0, 'DocumentModel')