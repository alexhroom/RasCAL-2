"""Delegates for items in Qt tables."""

from PyQt6 import QtCore, QtGui, QtWidgets

from rascal2.widgets.inputs import ValidatedInputWidget


class ValidatedInputDelegate(QtWidgets.QStyledItemDelegate):
    """Item delegate for validated inputs."""

    def __init__(self, parent, input):
        super().__init__(parent)
        self.input = input

    def createEditor(self, parent, option, index):
        return ValidatedInputWidget(parent)
    
    def setEditorData(self, editor: QtWidgets.QWidget, index):
        data = index.data(QtCore.Qt.ItemDataRole.DisplayRole)
        editor.set_data(data)
