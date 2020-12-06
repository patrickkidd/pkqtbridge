# pkqtbridge

Declarative Python property and QtQuick model system for document-oriented PyQt applications, where:

- Document data is a hierarchy of class instances
- Types have formal properties that are stored to disk
- Properties have comprehensive get/set/reset event support
- Properties have undo support.

## Classes


### Item

The basic type in the document model. Contains many `Property` objects. Has unique Id. Tracks event listeners for when properties change.

```python
class Event(Item):

    Item.registerProperties((
        { 'attr': 'date', 'type': QDate },
        { 'attr': 'unsure', 'default': True },
        { 'attr': 'description' },
        { 'attr': 'nodal', 'default': False },
        { 'attr': 'notes' },
        { 'attr': 'parentName' },
        { 'attr': 'location' },
        { 'attr': 'uniqueId' }, # 'birth', 'death', 'adopted', 'bonded', 'married', 'separated', 'divorced', 'now'
        { 'attr': 'includeOnDiagram', 'default': False }
    ))

    def itemName(self):
        if self.parent:
            return "<%s>: %s" % (self.parent.itemName(), self.description())
        else:
            return str(self)

    def write(self, chunk):
        super().write(chunk)
        chunk['dynamicProperties'] = {}
        for prop in self.dynamicProperties:
            chunk['dynamicProperties'][prop.attr] = prop.get()
            
    def read(self, chunk, byId):
        super().read(chunk, byId)
        if self.date() is not None and self.date().isNull():
            self.setDate(None, notify=False)
        for attr, value in chunk.get('dynamicProperties', {}).items():
            prop = self.addDynamicProperty(attr)
            if prop: # avoid duplicates
                prop.set(value, notify=False)

    @util.blocked
    def onProperty(self, prop):
        if prop.name() == 'description':
            if not self._onHideNames:
                self.updateDescription()
        elif prop.name() == 'notes':
            if not self._onHideNames:
                self.updateNotes()
        elif prop.name() == 'uniqueId':
            self.updateDescription()
        if not self.uniqueId() == 'now' and not self.addDummy:
            super().onProperty(prop)
            if self.parent:
                self.parent.onEventProperty(prop)

```

### Property

A stored value with get/set/reset handlers and events. Includes undo support via `commands.SetProperty`. Added to `Item` subclass using declarative form:

```python
class Event(Item):

    Item.registerProperties((
        { 'attr': 'date', 'type': QDate },
        { 'attr': 'unsure', 'default': True },
        { 'attr': 'description' },
        { 'attr': 'nodal', 'default': False },
        { 'attr': 'notes' },
        { 'attr': 'parentName' },
        { 'attr': 'location' },
        { 'attr': 'uniqueId' }, # 'birth', 'death', 'adopted', 'bonded', 'married', 'separated', 'divorced', 'now'
        { 'attr': 'includeOnDiagram', 'default': False }
    ))
```

### Document

Contains many items. Manages unique `Item.id` values. Contains `Layer` items.

```python
class MyItem(Item):
    Item.registerProperties((
        { 'attr': 'something', 'type': int, default=-1 },
    ))

document = Document()
item1, item2 = MyItem(something=123, MyItem(something=456)
document.addItems(item1, item2)

assert item1.id != item2.id
assert item1 == document.findById(item1.id)
assert item2 == document.findById(item2.id)
```

### Layer

A stored, cascading sub-set of `Property` values. Intended for quick-swapping out one subset for another, like a cascading style sheet.

```python
class MyItem(Item):
    Item.registerProperties((
        { 'attr': 'something', 'type': int, 'default'=-1, 'layered': True },
    ))
    
document = Document()
item = MyItem(something=234)
layer1 = Layer(name='Layer 1')
document.addLayer(layer1, item)
layer1.setActive(True)
item.setSomething(456)
assert item.something() == 456

layer1.setActive(False)
assert item.something() == 234

layer1.setActive(True)
assert item.something() == 456
```

### QObjectHelper

Declarative interface for mapping `Property`'s onto Qt properties. Useful for exposing an `Item` to QtQuick.


```python
class ModelHelper(QObjectHelper):
    """ Handle properties for a list of like Item's.
    calls refreshAllProperties() when items and/or scene changed.
    """

    QObjectHelper.registerQtProperties([
        { 'attr': 'items', 'type': list },
        { 'attr': 'scene', 'type': Scene, 'default': None },
        { 'attr': 'blockNotify', 'type': bool, 'default': False },
        { 'attr': 'blockUndo', 'type': bool, 'default': False },
        { 'attr': 'addMode', 'type': bool, 'default': False },
        { 'attr': 'dirty', 'type': bool, 'default': False }, # set automatically, reset manually
        { 'attr': 'resetter', 'type': bool } # alternates when modelReset is called for bindings
    ])


    def initModelHelper(self, storage=False):
        self._blockNotify = False
        self._blockUndo = False
        self._addMode = False
        self._dirty = False
        self._items = []
        self._document = None
        self._resetter = False

    def get(self, attr):
        """ Return the value. Default behavior is to return the same(attr).
            If value is a bool then convert it to a check state.
        """
        if attr == 'items':
            return self._items
        # and more....
        else:
            return super().get(attr)

    def set(self, attr, value):
        if attr == 'items':
            if self._items:
                for item in self._items:
                    item.removePropertyListener(self)
                self._items = []
            if value not in (None, [None]):
                if not isinstance(value, list):
                    value = [value]
                self._items = value
                for item in self._items:
                    item.addPropertyListener(self)
            self.refreshProperty('items')
            return

        # and more...

    def reset(self, attr):
        if attr == 'items':
            self.set('items', [])
            return
        elif attr == 'document':
            self.set('document', [])
            return
        elif attr == 'dirty':
            self.set('dirty', False)
        if self.blockUndo:
            id = False
        else:
            id = commands.nextId()
        notify = not self.blockNotify
        for item in self._items:
            prop = item.prop(attr)
            if prop:
                item.prop(attr).reset(notify=notify, undo=id)=
```

(See [modelhelper.py](qtbridge/modelhelper.py) for full example)

### ModelHelper

Bridge mixin for QAbstractItemModel + QObjectHelper.
Calls refreshAllProperties() when items and/or document changed.

### QmlWidgetHelper

Convenience mixin to help find qml items from python. Very helpful in unit testing QQuickWidget from Python.
Declarative interface for `QQuickWidget`.

```python
class QmlSomething(QQuickWidget, QmlWidgetHelper):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._sizeHint = QSize()
        Layout = QVBoxLayout(self)
        Layout.setContentsMargins(0, 0, 0, 0)
        self.initQmlWidgetHelper('qml/Something.qml')

something = QmlSomething()
assert something.findItem('doneButton').property('hasActiveFocus) == something.itemProp('doneButton', 'hasActiveFocus')
```

### conftest.PKQtBot

Bug fixes and additional features for `qtbot` pytest plugin.

