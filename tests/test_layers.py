import pytest
from qtbridge.pyqt import Qt, QPointF
from qtbridge import util, commands, Debug, Document, Item, Layer, PathItem, Person, Property, Callout



@pytest.fixture
def undoStack(qApp):
    commands.stack().clear()
    return commands.stack()


def test_add_layers_retain_order(qApp):
    document = Document()
    document.addItem(Layer(name='Layer 1'))
    document.addItem(Layer(name='Layer 2'))
    document.addItem(Layer(name='Layer 3'))
    document.addItem(Layer(name='Layer 4'))

    document.query1(name='Layer 1').order() == 0
    document.query1(name='Layer 2').order() == 1
    document.query1(name='Layer 3').order() == 2
    document.query1(name='Layer 4').order() == 3


def test_layerOrderChanged(qApp):
    document = Document()
    document.addItem(Layer(name='Layer 1'))
    document.addItem(Layer(name='Layer 2'))
    document.addItem(Layer(name='Layer 3'))
    document.addItem(Layer(name='Layer 4'))
    layerOrderChanged = util.Condition(document.layerOrderChanged)

    document.resortLayersFromOrder() # noop
    assert layerOrderChanged.callCount == 0

    document.query1(name='Layer 2').setOrder(10) # way above
    document.resortLayersFromOrder()
    assert layerOrderChanged.callCount == 1



def test_document_signals(simpleDocument, undoStack):
    onLayerAdded = util.Condition()
    simpleDocument.layerAdded[Layer].connect(onLayerAdded)
    onLayerChanged = util.Condition()
    simpleDocument.layerChanged[Property].connect(onLayerChanged)
    onLayerRemoved = util.Condition()
    simpleDocument.layerRemoved[Layer].connect(onLayerRemoved)

    # add
    for i in range(3):        
        layer = Layer()
        simpleDocument.addItem(layer)
        assert onLayerAdded.callCount == i+1
        assert onLayerAdded.lastCallArgs == (layer,)
    assert len(simpleDocument.layers()) == 3
    assert onLayerAdded.callCount == 3
    assert onLayerChanged.callCount == 0
    assert onLayerRemoved.callCount == 0

    # change
    for i in range(3):
        layer = simpleDocument.layers()[i]
        name = 'here %i' % i
        layer.setName(name)
        prop = layer.prop('name')
        assert onLayerChanged.callCount == i+1
        assert onLayerChanged.lastCallArgs == (prop,)
    assert onLayerAdded.callCount == 3
    assert onLayerChanged.callCount == 3
    assert onLayerRemoved.callCount == 0

    # remove
    for i in range(3):
        layer = simpleDocument.layers()[-1]
        simpleDocument.removeItem(layer)
        assert onLayerRemoved.callCount == i+1
        assert onLayerRemoved.lastCallArgs == (layer,)
    assert onLayerAdded.callCount == 3
    assert onLayerChanged.callCount == 3
    assert onLayerRemoved.callCount == 3


def test_undo_commands(simpleDocument, undoStack):
    """ Test merging multiple undo commands values. """
    person1 = simpleDocument.query1(name='p1')
    person2 = simpleDocument.query1(name='p2')
    
    layer = Layer(name='Layer 1')
    simpleDocument.addItem(layer)
    layer.setActive(True)
    
    id = commands.nextId()
    person1.setColor('#ABCABC', undo=id)
    person2.setColor('#DEFDEF', undo=id)

    id = commands.nextId()
    person1.setColor('#123123', undo=id)
    person2.setColor('#456456', undo=id)

    assert person1.color() == '#123123'
    assert person2.color() == '#456456'

    undoStack.undo()
    assert person1.color() == '#ABCABC'
    assert person2.color() == '#DEFDEF'

    undoStack.undo()
    assert person1.color() == None
    assert person2.color() == None

    
def test_person_props(simpleDocument):
    layer = Layer()
    person = Person()
    simpleDocument.addItem(layer)
    simpleDocument.addItem(person)        

    # layer on
    layer.setActive(True)
    assert simpleDocument.activeLayers() == [layer]

    # set props
    person.setColor('#FF0000')
    assert person.color() == '#FF0000'

    # layer off
    layer.setActive(False)
    assert simpleDocument.activeLayers() == []
    assert person.color() == None

    # layer back on
    layer.setActive(True)
    assert simpleDocument.activeLayers() == [layer]
    assert person.color() == '#FF0000'


