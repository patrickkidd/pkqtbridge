##
## Qt UndoCommand support, including compressing `Property` commands.
##
##

from .pyqt import QUndoStack, QUndoCommand
from . import util
from . import Application


class UndoStack(QUndoStack, util.Debug):
    """ QUndoStack that tracks commands for analytics. """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.lastId = None

    def push(self, cmd):
        """ Track analytics for non-compressed commands. """
        s = None
        if isinstance(cmd.ANALYTICS, str):
            s = 'Commands: ' + cmd.ANALYTICS
        elif cmd.ANALYTICS is True and (cmd.id() == -1 or cmd.id() != self.lastId):
            s = 'Commands: ' + cmd.text()
        if s:
            self.track(s, cmd.analyticsProperties())
        super().push(cmd)
        self.lastId = cmd.id()

    def track(self, eventName, properties={}):
        if not Application.prefs() or util.IS_DEV or util.IS_IOS:
            return
        self.here(eventName)
        enableAppUsageAnalytics = Application.prefs().value('enableAppUsageAnalytics', defaultValue=True, type=bool)
        if enableAppUsageAnalytics:
            ### Send to some analytics API here.
            pass

def track(eventName, properties={}):
    return stack().track(eventName, properties)

def trackApp(eventName, properties={}):
    return track('Application: ' + eventName, properties)

def trackAction(eventName, properties={}):
    return track('Action: ' + eventName, properties)

def trackView(eventName, properties={}):
    return track('View: ' + eventName, properties)



_stack = UndoStack()
def stack():
    """ The global undo stack. You may not like a global, but I do. """
    global _stack
    return _stack


lastId = 10 # Necessary for QUndoStack compression. Value of `10` is arbitrary.
def nextId():
    global lastId
    lastId = lastId + 1
    return lastId


class UndoCommand(QUndoCommand, util.Debug):

    ANALYTICS = True

    def __init__(self, text, id=-1):
        super().__init__(text)
        self._id = id

    def id(self):
        return self._id

    def analyticsProperties(self):
        return {}


class AddItem(UndoCommand):
    """ Add an item to the document.
    
    You may want to add a `AddItems` command like the `RemoveItems` command.
    """

    def __init__(self, document, item):
        super().__init__('Add %s' % item.itemName())
        self.document = document
        self.item = item

    def redo(self):
        self.document.addItem(self.item)

    def undo(self):
        self.document.removeItem(self.item)

def addItem(*args):
    cmd = AddItem(*args)
    stack().push(cmd)
    return cmd.item
    
    
class RemoveItems(UndoCommand):
    """ Remove items from the document. """

    def __init__(self, document, items):
        super().__init__('Remove items')
        self.document = document
        if isinstance(items, list):
            self.items = list(items)
        else:
            self.items = [items]

        # Keep track of a list of each kind of items at the top level to
        # detach their relationships and then re-attach them after an
        # undo.
        # Re-implement this in subclasses           
        self._unmapped = {
            'layers': [],
            'layerProperties': {}
        }

        def mapItem(item):
            for layer in document.layers():
                layerEntries = {}
                for prop in item.props:
                    if prop.layered:
                        value, ok = layer.getItemProperty(item.id, prop.name())
                        if ok:
                            if not item.id in layerEntries:
                                layerEntries[item.id] = {}
                            layerEntries[item.id][prop.name()] = {
                                'prop': prop,
                                'was': value
                            }
                if layerEntries:
                    if not layer in self._unmapped['layerProperties']:
                        self._unmapped['layerProperties'][layer] = {}
                    self._unmapped['layerProperties'][layer].update(layerEntries)

        # Map anything that will be directly removed or removed as a dependency.
        # Do the mappings first before the data structure is altered
        for item in self.items:
            if item.isLayer:
                self._unmapped['layers'].append({
                    'layer': item,
                })
            
            mapItem(item)


    def redo(self):
        self.document.setBatchAddingRemovingItems(True)
        for item in self.items:
                
            if item.isLayer:
                for layerItem in self.document.layerItems():
                    if item.id in layerItem.layers():
                        layerItem.layers().remove(item.id)
                    if not layerItem.layers(): # orphaned now
                        self.document.removeItem(layerItem)
                self.document.removeItem(item)

        for layer, itemEntries in self._unmapped['layerProperties'].items():
            for itemId, propEntries in itemEntries.items():
                for propName, entry in propEntries.items():
                    layer.resetItemProperty(entry['prop'])

        self.document.setBatchAddingRemovingItems(False)

    def undo(self):
        self.document.setBatchAddingRemovingItems(True)
        #
        for layer, itemEntries in self._unmapped['layerProperties'].items():
            for itemId, propEntries in itemEntries.items():
                for propName, entry in propEntries.items():
                    layer.setItemProperty(itemId, entry['prop'].name(), entry['was'])
        #
        for entry in self._unmapped['layers']: # before layer items
            self.document.addItem(entry['layer'])
        self.document.setBatchAddingRemovingItems(False)


