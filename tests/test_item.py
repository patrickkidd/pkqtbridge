from qtbridge import Document, Item, Layer, commands

def test_forward_compat():
    # simulate future version with additional props
    future = Item()
    future.addProperties([
        { 'attr': 'here', 'default': 101 },
        { 'attr': 'there', 'default': 202 }
    ])
    chunk1 = {}
    future.write(chunk1)
    assert 'here' in chunk1
    assert chunk1['here'] == 101
    assert 'there' in chunk1
    assert chunk1['there'] == 202

    past = Item()
    past.addProperties([
        { 'attr': 'here', 'default': 10101 },
    ])
    past.read(chunk1, None)
    assert past.prop('here') is not None
    assert past.prop('here').get() == 101
    assert past.prop('there') is None
    
    chunk2 = {}
    past.write(chunk2)
    assert 'here' in chunk2
    assert chunk2['here'] == 101
    assert 'there' in chunk2
    assert chunk2['there'] == 202



def test_hasTags_no_item_tags():
    """ Enumerate list of scenarios for tag filtering.
    Reverse tags only apply when they match an item tag,
    so this test is pretty simple.
    """

    # item has no tags
    oneTwo = Item()

    # default
    assert oneTwo.hasTags([], [])                              == True  # default match

    # tags
    assert oneTwo.hasTags(['one'], [])                         == False # no match,                none
    assert oneTwo.hasTags(['one', 'two'], [])                  == False # multiple no match,       none

    # reverse tags
    assert oneTwo.hasTags([], ['one'])                         == True  # none,                    reverse no match
    assert oneTwo.hasTags([], ['one', 'two'])                  == True  # none,                    multiple reverse no match
    
    # tags + reverse tags
    assert oneTwo.hasTags(['one'], ['two'])                    == False # no match
    assert oneTwo.hasTags(['one'], ['one'])                    == False # single match
    assert oneTwo.hasTags(['one', 'two'], ['one', 'three'])    == False # partial match
    assert oneTwo.hasTags(['one', 'two'], ['three', 'four'])   == False # multiple match


def test_hasTags_item_tags():

    # item has tags
    oneTwo = Item(tags=['one', 'two'])

    # default
    assert oneTwo.hasTags([], [])                              == True  # default match

    # tags
    assert oneTwo.hasTags(['one'], [])                         == True  # single match,            none
    assert oneTwo.hasTags(['one', 'two'], [])                  == True  # multiple match,          none
    assert oneTwo.hasTags(['three'], [])                       == False # no match,                none

    # reverse tags
    assert oneTwo.hasTags([], ['two'])                         == False # none,                    single reverse match
    assert oneTwo.hasTags([], ['one', 'two'])                  == False # none,                    mulitple reverse match
    assert oneTwo.hasTags([], ['three'])                       == True  # none,                    reverse no match
    
    # tags + reverse tags
    assert oneTwo.hasTags(['one'], ['one'])                    == True  # single match,            single reverse match
    assert oneTwo.hasTags(['one'], ['two'])                    == False # single match,            single different reverse match
    assert oneTwo.hasTags(['one'], ['one', 'two'])             == False # single match,            multiple reverse match
    assert oneTwo.hasTags(['one'], ['three'])                  == True  # single match,            no reverse match
    
    assert oneTwo.hasTags(['one', 'two'], ['one'])             == True  # multiple match,          single reverse match
    assert oneTwo.hasTags(['one', 'two'], ['three'])           == True  # multiple match,          no reverse match
    assert oneTwo.hasTags(['one', 'two'], ['one', 'two'])      == True  # multiple match,          multiple reverse match
    assert oneTwo.hasTags(['one', 'two'], ['one', 'four'])     == True  # multiple match,          partial reverse match
    assert oneTwo.hasTags(['one', 'three'], ['two', 'three'])  == False # partial match,           partial different reverse match
    assert oneTwo.hasTags(['one', 'three'], ['four', 'five'])  == True  # partial match,           multiple no reverse match

    assert oneTwo.hasTags(['three'], ['one'])                  == False # no match,                single reverse match
    assert oneTwo.hasTags(['three'], ['four'])                 == False  # no match,               no reverse match
    assert oneTwo.hasTags(['three'], ['one', 'two'])           == False # no match,                multiple reverse match
    assert oneTwo.hasTags(['three'], ['three', 'four'])        == False  # no match,                multiple no reverse match

    
    
class LayeredItem(Item):

    Item.registerProperties((
        { 'attr': 'num', 'default': -1, 'layered': True },
    ))

    def __init__(self, *args, **kwargs):
        super().__init__(self, *args, **kwargs)
        self.count = 0
        self.layeredCount = 0

    def onProperty(self, prop):
        if prop.name() == 'num':
            if prop.isUsingLayer():
                self.layeredCount += 1
            self.count += 1
        super().onProperty(prop)


def test_layered_property(qApp):

    document = Document()
    item = LayeredItem()
    layer = Layer(name='Layer 1')
    document.addItem(item)
    document.addItem(layer)

    assert item.num() == -1
    assert item.count == 0
    assert item.layeredCount == 0

    item.setNum(1)
    assert item.num() == 1
    assert item.count == 1
    assert item.layeredCount == 0

    layer.setActive(True)
    assert item.num() == 1
    assert item.count == 1
    assert item.layeredCount == 0

    item.prop('num').set(2)
    # item.setNum(2)
    assert item.num() == 2
    assert item.count == 2
    assert item.layeredCount == 1

    layer.setActive(False)
    assert item.num() == 1
    assert item.count == 3
    assert item.layeredCount == 1

    layer.setActive(True)
    assert item.num() == 2
    assert item.count == 4
    assert item.layeredCount == 2

    item.prop('num').reset()
    assert item.num() == 1
    assert item.count == 5
    assert item.layeredCount == 2

    layer.setActive(False)
    assert item.num() == 1
    assert item.count == 5
    assert item.layeredCount == 2



def test_layered_property_undo_redo(qApp):
    """ commands.SetItemProperty wasn't working for non-layered properties. """
    document = Document()
    item = LayeredItem()
    layer = Layer(name='Layer 1')
    document.addItems(layer, item) # 0
    assert item.num() == -1
    assert item.count == 0
    assert item.layeredCount == 0

    item.setNum(1, undo=True) # 1
    assert item.num() == 1
    assert item.count == 1
    assert item.layeredCount == 0

    commands.stack().undo() # 0
    assert item.num() == -1
    assert item.count == 2
    assert item.layeredCount == 0

    commands.stack().redo() # 1
    assert item.num() == 1
    assert item.count == 3
    assert item.layeredCount == 0



    
# def test_class_defs():
#     """ Test migration from properties defined in instance to defined in class, particular onset callback references. """

#     pass