def test_same_value_multiple_layers(simpleDocument):
    """ Property._value was caching the set value from the previous layer, preventing the next layer to set it.  """

    layer1 = Layer(name='layer1')
    layer2 = Layer(name='layer2')
    simpleDocument.addItem(layer1)
    simpleDocument.addItem(layer2)

    person = simpleDocument.query1(name='p1')

    # default
    assert person.itemOpacity() is None

    layer1.setActive(True)
    person.setItemOpacity(.1)
    x, ok = layer1.getItemProperty(person.id, 'itemOpacity')
    assert ok
    assert x == .1
    assert person.itemOpacity() == .1

    layer1.setActive(False)
    layer2.setActive(True)
    person.setItemOpacity(.1)
    x, ok = layer2.getItemProperty(person.id, 'itemOpacity')
    assert ok
    assert x == .1
    assert person.itemOpacity() == .1

    layer2.setActive(False)
    assert person.itemOpacity() is None

    
def test_layer_callout(simpleDocument):
    layer = Layer(name='layer')
    simpleDocument.addItem(layer)

    # add
    layer.setActive(True)
    callout = Callout()
    simpleDocument.addItem(callout)
    assert callout.layers() == [layer.id]
    assert callout.document() == simpleDocument
    assert callout.isVisible()
    assert callout.opacity() == 1.0

    # hide
    layer.setActive(False)
    assert not callout.isVisible()
    assert callout.opacity() == 0.0

    # show
    layer.setActive(True)
    assert callout.isVisible()
    assert callout.opacity() == 1.0

    
def test_add_default_layer_with_first_LayerItem(simpleDocument):
    assert simpleDocument.layers() == []

    callout = Callout()
    simpleDocument.addItem(callout)
    assert len(simpleDocument.layers()) == 1
    assert callout.layers() == [simpleDocument.layers()[0].id]


def test_write_read_active_layer_items(qApp):

    tags = ['here']
    document = Document(tags=tags)
    personA = Person(name='personA')
    personB = Person(name='personB', tags=tags)
    layer = Layer(active=True, tags=tags)
    document.addItems(layer, personA, personB)
    assert document.query1(name='personA').isVisible() == False
    assert document.query1(name='personB').isVisible() == True
    data = {}
    document.write(data)

    document = Document()
    document.read(data)
    assert len(document.find(types=Layer)) == 1
    assert len(document.find(types=Person)) == 2
    assert document.find(types=Layer)[0].active() == True
    assert document.query1(name='personA').isVisible() == False
    assert document.query1(name='personB').isVisible() == True


def test_remove_layers_with_layerItems(simpleDocument, undoStack):
    layer1 = Layer()
    simpleDocument.addItem(layer1)
    layer2 = Layer()
    simpleDocument.addItem(layer2)

    assert simpleDocument.activeLayers() == []

    layer1.setActive(True)
    callout1 = Callout()
    simpleDocument.addItem(callout1) # layer1, layer2

    layer1.setActive(False)
    layer2.setActive(True)
    callout2 = Callout()
    simpleDocument.addItem(callout2) # layer2

    layer1.setActive(True)
    callout3 = Callout()
    simpleDocument.addItem(callout3) # layer1, layer2

    commands.removeItems(simpleDocument, [layer1])
    assert not (layer1 in simpleDocument.layers())
    assert not (callout1 in simpleDocument.layerItems())
    assert callout2 in simpleDocument.layerItems()
    assert callout3 in simpleDocument.layerItems()
    assert callout1.layers() == []
    assert callout2.layers() == [layer2.id]
    assert callout3.layers() == [layer2.id]

    undoStack.undo()
    assert layer1 in simpleDocument.layers()
    assert callout1 in simpleDocument.layerItems()
    assert callout2 in simpleDocument.layerItems()
    assert callout3 in simpleDocument.layerItems()
    assert callout1.layers() == [layer1.id]
    assert callout2.layers() == [layer2.id]
    assert sorted(callout3.layers()) == [layer1.id, layer2.id]

    ##

    commands.removeItems(simpleDocument, [layer2])
    assert not (layer2 in simpleDocument.layers())
    assert callout1 in simpleDocument.layerItems()
    assert not (callout2 in simpleDocument.layerItems())
    assert callout3 in simpleDocument.layerItems()
    assert callout1.layers() == [layer1.id]
    assert callout2.layers() == []
    assert callout3.layers() == [layer1.id]

    undoStack.undo()
    assert layer2 in simpleDocument.layers()
    assert callout1 in simpleDocument.layerItems()
    assert callout2 in simpleDocument.layerItems()
    assert callout3 in simpleDocument.layerItems()
    assert callout1.layers() == [layer1.id]
    assert callout2.layers() == [layer2.id]
    assert sorted(callout3.layers()) == [layer1.id, layer2.id]

    ##

    commands.removeItems(simpleDocument, [layer1, layer2])
    assert not (layer1 in simpleDocument.layers())
    assert not (layer2 in simpleDocument.layers())
    assert not (callout1 in simpleDocument.layerItems())
    assert not (callout2 in simpleDocument.layerItems())
    assert not (callout3 in simpleDocument.layerItems())
    assert callout1.layers() == []
    assert callout2.layers() == []
    assert callout3.layers() == []

    undoStack.undo()
    assert layer1 in simpleDocument.layers()
    assert layer2 in simpleDocument.layers()
    assert callout1 in simpleDocument.layerItems()
    assert callout2 in simpleDocument.layerItems()
    assert callout3 in simpleDocument.layerItems()
    assert callout1.layers() == [layer1.id]
    assert callout2.layers() == [layer2.id]
    assert sorted(callout3.layers()) == [layer1.id, layer2.id]



