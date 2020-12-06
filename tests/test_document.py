import os, os.path, pickle
import pytest
import conftest
from conftest import Person
from qtbridge.pyqt import QDate, QPointF, QRectF
from qtbridge import util, commands, Document, Item, Layer, LayerModel


def test_find_by_types(simpleDocument):
    """ """
    people = simpleDocument.find(types=Person)
    assert len(people) == 3

    people = simpleDocument.find(types=[Person])
    assert len(people) == 3

    pairBonds = simpleDocument.find(types=[Marriage])
    assert len(pairBonds) == 1


def test_find_by_tags(simpleDocument):
    p1 = simpleDocument.query1(name='p1')
    p = simpleDocument.query1(name='p')
    p1.setTags(['hello'])
    p.setTags(['hello'])
    p1.birthEvent.setTags(['hello'])
    
    items = simpleDocument.find(tags='hello')
    assert len(items) == 3
    
    items = simpleDocument.find(tags=['hello'])
    assert len(items) == 3


def test_find_by_types_and_tags(simpleDocument):
    p1 = simpleDocument.query1(name='p1')
    p2 = simpleDocument.query1(name='p2')
    p = simpleDocument.query1(name='p')
    p1.setTags(['hello'])
    p.setTags(['hello'])
    p1.birthEvent.setTags(['hello'])
        
    items = simpleDocument.find(tags='hello', types=Event)
    assert len(items) == 1
    
    items = simpleDocument.find(tags=['hello'], types=Person)
    assert len(items) == 2
    
    
def test_undo_remove_child_selected(qtbot, simpleDocument):
    """ People and pair-bond were selected but not child items after delete and undo. """

    p = simpleDocument.query(name='p')[0]
    p1 = simpleDocument.query(name='p1')[0]
    p2 = simpleDocument.query(name='p2')[0]
    m = p1.marriages[0]

    assert p.childOf is not None

    m.setSelected(True)
    p.setSelected(True)
    p1.setSelected(True)
    p2.setSelected(True)

    qtbot.clickYesAfter(lambda: simpleDocument.removeSelection())
    commands.stack().undo()
    
    assert not m.isSelected()
    assert not p.isSelected()
    assert not p1.isSelected()
    assert not p2.isSelected()
    assert not p.childOf.isSelected()


def test_rename_tag_retains_tag_on_items(qApp):

    s = Document()
    s.setTags(['aaa', 'ccc', 'ddd'])
    item = Item()
    s.addItem(item)
    item.setTags(['ddd'])

    s.renameTag('ddd', 'bbb')

    assert s.tags() == ['aaa', 'bbb', 'ccc']
    assert item.tags() == ['bbb']


def test_new_items_have_current_tags(qApp):

    s = Document()
    s.setTags(['are', 'here', 'you'])
    layer1 = Layer(tags=['here'])
    s.addItem(layer1)
    p1 = Person(name='p1')
    assert p1.tags() == []

    layer1.setActive(True)
    assert p1.tags() == []

    p2 = Person(name='p2')
    s.addItem(p2)
    assert p1.tags() == []
    assert p2.tags() == ['here']
    
    layer2 = Layer(tags=['you'], active=True)
    s.addItem(layer2)
    assert p1.tags() == []
    assert p2.tags() == ['here']
     
    p3 = Person(name='p3')
    s.addItem(p3)
    assert p1.tags() == []
    assert p2.tags() == ['here']
    assert p3.tags() == ['here', 'you']

    layer1.setActive(False)
    p4 = Person(name='p4')
    s.addItem(p4)
    assert p1.tags() == []
    assert p2.tags() == ['here']
    assert p3.tags() == ['here', 'you']
    assert p4.tags() == ['you']
    


