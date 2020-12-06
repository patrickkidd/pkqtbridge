from .pyqt import pyqtSignal, QDate
from .item import Item
from .property import Property




class Document(Item):
    """ Contains all of the items. Manages unique item ids. """

    _isDocument = True

    itemAdded = pyqtSignal(Item)
    itemRemoved = pyqtSignal(Item)
    propertyChanged = pyqtSignal(Property)
    layerAdded = pyqtSignal(Layer)
    layerChanged = pyqtSignal(Property)
    layerRemoved = pyqtSignal(Layer)
    activeLayersChanged = pyqtSignal(list)
    layerOrderChanged = pyqtSignal()

    Item.registerProperties((
        { 'attr': 'lastItemId', 'default': -1, 'notify': False },
    ))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._isInitializing = True
        self._batchAddRemoveStackLevel = 0
        self._updatingAll = False # indicates a static update is occuring, i.e. no animations, etc
        self._areActiveLayersChanging = False
        self._itemRegistry = {}
        self._layers = []
        self._activeLayers = []

    def addItem(self, item, register=True):
        if (isinstance(item, QGraphicsItem) or isinstance(item, QGraphicsObject)) and not item.document() is self:
            super().addItem(item)
        if not isinstance(item, Item):
            return
        if register:
            if item.id is None:
                item.id = self.nextId()
            elif item.id > self.lastItemId():
                self.setLastItemId(item.id) # bump
            elif self.itemRegistry.get(item.id, None) is item: # already registered
                return
            self.itemRegistry[item.id] = item
        ## Signals
        if not self.isBatchAddingRemovingItems():
            item.updateAll()
        if item.isLayer:
            self._layers.append(item)
            item.setDocument(self)
            if not self.isBatchAddingRemovingItems():
                self.tidyLayerOrder()
            self.layerAdded.emit(item)
            if not self.isBatchAddingRemovingItems():
                if item.active():
                    self.updateActiveLayers()
        item.addPropertyListener(self)
        item.onRegistered(self)
        if self.isBatchAddingRemovingItems() and not item in self._batchAddedItems:
            self._batchAddedItems.append(item)
        self.itemAdded.emit(item)
        return item

    def addItems(self, *args):
        self.setBatchAddingRemovingItems(True)
        for item in args:
            self.addItem(item)
        self.setBatchAddingRemovingItems(False)

    def isBatchAddingRemovingItems(self):
        return self._batchAddRemoveStackLevel > 0

    def setBatchAddingRemovingItems(self, on):
        if on:
            self._batchAddRemoveStackLevel += 1
            self._batchAddedItems = []
            self._batchRemovedItems = []
        else:
            self._batchAddRemoveStackLevel -= 1
            assert self._batchAddRemoveStackLevel >= 0
            if self._batchAddRemoveStackLevel == 0:
                if len([x for x in (self._batchAddedItems + self._batchRemovedItems) if isinstance(x, Layer)]) > 0:
                    self.tidyLayerOrder()
                self.updateAll()
                self._batchAddedItems = []
                self._batchRemovedItems = []

    def removeItem(self, item):
        if not isinstance(item, Item):
            return
        # deregister
        if not item.id in self.itemRegistry:
            return
        del self.itemRegistry[item.id]
        item.onDeregistered(self)
        item.removePropertyListener(self)
        # I think it's ok to skip signals when deinitializing
        if self.isDeinitializing:
            return
        ## Signals
        if item.isLayer:
            self._layers.remove(item)
            self.tidyLayerOrder()
            self.layerRemoved.emit(item)
        if self.isBatchAddingRemovingItems() and not item in self._batchRemovedItems:
            self._batchRemovedItems.append(item)
        self.itemRemoved.emit(item)

    def resortLayersFromOrder(self):
        # re-sort iternal layer list.
        was = list(self._layers)
        def layerOrder(layer):
            if layer.order() is layer.prop('order').default:
                return sys.maxsize-1
            else:
                return layer.order()
        self._layers = sorted(self.layers(), key=layerOrder)
        if self._layers != was:
            self.layerOrderChanged.emit()

    def tidyLayerOrder(self):
        """ Set Layer.order based on order of self._layers. """
        was = list(self._layers)
        for i, layer in enumerate(self.layers()):
            layer.setOrder(i, notify=False)
        if self._layers != was:
            self.layerOrderChanged.emit()