class LayeredPathItem(PathItem):

    PathItem.registerProperties((
        { 'attr': 'something', 'layered': True },
    ))

    
def test_delete_layer_prop_with_items(qtbot, qApp):
    document = Document()
    item = LayeredPathItem()
    item.setFlag(item.ItemIsSelectable, True)
    layer = Layer(active=True)
    document.addItems(layer, item)
    item.setSomething('here', undo=True) # 0
    value, ok = layer.getItemProperty(item.id, 'something')
    assert ok == True
    assert value == 'here'
    assert len(layer.itemProperties().items()) == 1
    
    item.setSelected(True)
    qtbot.clickYesAfter(lambda: document.removeSelection()) # 1
    value, ok = layer.getItemProperty(item.id, 'something')
    assert ok == False
    assert value == None
    assert len(layer.itemProperties().items()) == 0

    commands.stack().undo() # 0
    value, ok = layer.getItemProperty(item.id, 'something')
    assert ok == True
    assert value == 'here'
    assert len(layer.itemProperties().items()) == 1
    

def test_store_geometry(qtbot, qApp, monkeypatch):
    document = Document()
    layer = Layer()
    person = Person()
    document.addItems(layer, person)
    layer.setStoreGeometry(False)
    monkeypatch.setattr(document, 'isMovingSomething', lambda: True)

    # Each assert should have all three cases; current visible, no layers, layer.

    person.setPos(QPointF(100, 100))
    person.setSize(1)
    assert person.itemPos() == QPointF(100, 100)
    assert person.itemPos(forLayers=[]) == QPointF(100, 100)
    assert person.itemPos(forLayers=[layer]) == None
    assert person.size(forLayers=[]) == 1
    assert person.size(forLayers=[layer]) == None

    layer.setActive(True)
    assert person.itemPos() == QPointF(100, 100)
    assert person.itemPos(forLayers=[]) == QPointF(100, 100)
    assert person.itemPos(forLayers=[layer]) == None
    assert person.size() == 1
    assert person.size(forLayers=[]) == 1
    assert person.size(forLayers=[layer]) == None

    person.setPos(QPointF(200, 200))
    person.setSize(2)
    assert person.itemPos() == QPointF(200, 200)
    assert person.itemPos(forLayers=[]) == QPointF(200, 200)
    assert person.itemPos(forLayers=[layer]) == None
    assert person.size() == 2
    assert person.size(forLayers=[]) == 2
    assert person.size(forLayers=[layer]) == None

    layer.setStoreGeometry(True)
    assert person.itemPos() == QPointF(200, 200)
    assert person.itemPos(forLayers=[]) == QPointF(200, 200)
    assert person.itemPos(forLayers=[layer]) == None
    assert person.size() == 2
    assert person.size(forLayers=[]) == 2
    assert person.size(forLayers=[layer]) == None

    person.setPos(QPointF(300, 300))
    person.setSize(3)
    assert person.itemPos() == QPointF(300, 300)
    assert person.itemPos(forLayers=[]) == QPointF(200, 200)
    assert person.itemPos(forLayers=[layer]) == QPointF(300, 300)
    assert person.size() == 3
    assert person.size(forLayers=[]) == 2
    assert person.size(forLayers=[layer]) == 3

    layer.setActive(False)
    assert person.itemPos() == QPointF(200, 200)
    assert person.itemPos(forLayers=[]) == QPointF(200, 200)
    assert person.itemPos(forLayers=[layer]) == QPointF(300, 300)
    assert person.size() == 2
    assert person.size(forLayers=[]) == 2
    assert person.size(forLayers=[layer]) == 3

    # test values are deleted
    layer.setStoreGeometry(False)
    assert person.itemPos() == QPointF(200, 200)
    assert person.itemPos(forLayers=[]) == QPointF(200, 200)
    assert person.itemPos(forLayers=[layer]) == None
    assert person.size() == 2
    assert person.size(forLayers=[]) == 2
    assert person.size(forLayers=[layer]) == None

    # test values don't change after setting active (ensure values deleted)
    layer.setActive(True)
    assert person.itemPos() == QPointF(200, 200)
    assert person.itemPos(forLayers=[]) == QPointF(200, 200)
    assert person.itemPos(forLayers=[layer]) == None
    assert person.size() == 2
    assert person.size(forLayers=[]) == 2
    assert person.size(forLayers=[layer]) == None

    # test values are not stored in layer, even if layer active
    person.setPos(QPointF(400, 400))
    person.setSize(4)
    assert person.itemPos() == QPointF(400, 400) # value still stored in layer
    assert person.itemPos(forLayers=[]) == QPointF(400, 400) # new default value
    assert person.itemPos(forLayers=[layer]) == None
    assert person.size() == 4
    assert person.size(forLayers=[]) == 4
    assert person.size(forLayers=[layer]) == None # should reset layer value when setting default value



