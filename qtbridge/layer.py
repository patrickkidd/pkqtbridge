import copy
from .item import Item


class Layer(Item):

    Item.registerProperties((
        { 'attr': 'order', 'type': int, 'default': -1 },
        { 'attr': 'name' },
        { 'attr': 'description' },
        { 'attr': 'active', 'type': bool, 'default': False },
        { 'attr': 'itemProperties', 'type': dict }
    ))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.isLayer = True
        self._document = kwargs.get('document')
        if not 'itemProperties' in kwargs: # avoid shared default value instance
            self.prop('itemProperties').set({}, notify=False)

    def __repr__(self):
        return super().__repr__(exclude='itemProperties')

    def __lt__(self, other):
        if self.name() is not None and other.name() is None:
            return True
        elif self.name() is None and other.name() is not None:
            return False
        elif self.name() is None and other.name() is None:
            return True
        return self.name() < other.name()

    ## Marshalling

    def clone(self, document):
        x = super().clone(document)
        stuff = copy.deepcopy(self.itemProperties())
        x.prop('itemProperties').set(None, notify=False) # avoid equality check
        x.prop('itemProperties').set(stuff, notify=False)
        return x

    def remap(self, map):
        """ TODO: Map itemProperties. """
        return False

    ## Item property storage

    def itemName(self):
        return self.name()

    def getItemProperty(self, itemId, propName):
        # {
        #     id: {
        #         'propName': value,
        #         'propName': value
        #     }
        # }
        values = self.itemProperties().get(itemId)
        if values and propName in values:
            # self.here(self.id, itemId, propName, values[propName])
            return values[propName], True
        else:
            # self.here(self.id, itemId, propName, None)
            return None, False

    def setItemProperty(self, itemId, propName, value):
        props = self.itemProperties()
        if itemId in props:
            values = props[itemId]
        else:
            values = {}
            props[itemId] = values
        values[propName] = value
        self.setItemProperties(props, notify=False) # noop?
        item = self.document().find(itemId)

    def resetItemProperty(self, prop):
        """ Called from Property.reset. """
        props = self.itemProperties()
        itemProps = props.get(prop.item.id)
        if not itemProps:
            return
        changed = False
        if prop.name() in itemProps:
            del itemProps[prop.name()]
            changed = True
        if not itemProps:
            del props[prop.item.id]
            changed = True
        if changed:
            self.setItemProperties(props, notify=False)

    def resetAllItemProperties(self, notify=True, undo=None):
        for itemId, propValues in list(self.itemProperties().items()):
            item = self.document().find(itemId)
            for propName in list(propValues.keys()):
                item.prop(propName).reset(notify=notify, undo=undo)
        self.setItemProperties({})


