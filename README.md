# pkqtbridge

Declarative Python property system for document-oriented PyQt applications, where:

- Document data is a hierarchy of class instances
- Types have formal properties that are stored to disk
- Properties have comprehensive get/set/reset event support
- Properties have undo support.

## Classes


### Item

The basic type in the document model. Contains many `Property` objects. Has unique Id. Tracks event listeners for when properties change.

### Property

A stored value with get/set/reset handlers and events. Includes undo support via `commands.SetProperty`.

### Document

Contains many items. Manages unique `Item.id` values. Contains `Layer` items.

### Layer

A stored, cascading sub-set of `Property` values. Intended for quick-swapping out one subset for another, like a cascading style sheet.

### QObjectHelper

Declarative interface for mapping `Property`'s onto Qt properties. Useful for exposing an `Item` to QtQuick.

### QmlHelper

Declarative interface for `QQuickWidget`.

### QmlWidgetHelper

Convenience mixin to help find qml items from python. Very helpful in unit testing QQuickWidget from Python.


### conftest.PKQtBot

Additional features and bug fixes for `qtbot` pytest plugin.