def test_update_set_tag_on_inspected_items_out_of_layer(qApp):
    """ Show layer with people that have emotional process
    symbols that don’t have the layer’s tags, inspect those
    symbols from personal timeline, add tag for the layer -> symbols don’t appear.
    """
    tags = ['here']
    s = Document()
    s.setTags(tags)
    layer1 = Layer(tags=tags)
    s.addItem(layer1)
    p1 = Person(name='p1', tags=tags)
    p2 = Person(name='p2', tags=tags)
    s.addItems(p1, p2)
    cutoff = Emotion(kind=util.ITEM_CUTOFF, personA=p1, personB=p2)
    s.addItems(cutoff)
    layer1.setActive(True)
    date = QDate.currentDate()
    assert p1.shouldShowFor(date, tags) == True
    assert p2.shouldShowFor(date, tags) == True
    assert cutoff.shouldShowFor(date, tags) == False
    assert cutoff.isVisible() == False

    # Simulate inspecting a hidden emotion from person props
    cutoff.setTags(tags)
    assert cutoff.shouldShowFor(date, tags) == True
    assert cutoff.isVisible() == True
    

def test_read(qApp):
    """ Just try to break the most basic object constructors. """
    stuff = []
    def byId(id):
        return None

    data = {
        'items': [
            {
                'kind': 'Person',
                'id': 1,
                'events': [
                    {
                        'id': 2
                    }
                ],
                'parents': None,
                'marriages': []
            }
        ]
    }
    
    document = Document()
    document.read(data, byId)



def test_read_fd(qApp):
    """ Just test reading in an actual fd. """
    with open(os.path.join(conftest.TIMELINE_TEST_FD, 'diagram.pickle'), 'rb') as f:
        bdata = f.read()
    document = Document()
    data = pickle.loads(bdata)
    assert document.read(data) == None


def test_clean_stale_refs(qApp):
    with open(os.path.join(conftest.DATA_ROOT, 'patrick-stinson-stale-refs.fd/diagram.pickle'), 'rb') as f:
        bdata = f.read()
    document = Document()
    data = pickle.loads(bdata)
    assert len(document.prune(data)) == 9


def test_hasActiveLayers(qApp):
    document = Document()
    assert document.hasActiveLayers == False
    
    layer = Layer(active=True)
    document.addItem(layer)
    assert document.hasActiveLayers == True

    layer.setActive(False)
    assert document.hasActiveLayers == False
    
    
def __test_getPrintRect(qApp): # was always changing by a few pixels...
    s = Document()
    s.setTags(['NW', 'NE', 'SW', 'SE'])
    northWest = Person(name='NW', pos=QPointF(-1000, -1000), tags=['NW'])
    northEast = Person(name='NE', pos=QPointF(1000, -1000), tags=['NE'])
    southWest = Person(name='SW', pos=QPointF(-1000, 1000), tags=['SW'])
    southEast = Person(name='SE', pos=QPointF(1000, 1000), tags=['SE'])
    s.addItems(northWest, northEast, southWest, southEast)

    fullRect = s.getPrintRect()
    assert fullRect == QRectF(-1162.5, -1181.25, 2407.5, 2343.75)

    nwRect = s.getPrintRect(forTags=['NW'])
    assert nwRect == QRectF(-1162.5, -1181.25, 417.5, 343.75)

    ## TODO: account for ChildOf, Emotions, and other Item's that don't have a layerPos()