def test_dont_store_positions(qApp, monkeypatch):
    document = Document()
    layer = Layer()
    item = PathItem()
    document.addItems(layer, item)
    layer.setStoreGeometry(False)
    monkeypatch.setattr(document, 'isMovingSomething', lambda: True)

    item.setPos(QPointF(100, 100))
    assert item.itemPos() == QPointF(100, 100)
    assert item.itemPos(forLayers=[layer]) == None

    layer.setActive(True)
    assert item.itemPos() == QPointF(100, 100)
    assert item.itemPos(forLayers=[layer]) == None

    item.setPos(QPointF(200, 200))
    assert item.itemPos() == QPointF(200, 200)
    assert item.itemPos(forLayers=[layer]) == None

    layer.setStoreGeometry(True)
    item.setPos(QPointF(300, 300))
    assert item.itemPos() == QPointF(300, 300)
    assert item.itemPos(forLayers=[layer]) == QPointF(300, 300)

    layer.setStoreGeometry(False)
    item.setPos(QPointF(400, 400)) # layer still active
    assert item.itemPos() == QPointF(400, 400)
    assert item.itemPos(forLayers=[layer]) == None # layer value deleted when setting storeGeometry = False

    layer.setStoreGeometry(True)
    item.setPos(QPointF(500, 500)) # layer still active
    assert item.itemPos() == QPointF(500, 500)
    assert item.itemPos(forLayers=[layer]) == QPointF(500, 500)

    item.prop('itemPos').reset()
    assert item.itemPos() == QPointF(400, 400) # value still stored in layer
    assert item.itemPos(forLayers=[layer]) == None # layer value is cleared now


def test_storeGeometry_dont_reset_LayerItem_pos(qApp, monkeypatch):
    document = Document()
    layer = Layer()
    item = LayeredPathItem()
    document.addItems(layer, item)
    monkeypatch.setattr(document, 'isMovingSomething', lambda: True)

    item.setPos(QPointF(100, 100))
    assert item.itemPos() == QPointF(100, 100)
    assert item.itemPos(forLayers=[layer]) == None

    layer.setActive(True)
    layer.setStoreGeometry(True)
    item.setPos(QPointF(200, 200))
    assert item.itemPos() == QPointF(200, 200)
    assert item.itemPos(forLayers=[layer]) == QPointF(200, 200)

    layer.setStoreGeometry(False)
    assert item.itemPos() == QPointF(100, 100)
    assert item.itemPos(forLayers=[layer]) == None

    # test no change
    layer.setActive(True)
    assert item.itemPos() == QPointF(100, 100)
    assert item.itemPos(forLayers=[layer]) == None # redundant, but no biggie


# not sure this makes sense now that setting storeGeometry = False clears geo props in layer
def __test_dont_reset_positions_on_activate_layer(qApp, monkeypatch):
    document = Document()
    layer = Layer()
    item = PathItem()
    document.addItems(layer, item)
    monkeypatch.setattr(document, 'isMovingSomething', lambda: True)
    layer.setStoreGeometry(True)
    
    item.setPos(QPointF(100, 100))

    layer.setActive(True)
    item.setPos(QPointF(200, 200))
    
    layer.setStoreGeometry(False)
    layer.setActive(False)
    assert item.itemPos() == QPointF(100, 100)
    assert item.itemPos(forLayers=[layer]) == None

    layer.setActive(True)
    assert item.itemPos() == QPointF(200, 200)
    assert item.itemPos(forLayers=[layer]) == None
    

def tests_duplicate(qApp):
    document = Document()
    layer1 = Layer(active=True)
    item = PathItem()
    callout = Callout()
    document.addItem(layer1)
    document.addItems(item, callout)
    assert layer1.id in callout.layers()
    
    layer2 = layer1.clone(document)
    assert layer2.id in callout.layers()