def removeItems(*args):
    stack().push(RemoveItems(*args))
 


class SetItemProperty(UndoCommand):
    """ Only ever called from Property.set(undo=bool|int). """
    
    ANALYTICS = 'SetItemProperty'
    
    def __init__(self, prop, value, layers=[], id=-1):
        if layers:
            super().__init__('Set %s on layers' % prop.name(), id)
        else:
            super().__init__('Set %s' % prop.name(), id)
        self.data = {}
        def _addEntry(layer, prop, value, was):
            if not layer in self.data:
                self.data[layer] = {}
            if not prop.item.id in self.data[layer]:
                self.data[layer][prop.item.id] = {}
            self.data[layer][prop.item.id][prop.name()] = {
                'value': value,
                'prop': prop
            }
            self.data[layer][prop.item.id][prop.name()]['wasSet'] = prop.isset()
            if not was is None:
                self.data[layer][prop.item.id][prop.name()]['was'] = was
        if layers:
            for layer in layers:
                was, ok = layer.getItemProperty(prop.item.id, prop.name())
                _addEntry(layer, prop, value, was)
        else:
            _addEntry(None, prop, value, prop.get())
        self.firstTime = True # yep

    def redo(self):
        if self.firstTime:
            self.firstTime = False
            return
        for layer, itemData in self.data.items():
            for itemId, props in itemData.items():
                for propName, data in props.items():
                    if layer:
                        layer.setItemProperty(itemId, propName, data['value'])
                        data['prop'].onActiveLayersChanged()
                    else:
                        data['prop'].set(data['value'], force=True)

    def undo(self):
        for layer, itemData in self.data.items():
            for itemId, props in itemData.items():
                for propName, data in props.items():
                    if layer:
                        if data['wasSet'] and 'was' in data:
                            layer.setItemProperty(itemId, propName, data['was'])
                        else:
                            layer.resetItemProperty(data['prop'])
                        data['prop'].onActiveLayersChanged()
                    else:
                        if data['wasSet'] and 'was' in data:
                            data['prop'].set(data['was'], force=True)
                        else:
                            data['prop'].reset()


    def mergeWith(self, other):
        util.deepMerge(self.data, other.data, ignore='was')
        return True


class ResetItemProperty(UndoCommand):
    """ Only used from Property.reset(undo=bool|int). """
    def __init__(self, prop, layers=[], id=-1):
        item = prop.item
        super().__init__('Reset %s' % prop.name(), id)
        self.data = {}
        if prop.layered:
            # only take `was` values stored on selected layers
            for layer in layers:
                self.data[layer] = {}
                x, ok = layer.getItemProperty(prop.item.id, prop.name())
                if ok:
                    self.data[layer] = {
                        prop: x
                    }
        else:
            self.data[None] = {
                prop: prop.get()
            }
        self.firstTime = True

    def redo(self):
        if self.firstTime:
            self.firstTime = False
            return
        for layer, propEntry in self.data.items():
            for prop, was in propEntry.items():
                if layer:
                    layer.resetItemProperty(prop)
                else:
                    prop.reset()
        self.firstTime = False

    def undo(self):
        for layer, propEntry in self.data.items():
            for prop, was in propEntry.items():
                if layer:
                    layer.setItemProperty(prop.item.id, prop.name(), was)
                else:
                    prop.set(was)

    def mergeWith(self, other):
        util.deepMerge(self.data, other.data, ignore='was')
        return True