def test_layered_properties(qApp):
    """ Ensure correct layered prop updates for marriage+marriage-indicators. """
    document = Document()
    male = Person(name='Male', kind='male')
    female = Person(name='Female', kind='female')
    marriage = Marriage(personA=male, personB=female)
    divorcedEvent = Event(parent=marriage, uniqueId='divorced', date=QDate(1900, 1, 1))
    layer = Layer(name='Layer 1')
    document.addItems(male, female, marriage, layer)
    #
    unlayered = {
        'male': QPointF(-100, -50),
        'maleDetails': QPointF(100, 100),
        'female': QPointF(100, -50),
        'femaleDetails': QPointF(-100,-200),
        'marriageSep': QPointF(100, 0),
        'marriageDetails': QPointF(-25, 0),
    }
    layered = {
        'male': QPointF(-200, -150),
        'maleDetails': QPointF(-100, -100),
        'female': QPointF(100, 50),
        'femaleDetails': QPointF(100, 200),
        'marriageSep': QPointF(100, 0),
        'marriageDetails': QPointF(25, -100),
    }
    # layered
    layer.setItemProperty(male.id, 'itemPos', layered['male'])
    layer.setItemProperty(male.detailsText.id, 'itemPos', layered['maleDetails'])
    layer.setItemProperty(female.id, 'itemPos', layered['female'])
    layer.setItemProperty(female.detailsText.id, 'itemPos', layered['femaleDetails'])
    layer.setItemProperty(marriage.detailsText.id, 'itemPos', layered['marriageDetails'])
    layer.setItemProperty(marriage.separationIndicator.id, 'itemPos', layered['marriageSep'])
    # unlayered
    male.setItemPos(unlayered['male'], undo=False)
    male.detailsText.setItemPos(unlayered['maleDetails'], undo=False)
    female.setItemPos(unlayered['female'], undo=False)
    female.detailsText.setItemPos(unlayered['femaleDetails'], undo=False)
    # marriage.setDivorced(True, undo=False)
    marriage.separationIndicator.setItemPos(unlayered['marriageSep'], undo=False)
    marriage.detailsText.setItemPos(unlayered['marriageDetails'], undo=False)
    
    assert male.pos() == unlayered['male']
    assert male.detailsText.pos() == unlayered['maleDetails']
    assert female.pos() == unlayered['female']
    assert female.detailsText.pos() == unlayered['femaleDetails']
    assert marriage.detailsText.pos() == unlayered['marriageDetails']
    assert marriage.separationIndicator.pos() == unlayered['marriageSep']

    layer.setActive(True)
    assert male.pos() == layered['male']
    assert male.detailsText.pos() == layered['maleDetails']
    assert female.pos() == layered['female']
    assert female.detailsText.pos() == layered['femaleDetails']
    assert marriage.detailsText.pos() == layered['marriageDetails']
    assert marriage.separationIndicator.pos() == layered['marriageSep']
    
    layer.setActive(False)
    assert male.pos() == unlayered['male']
    assert male.detailsText.pos() == unlayered['maleDetails']
    assert female.pos() == unlayered['female']
    assert female.detailsText.pos() == unlayered['femaleDetails']
    assert marriage.detailsText.pos() == unlayered['marriageDetails']
    assert marriage.separationIndicator.pos() == unlayered['marriageSep']
 
    layer.resetItemProperty(male.prop('itemPos'))
    layer.resetItemProperty(male.detailsText.prop('itemPos'))
    layer.resetItemProperty(female.prop('itemPos'))
    layer.resetItemProperty(female.detailsText.prop('itemPos'))
    layer.resetItemProperty(marriage.detailsText.prop('itemPos'))
    layer.resetItemProperty(marriage.separationIndicator.prop('itemPos'))
    layer.setActive(True)
    assert male.pos() == unlayered['male']
    assert male.detailsText.pos() == unlayered['maleDetails']
    assert female.pos() == unlayered['female']
    assert female.detailsText.pos() == unlayered['femaleDetails']
    assert marriage.detailsText.pos() == unlayered['marriageDetails']
    assert marriage.separationIndicator.pos() == unlayered['marriageSep']
   


