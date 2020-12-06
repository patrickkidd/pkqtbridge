import pytest
from qtbridge.pyqt import Qt
from qtbridge import Debug, util, Document, TagsModel, Item



def test_init_deinit(qApp):
    model = TagsModel()
    assert model.rowCount() == 0
    
    document = Document(tags=['here', 'we', 'are'])
    model.document = document
    assert model.rowCount() == 3
    
    item1 = Item(tags=['here', 'we'])
    item2 = Item(tags=['here'])
    model.items = [item1, item2]
    assert model.data(model.index(0, 0)) == 'are'
    assert model.data(model.index(1, 0)) == 'here'
    assert model.data(model.index(2, 0)) == 'we'
    assert model.data(model.index(0, 0), model.ActiveRole) == Qt.Unchecked # are
    assert model.data(model.index(1, 0), model.ActiveRole) == Qt.Checked # here
    assert model.data(model.index(2, 0), model.ActiveRole) == Qt.PartiallyChecked # we

    model.resetItems()
    assert model.rowCount() == 3
    # should not change item tags
    assert item1.tags() == ['here', 'we']
    assert item2.tags() == ['here']

    model.resetDocument()
    assert model.rowCount() == 0
    with pytest.raises(KeyError):
        model.data(model.index(0, 0))
            
    
def test_add_tag(qApp):
    document = Document()
    model = TagsModel()
    model.document = document
    item1 = Item()
    item2 = Item()
    model.items = [item1, item2]
    assert model.rowCount() == 0

    modelReset = util.Condition()
    model.modelReset.connect(modelReset)

    model.addTag()
    assert modelReset.callCount == 1
    assert model.rowCount() == 1
    assert model.data(model.index(0, 0)) == model.NEW_NAME_TMPL % 1


def test_remove_tag(qApp, qtbot):
    model = TagsModel()
    document = Document(tags=['here', 'we', 'are'])
    model.document = document
    item1 = Item(tags=['here', 'we'])
    item2 = Item(tags=['here'])
    model.items = [item1, item2]
    
    modelReset = util.Condition()
    model.modelReset.connect(modelReset)

    qtbot.clickYesAfter(lambda: model.removeTag(1))
    assert modelReset.callCount == 1
    assert model.rowCount() == 2
    assert model.data(model.index(0, 0)) == 'are'
    assert model.data(model.index(0, 0), model.ActiveRole) == Qt.Unchecked
    assert model.data(model.index(1, 0)) == 'we'
    assert model.data(model.index(1, 0), model.ActiveRole) == Qt.PartiallyChecked
    


def test_rename_tag_retains_tag_on_items(qApp):

    s = Document()
    s.setTags(['aaa', 'ccc', 'ddd'])
    item = Item()
    s.addItem(item)
    item.setTags(['ddd'])

    model = TagsModel()
    model.items = [item]
    model.document = s
    assert model.data(model.index(2, 0), model.NameRole) == 'ddd'

    dataChanged = util.Condition()
    model.dataChanged.connect(dataChanged)
    modelReset = util.Condition()
    model.modelReset.connect(modelReset)    

    model.setData(model.index(2, 0), 'bbb', model.NameRole)

    assert s.tags() == ['aaa', 'bbb', 'ccc']
    assert item.tags() == ['bbb']
    assert modelReset.callCount == 1
    assert dataChanged.callCount == 0

        
def test_set_active(qApp):
    document = Document()
    model = TagsModel()
    model.document = document
    item1 = Item()
    item2 = Item()
    model.items = [item1, item2]

    document.setTags(['here', 'we', 'are'])
    assert item1.tags() == []
    assert item2.tags() == []

    def set(row, value):
        assert model.setData(model.index(row, 0), value, model.ActiveRole) is True

    set(0, True)
    assert item1.tags() == ['are']
    assert item2.tags() == ['are']
    
    set(2, True)
    assert item1.tags() == ['are', 'we']
    assert item2.tags() == ['are', 'we']
        
    set(0, False)
    assert item1.tags() == ['we']
    assert item2.tags() == ['we']
    
    set(2, False)
    assert item1.tags() == []
    assert item2.tags() == []

