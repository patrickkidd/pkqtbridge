from qtbridge import Debug, misc, Document, DocumentModel, Layer


def test_documentChanged(qApp):
    document = Document()
    model = DocumentModel()
    documentChanged = misc.Condition(model.documentChanged)
    model.document = document
    assert documentChanged.callCount == 1
    assert documentChanged.callArgs[0][0] == document


def test_hasActiveLayers(qApp):
    document = Document()
    model = DocumentModel()
    model.document = document
    assert model.hasActiveLayers == document.hasActiveLayers

    layer = Layer(active=True)
    document.addItem(layer)
    assert model.hasActiveLayers == document.hasActiveLayers

    layer.setActive(False)
    assert model.hasActiveLayers == document.hasActiveLayers
    

def __test_valid_props(qApp):
    document = Document()
    model = DocumentModel()
    model.document = document

    attrs = model.classProperties(DocumentModel)
    for kwargs in attrs:
        attr = kwargs['attr']
        Debug(attr, model.get(attr))
        