def test_undo_add_remove_layered_item_props(qtbot, qApp):
    document = Document()
    male = Person(name='Male', kind='male')
    female = Person(name='Female', kind='female')
    marriage = Marriage(personA=male, personB=female)
    divorcedEvent = Event(parent=marriage, uniqueId='divorced', date=QDate(1900, 1, 1))
    layer = Layer(name='Layer 1')
    document.addItems(male, female, marriage, layer)
    #
    unlayered = {
        'male': QPointF(-100, -50),
        'maleDetails': QPointF(100, 100),
        'female': QPointF(100, -50),
        'femaleDetails': QPointF(-100,-200),
        'marriageSep': QPointF(100, 0),
        'marriageDetails': QPointF(-25, 0),
    }
    layered = {
        'male': QPointF(-200, -150),
        'maleDetails': QPointF(-100, -100),
        'female': QPointF(100, 50),
        'femaleDetails': QPointF(100, 200),
        'marriageSep': QPointF(100, 0),
        'marriageDetails': QPointF(25, -100),
    }
    # layered
    layer.setItemProperty(male.id, 'itemPos', layered['male'])
    layer.setItemProperty(male.detailsText.id, 'itemPos', layered['maleDetails'])
    layer.setItemProperty(female.id, 'itemPos', layered['female'])
    layer.setItemProperty(female.detailsText.id, 'itemPos', layered['femaleDetails'])
    layer.setItemProperty(marriage.detailsText.id, 'itemPos', layered['marriageDetails'])
    layer.setItemProperty(marriage.separationIndicator.id, 'itemPos', layered['marriageSep'])
    # unlayered
    male.setItemPos(unlayered['male'], undo=False)
    male.detailsText.setItemPos(unlayered['maleDetails'], undo=False)
    female.setItemPos(unlayered['female'], undo=False)
    female.detailsText.setItemPos(unlayered['femaleDetails'], undo=False)
    # marriage.setDivorced(True, undo=False)
    marriage.separationIndicator.setItemPos(unlayered['marriageSep'], undo=False)
    marriage.detailsText.setItemPos(unlayered['marriageDetails'], undo=False)
    assert len(document.items()) == 22

    document.selectAll()
    qtbot.clickYesAfter(lambda: document.removeSelection())
    assert len(document.items()) == 0

    commands.stack().undo()
    assert len(document.items()) == 22

    commands.stack().redo()
    assert len(document.items()) == 0


def test_read_write_layered_props(qApp):
    """ Item.write was not explicitly requesting non-layered prop values. """
    document = Document()
    person = Person()
    layer = Layer(name='Layer 1', active=True)
    document.addItems(person, layer)
    person.setItemPos(QPointF(10, 10))
    person.setColor('#ff0000')
    #
    data = {}
    document.write(data)
    document = Document()
    document.read(data)
    assert document.people()[0].pos() == QPointF(10, 10)
    assert document.people()[0].color() == '#ff0000'
    assert document.people()[0].pen().color().name() == '#ff0000'
    
    document.layers()[0].setActive(False)
    assert document.people()[0].color() == None
    assert document.people()[0].pen().color().name() == util.PEN.color().name()
    
    document.layers()[0].setActive(True)
    assert document.people()[0].color() == '#ff0000'
    assert document.people()[0].pen().color().name() == '#ff0000'



def test_reset_layered_props(qApp):
    """ Item.write was not explicitly requesting non-layered prop values. """
    document = Document()
    person = Person()
    layer = Layer(name='Layer 1', active=True, storeGeometry=True)
    document.addItems(person, layer)
    person.setItemPos(QPointF(10, 10))
    assert layer.active() == True
    assert person.pos() == QPointF(10, 10)
    
    document.resetAll() # was throwing exception in commands.py
    assert person.itemPos() == QPointF()
    assert person.pos() == QPointF()


def test_exclusiveLayerSelection(qApp):
    document = Document()
    layerModel = LayerModel()
    layerModel.document = document
    layer1 = Layer(name='Layer 1', active=True)
    layer2 = Layer(name='Layer 2')
    document.addItems(layer1, layer2)
    assert layer1.active() == True

    layerModel.setActiveExclusively(1)
    assert layer2.active() == True
    assert layer1.active() == False



def test_save_load_delete_items(qtbot, qApp):
    """ ItemDetails and SeparationIndicator that were saved to disk were
    not retaining ids stored in the fd, causing addItem() to asign new ids.
    Then item properties in layers would be out of sync, etc.
    Fixed by not adding items until after read().
    """
    document = Document()
    person = Person()
    person.setDiagramNotes('here are some notes')
    document.addItem(person)
    data = {}
    document.write(data)
    bdata = pickle.dumps(data)
    #
    document = Document()
    document.read(data)
    ## added to ensure that ItemDetails|SeparationIndicator id's match the id's in the file
    for id, item in document.itemRegistry.items():
        assert id == item.id
    document.selectAll()
    qtbot.clickYesAfter(lambda: document.removeSelection()) # would throw exception


