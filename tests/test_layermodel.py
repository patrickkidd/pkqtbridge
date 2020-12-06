import pytest
from qtbridge.pyqt import Qt
from qtbridge import util, Document, LayerModel, Layer


def test_init_deinit(qApp):
    model = LayerModel()
    assert model.rowCount() == 0
    
    document = Document()
    layer1 = Layer(name='Layer 1')
    layer2 = Layer(name='Layer 2', active=True)
    layer3 = Layer(name='Layer 3', active=True)
    document.addItems(layer1, layer2, layer3)
    model.document = document
    assert model.rowCount() == 3
    assert model.data(model.index(0, 0), model.IdRole) == layer1.id
    assert model.data(model.index(1, 0), model.IdRole) == layer2.id
    assert model.data(model.index(2, 0), model.IdRole) == layer3.id
    assert model.data(model.index(0, 0)) == 'Layer 1'
    assert model.data(model.index(1, 0)) == 'Layer 2'
    assert model.data(model.index(2, 0)) == 'Layer 3'
    assert model.data(model.index(0, 0), model.ActiveRole) == Qt.Unchecked
    assert model.data(model.index(1, 0), model.ActiveRole) == Qt.Checked
    assert model.data(model.index(2, 0), model.ActiveRole) == Qt.Checked

    model.resetDocument()
    assert model.rowCount() == 0
    with pytest.raises(IndexError):
        model.data(model.index(0, 0))
    
    
def test_add_layer(qApp):
    document = Document()
    model = LayerModel()
    model.document = document
    rowsInserted = util.Condition()
    model.rowsInserted.connect(rowsInserted)
    model.addRow()
    assert rowsInserted.callCount == 1
    assert model.rowCount() == 1
    assert model.data(model.index(0, 0)) == (model.NEW_NAME_TMPL % 1)

    model.addRow()
    assert rowsInserted.callCount == 2
    assert model.rowCount() == 2
    assert model.data(model.index(1, 0)) == (model.NEW_NAME_TMPL % 2)


def test_remove_layer(qApp, qtbot):
    model = LayerModel()
    document = Document()
    model.document = document
    model.addRow()
    model.addRow()
    rowsRemoved = util.Condition()
    model.rowsRemoved.connect(rowsRemoved)
    qtbot.clickYesAfter(lambda: model.removeRow(0))
    
    assert rowsRemoved.callCount == 1
    assert model.rowCount() == 1
    assert model.data(model.index(0, 0)) == (model.NEW_NAME_TMPL % 2)
    assert model.data(model.index(0, 0), model.ActiveRole) == Qt.Unchecked


def test_set_active(qApp):
    model = LayerModel()
    document = Document()
    layer1 = Layer(name='Layer 1')
    layer2 = Layer(name='Layer 2')
    layer3 = Layer(name='Layer 3')
    document.addItems(layer1, layer2, layer3)
    model.document = document

    assert layer1.active() == False
    assert layer2.active() == False
    assert layer3.active() == False

    def set(row, value):
        assert model.setData(model.index(row, 0), value, model.ActiveRole) is True

    set(0, True)
    assert layer1.active() == True
    assert layer2.active() == False
    assert layer2.active() == False
    
    set(2, True)
    assert layer1.active() == True
    assert layer2.active() == False
    assert layer3.active() == True
        
    set(0, False)
    assert layer1.active() == False
    assert layer2.active() == False
    assert layer3.active() == True
    
    set(2, False)
    assert layer1.active() == False
    assert layer2.active() == False
    assert layer3.active() == False
    

def test_moveLayer(qApp):
    document = Document()
    model = LayerModel()
    layer0 = Layer(name='Layer 0')
    layer1 = Layer(name='Layer 1')
    layer2 = Layer(name='Layer 2')
    document.addItems(layer0, layer1, layer2)
    model.document = document

    assert layer0.order() == 0
    assert layer1.order() == 1
    assert layer2.order() == 2

    model.moveLayer(2, 1)
    assert layer0.order() == 0
    assert layer1.order() == 2
    assert layer2.order() == 1

    model.moveLayer(0, 2)
    assert layer0.order() == 2
    assert layer1.order() == 1
    assert layer2.order() == 0
    assert document.layers() == [layer2, layer1, layer0]

    # test reload file after reordering layers

    data = {}
    document.write(data)
    document2 = Document()
    document2.read(data)
    
    _layer0 = document2.query1(name='Layer 0')
    _layer1 = document2.query1(name='Layer 1')
    _layer2 = document2.query1(name='Layer 2')
    assert _layer0.order() == 2
    assert _layer1.order() == 1
    assert _layer2.order() == 0
    assert document2.layers() == [_layer2, _layer1, _layer0]
