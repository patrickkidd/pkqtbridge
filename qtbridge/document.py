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

    def nextId(self):
        self.setLastItemId(self.lastItemId() + 1)
        return self.lastItemId()

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
                self._tidyLayerOrder()
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
                    self._tidyLayerOrder()
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
            self._tidyLayerOrder()
            self.layerRemoved.emit(item)
        if self.isBatchAddingRemovingItems() and not item in self._batchRemovedItems:
            self._batchRemovedItems.append(item)
        self.itemRemoved.emit(item)

    ## Query interface
            
    def query(self, **kwargs):
        """ Query based on property value. """
        ret = []
        for id, item in self.itemRegistry.items():
            for k, v in kwargs.items():
                prop = item.prop(k)
                if prop and item.prop(k).get() == v:
                    ret.append(item)
        return ret
        
    def query1(self, **kwargs):
        ret = self.query(**kwargs)
        if ret:
            return ret[0]
        
    def find(self, id=None, tags=None, types=None, sort=None):
        """ Match is AND. """
        if id is not None: # exclusive; most common use case
            ret = self.itemRegistry.get(id, None)
        else:
            if types is not None:
                if isinstance(types, list):
                    types = tuple(types)
                elif not isinstance(types, tuple):
                    types = (types,)
            if tags is not None:
                if not isinstance(tags, list):
                    tags = [tags]
            _reverseTags = self.reverseTags() # cache
            ret = []
            for id, item in self.itemRegistry.items():
                if types is not None and not isinstance(item, types):
                    continue
                if tags is not None and not item.hasTags(tags, _reverseTags):
                    continue
                ret.append(item)
        if sort:
            return Property.sortBy(ret, sort)
        else:
            return ret

    def findById(self, id):
        if id is not None:
            return self.find(id=id)

    def itemsWithTags(self, tags=[], kind=Item):
        ret = []
        for id, item in self.itemRegistry.items():
            if isinstance(item, kind) and item.hasTags(tags):
                ret.append(item)
        return sorted(ret)

    ## Layers

    def _resortLayersFromOrder(self):
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

    def _tidyLayerOrder(self):
        """ Set Layer.order based on order of self._layers. """
        was = list(self._layers)
        for i, layer in enumerate(self.layers()):
            layer.setOrder(i, notify=False)
        if self._layers != was:
            self.layerOrderChanged.emit()