class AddLayer(UndoCommand):

    ANALYTICS = 'Add layer'
    
    def __init__(self, document, layer):
        super().__init__('Add layer %s' % layer.itemName())
        self.document = document
        self.layer = layer

    def redo(self):
        layers = self.document.layers()
        iOrder = len(self.document.layers())
        self.layer.setOrder(iOrder) # append
        self.document.addItem(self.layer)

    def undo(self):
        self.document.removeItem(self.layer)
        for i, layer in enumerate(self.document.layers()):
            self.layer.setOrder(i, notify=False)


def addLayer(document, layer):
    cmd = AddLayer(document, layer)
    stack().push(cmd)
    return cmd.layer


class SetLayerOrder(UndoCommand):

    ANALYTICS = 'Set layer order'

    def __init__(self, document, layers):
        super().__init__('Set layer order')
        self.document = document
        self.oldLayers = document.layers() # sorted
        self.newLayers = layers # new sorted

    def redo(self):
        for i, layer in enumerate(self.newLayers):
            layer.setOrder(i)
        self.document.resortLayersFromOrder()
        
    def undo(self):
        for i, layer in enumerate(self.oldLayers): # re-init order
            layer.setOrder(i)
        self.document.resortLayersFromOrder()

def setLayerOrder(document, layers):
    stack().push(SetLayerOrder(document, layers))



class CreateTag(UndoCommand):

    ANALYTICS = 'Create tag'
    
    def __init__(self, document, tag):
        super().__init__('Create tag "%s"' % tag)
        self.document = document
        self.tag = tag

    def redo(self):
        self.document.addTag(self.tag)

    def undo(self):
        self.document.removeTag(self.tag)

def createTag(*args):
    stack().push(CreateTag(*args))


class DeleteTag(UndoCommand):

    ANALYTICS = 'Delete tag'
    
    def __init__(self, document, tag):
        super().__init__('Delete tag "%s"' % tag)
        self.document = document
        self.tag = tag
        self.items = []

    def redo(self):
        self.items = self.document.find(tags=self.tag)
        self.document.removeTag(self.tag)
        for item in self.items:
            item.unsetTag(self.tag)

    def undo(self):
        self.document.addTag(self.tag)
        for item in self.items:
            item.setTag(self.tag)


def deleteTag(*args):
    stack().push(DeleteTag(*args))


class RenameTag(UndoCommand):

    ANALYTICS = 'Rename tag'
    
    def __init__(self, document, old, new):
        super().__init__('Rename tag "%s" to "%s"' % (old, new))
        self.document = document
        self.old = old
        self.new = new

    def redo(self):
        self.document.renameTag(self.old, self.new)

    def undo(self):
        self.document.renameTag(self.new, self.old)


def renameTag(*args):
    stack().push(RenameTag(*args))


class SetTag(UndoCommand):

    ANALYTICS = 'Set tag'
    
    def __init__(self, item, tag):
        super().__init__('Set tag "%s" on <%s>' % (tag, item.itemName()))
        self.item = item
        self.tag = tag

    def redo(self):
        self.item.setTag(self.tag)

    def undo(self):
        self.item.unsetTag(self.tag)


def setTag(*args):
    stack().push(SetTag(*args))


class UnsetTag(UndoCommand):

    ANALYTICS = 'Unset tag'
    
    def __init__(self, item, tag):
        super().__init__('Unset tag "%s" on <%s>' % (tag, item.itemName()))
        self.item = item
        self.tag = tag

    def redo(self):
        self.item.unsetTag(self.tag)

    def undo(self):
        self.item.setTag(self.tag)


def unsetTag(*args):
    stack().push(UnsetTag(*args))


