import copy
from ..pyqt import QDate
from ..util import Debug
from .property import Property



CLASS_PROPERTIES = { }


class Item(Debug):
    """Anything that is stored in the diagram. Has a unique id, write()
    and save() API, and property system. """

    
    @staticmethod
    def registerProperties(propAttrs):
        # set type attr
        for kwargs in propAttrs:
            if not 'type' in kwargs:
                default = kwargs.get('default')
                if default is not None:
                    kwargs['type'] = type(default)
                else:
                    kwargs['type'] = str
        
        import inspect
        classScope = inspect.currentframe().f_back.f_locals
        __qualname__ = classScope['__qualname__']
        CLASS_PROPERTIES[__qualname__] = propAttrs
        
    @staticmethod
    def classProperties(kind):
        ret = []
        for ctor in reversed(kind.mro()):
            propArgs = CLASS_PROPERTIES.get(ctor.__qualname__, [])
            for args in propArgs:
                ret.append(args)
        return ret

    @staticmethod
    def adjustedClassProperties(kind, newEntries):
        """ Return a copy of the property meta data dict with newEntries added or updated. """
        entries = copy.deepcopy(Item.classProperties(kind))
        for newEntry in newEntries:
            found = False
            for entry in entries:
                if newEntry['attr'] == entry['attr']:
                    entry.update(newEntry)
                    found = True
                    break
            if not found:
                entries.append(newEntry)
        return entries

    @staticmethod
    def sameProp(items, attr):
        """ Used for property sheets. """
        if not items:
            return None
        for item in items:
            if item.prop(attr).get() != items[0].prop(attr).get():
                return None
        return items[0].prop(attr).get()


    @staticmethod
    def sameOf(items, getter):
        """ Return the same value for self.items as determined by getter(item). """
        if not items:
            return None
        stuff = [getter(item) for item in items]
        mismatch = False
        first = stuff[0]
        for i in stuff[1:]:
            if i != first:
                mismatch = True
                break
        if mismatch or first is None:
            return None
        else:
            return first


    registerProperties.__get__(Debug)((
        { 'attr': 'tags', 'default': [] },
        { 'attr': 'createdAt', 'type': QDate, 'default': QDate.currentDate() },
    ))

    def __init__(self, *args, **kwargs):
        self.id = None
        self._document = None
        self.propertyListeners = []
        self.props = []
        self._propCache = {}
        propAttrs = self.classProperties(self.__class__)
        self.addProperties(propAttrs)
        self._readChunk = {} # forward compat
        self._hasDeinit = False
        self.setProperties(**kwargs)

    def __repr__(self, exclude=[]):
        if not isinstance(exclude, list):
            exclude = [exclude]
        if not 'id' in exclude:
            exclude.append('id')
        props = {}
        for prop in self.props:
            if not prop.layered and prop.get() != prop.default:
                props[prop.attr] = prop.get()
        s = Debug.pretty(props, exclude=exclude)
        if s:
            s = ': ' + s
        return '<%s[%s]%s>' % (self.__class__.__name__, self.id, s)

    def init(self):
        """ Virtual. """
        pass

    def deinit(self):
        """ Virtual. Allways call base implmentation. """
        self._hasDeinit = False
        for prop in self.props:
            prop.deinit()
        self.props = []
        self._propCache = {}

    def document(self):
        """ Virtual. """
        return self._document

    def setDocument(self, document):
        self._document = document

    @property
    def isDocument(self):
        return self._isDocument

    def itemName(self):
        """ Virtual """
        return self.__class__.__name__

    ## Marshalling
    
    def write(self, chunk):
        """ virtual """
        # forward compatibility, must be before the rest
        # This call also should be called at the top of subclass impl..
        chunk.update(self._readChunk)
        chunk['id'] = self.id
        for prop in self.props:
            chunk[prop.attr] = prop.get(forLayers=[])
        
    def read(self, chunk, byId):
        """ virtual """
        self._readChunk = chunk # copy.deepcopy(chunk) # forward compat
        self.id = chunk.get('id', None)
        for prop in self.props:
            value = chunk.get(prop.attr, prop.default)
            if not isinstance(value, prop.type) and value != prop.default:
                try:
                    value = prop.type(value)
                except TypeError:
                    value = None
            prop.set(value, notify=False)

    def clone(self, document):
        """ Virtual """
        y = self.__class__()
        if hasattr(y, 'boundingRect'): # PathItem (avoid import)
            document.addItem(y)
        else:
            document.addItem(y)
        y._readChunk = copy.deepcopy(self._readChunk)
        for prop in self.props:
            y.prop(prop.attr).set(prop.get(), notify=False)
        y.setLoggedDate(QDate.currentDate(), notify=False)
        return y

    def remap(self, map):
        """ Virtual; return True if not possible to build coherant item. """
        return True

    ## Properties

    def addProperties(self, meta):
        """ append to property list: [
            { 'attr': 'married', 'type': bool, 'default': True, 'update': True },
            { 'attr': 'marriedDate', 'update': True },
        ]
        """
        for kwargs in meta:
            if kwargs['attr'] in ['properties', 'opacity']:
                raise ValueError('`%s` is a reserved method name for Item' % kwargs['attr'])
            p = Property(self, **kwargs)
            attr = kwargs['attr']
            setterName = 'set' + attr[0].upper() + attr[1:]
            if not hasattr(self, setterName):
                setattr(self, setterName, p.set)
            getterName = kwargs['attr']
            if not hasattr(self, getterName):
                setattr(self, getterName, p.get)
            resetterName = 'reset' + attr[0].upper() + attr[1:]
            if not hasattr(self, resetterName):
                setattr(self, resetterName, p.reset)
            self.props.append(p)
            self._propCache[attr] = p
            
    def setProperties(self, **kwargs):
        """ Convenience method for bulk assignment.
        Ignore kwargs without a registered property.
        """
        for k, v in kwargs.items():
            prop = self.prop(k)
            if prop:
                prop.set(v, notify=False)

    def onProperty(self, prop):
        """ virtual """
        for x in self.propertyListeners:
            x.onItemProperty(prop)

    def addPropertyListener(self, x):
        if not x in self.propertyListeners:
            self.propertyListeners.append(x)

    def removePropertyListener(self, x):
        if x in self.propertyListeners:
            self.propertyListeners.remove(x)

    def propertyNames(self):
        return self._propCache.keys()

    def prop(self, name):
        if name in self._propCache:
            return self._propCache[name]


    ## Tags

    def setTag(self, x, notify=True, undo=None):
        tags = list(self.tags())
        if not x in tags:
            tags.append(x)
            tags.sort()
            self.prop('tags').set(tags, notify=notify, undo=undo)

    def addTags(self, newTags, notify=True, undo=None):
        itemTags = list(self.tags())
        for tag in newTags:
            if not tag in itemTags:
                 itemTags.append(tag)
        itemTags.sort()
        if itemTags != self.tags():
            self.prop('tags').set(itemTags, notify=notify, undo=undo)

    def unsetTag(self, x, notify=True, undo=None):
        tags = list(self.tags())
        if x in tags:
            tags.remove(x)
            tags.sort()
            self.prop('tags').set(tags, notify=notify, undo=undo)

    def hasTags(self, tags, reverseTags):
        """ Central algorithm for checking tags.
        Reverse tags is meant to override the default behavior of showing if no tags are selected.

        Hide an item if:
        1) At least one tag in `reverseTags` that is not in `tags` - ABSOLUTE
        2) No tag in `tags` - ABSOLUTE
        3) `tags` is not empty and not one tag is in `tags`
        """
        # init
        if not tags and not reverseTags:
            return True
        if not isinstance(tags, list):
            tags = [tags]
        if not isinstance(reverseTags, list):
            reverseTags = [reverseTags]
            
        # algorithm

        hasTags = set(self.tags()) & set(tags)
        hasReverseTags = set(self.tags()) & set(reverseTags)
        allMyReverseTagsAreInTags = (set(tags) & hasReverseTags) == hasReverseTags
        # allMyReverseTagsAreInTags = all([(x in tags) for x in reverseTags])

        if hasReverseTags: # reverse filtering trumps all
            if allMyReverseTagsAreInTags:
                return True
            else:
                return False
        elif not tags:
            return True
        elif hasTags:
            return True
        else:
            return False

    def onTagRenamed(self, old, new):
        """ Called right from Document.renameTag() """
        tags = []
        for index, tag in enumerate(self.tags()):
            if tag == old:
                tags.append(new)
            else:
                tags.append(tag)
        tags.sort()
        self.prop('tags').set(tags, notify=False, undo=False)


    ## Document Events

    def onRegistered(self, document):
        """ virtual """
        self._document = document

    def onDeregistered(self, document):
        """ virtual """
        self._document = None

    def onActiveLayersChanged(self):
        """ Virtual. Calling base implementation is required. """
        changed = []
        for prop in self.props:
            if prop.layered:
                was = prop.get()
                prop.onActiveLayersChanged()
                now = prop.get()
                itemName = prop.item.itemName() and prop.item.itemName() or prop.item.__class__.__name__
                if now != was:
                    changed.append(prop)
        for prop in changed:
            self.onProperty(prop)

    def onUpdateAll(self):
        """ Virtual. Calling base implementation is required.
        
        Reimplement to perform a *read-only* update of Item representation,
        for example a visual re-paint. Must be able to be called any
        number of times at any time.
        """
        self.onActiveLayersChanged()
        for prop in self.props:
            if prop.layered:
                self.onProperty(prop)

    def updateAll(self):
        """ Read-only update of item representation, for example in a gui paint event. """
        if not self.document():
            return
        self._isUpdatingAll = True
        self.onUpdateAll()
        self._isUpdatingAll = False

    def isUpdatingAll(self):
        """ Return True if in the middle of a call to `updateAll()`.
        Useful for coalescing redundant operations.
        """
        return self._isUpdatingAll

