from qtbridge import Document, Item


class MyItem(Item):
    """ App-specific base class for Item. Highly encouraged to create one. """"

    _isMyItem = False
    _isStock = False

    Item.registerProperties.__get__(Item)((
        """ ... """
    ))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._isDocument = False

    @property
    def isMyItem(self):
        return True

    @property
    def isStock(self):
        return self._isStock


class Stock(TraderItem):

    _isStock = True


class Portfolio(Document):    
    pass


