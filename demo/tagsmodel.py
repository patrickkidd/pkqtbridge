from ..pyqt import Qt, QAbstractListModel, qmlRegisterUncreatableType, QModelIndex, QVariant, pyqtSlot, QMessageBox, QApplication, qmlRegisterType
from .. import util, objects, commands
from ..objects import Item, Property
from ..document import Document
from .modelhelper import ModelHelper



class TagsModel(QAbstractListModel, ModelHelper):
    """ Manages a list of tags from the document and their active state pulled from the items. """

    NEW_NAME_TMPL = 'New Tag %i'

    IdRole = Qt.UserRole + 1
    NameRole = IdRole + 1
    ActiveRole = NameRole + 1
    FlagsRole = ActiveRole + 1

    def __init__(self, parent=None):
        super().__init__(parent)
        self._documentTags = []
        self._settingTags = False
        self.initModelHelper()

    def set(self, attr, value):
        if attr == 'document':
            super().set(attr, value)
            if self._document:
                self._documentTags = sorted(self._document.tags(), key=lambda x: x.upper())
            else:
                self._documentTags = []
            self.modelReset.emit()
        elif attr == 'items':
            super().set(attr, value)
            self.modelReset.emit()
        else:
            super().set(attr, value)

    ## Data

    def onItemProperty(self, prop):
        if self._settingTags:
            return
        if self._items[0] != self._document:
            if prop.name() == 'tags':
                startIndex = self.index(0, 0)
                endIndex = self.index(self.rowCount()-1, 0)
                self.dataChanged.emit(startIndex, endIndex, [self.ActiveRole])
        elif self._items[0] == self._document:
            if prop.name() == 'shownTags':
                startIndex = self.index(0, 0)
                endIndex = self.index(self.rowCount()-1, 0)
                self.dataChanged.emit(startIndex, endIndex, [self.ActiveRole])
    
    def onDocumentProperty(self, prop):
        if prop.name() == 'tags':
            self._documentTags = sorted(self._document.tags(), key=lambda x: x.upper())
            self._blocked = True
            self.modelReset.emit()
            self._blocked = False

    def tagAtRow(self, row):
        if row < 0 or row >= len(self._documentTags):
            raise KeyError('No tag at row: %s' % row)
        return self._documentTags[row]

    @pyqtSlot()
    def addTag(self):
        tag = util.newNameOf(self._document.tags(), tmpl=self.NEW_NAME_TMPL, key=lambda x: x)
        commands.createTag(self._document, tag)

    @pyqtSlot(int)
    def removeTag(self, row):
        tag = self.data(self.index(row, 0))
        items = self._document.find(tags=tag)
        ok = QMessageBox.Yes
        if items:
            ok = QMessageBox.question(QApplication.activeWindow(), 'Are you sure?',
                                      'Deleting this tag will also remove it from the %i items that use it. Are you sure you want to do this?' % len(items))
        else:
            ok = QMessageBox.question(QApplication.activeWindow(), 'Are you sure?',
                                      'Are you sure you want to remove this tag?')
        if ok == QMessageBox.Yes:
            self._blocked = True
            commands.deleteTag(self._document, tag)
            self._blocked = False
            
    ## Qt Virtuals

    def roleNames(self):
        return {
            self.NameRole: b'name',
            self.ActiveRole: b'active',
            self.IdRole: b'id',
            self.FlagsRole: b'flags'
        }

    @pyqtSlot(result=int)
    def rowCount(self, index=QModelIndex()):
        if not self._document:
            return 0
        return len(self._documentTags)

    @pyqtSlot(result=int)
    def columnCount(self, index=QModelIndex()):
        return 1

    def flags(self, index):
        return super().flags(index) | Qt.ItemIsEditable

    def data(self, index, role=NameRole):
        ret = None
        if role == self.NameRole:
            ret = self.tagAtRow(index.row())
        elif role == self.ActiveRole:
            tag = self.tagAtRow(index.row())
            numChecked = 0
            for item in self._items:
                if item.isDocument:
                    itemTags = item.shownTags()
                else:
                    itemTags = item.tags()
                if tag in itemTags:
                    numChecked += 1
            if numChecked == 0:
                return Qt.Unchecked
            elif numChecked == len(self._items):
                return Qt.Checked
            else:
                return Qt.PartiallyChecked
        elif role == self.FlagsRole:
            ret = self.flags(index)
        else:
            ret = super().data(index, role)
        return ret
        
    def setData(self, index, value, role=NameRole):
        success = False
        emit = True
        tag = self.tagAtRow(index.row())
        if role == self.NameRole:
            if value and value not in self._document.tags(): # must be valid + unique
                commands.renameTag(self._document, tag, value)
                emit = False
                success = True
            else: # trigger a cancel
                self.dataChanged.emit(index, index)
        elif role == self.ActiveRole:
            if self._items and self._items[0] == self._document:
                shownTags = list(self._document.shownTags())
                if value:
                    if not tag in shownTags:
                        shownTags.append(tag)
                else:
                    if tag in shownTags:
                        shownTags.remove(tag)
                if shownTags != self._document.shownTags():
                    self._document.setShownTags(shownTags, undo=True)
                    success = True
            elif self._items and value != self.data(index, role):
                id = commands.nextId()
                self._settingTags = True
                for item in self._items:
                    if value == Qt.Checked or value:
                        if not item.hasTags([tag], []):
                            item.setTag(tag, undo=id)
                            success = True
                    else:
                        if item.hasTags([tag], []):
                            item.unsetTag(tag, undo=id)
                            success = True
                self._settingTags = False
        if success and emit:
            self.dataChanged.emit(index, index, [role])
        return success

        

            

qmlRegisterType(TagsModel, 'PK.Models', 1, 0, 'TagsModel')


