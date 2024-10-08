"""Delegates for items in Qt tables."""

from PyQt6 import QtCore, QtWidgets

from rascal2.widgets.inputs import ValidatedInputWidget


class ValidatedInputDelegate(QtWidgets.QStyledItemDelegate):
    """Item delegate for validated inputs."""

    def __init__(self, field_info, parent):
        super().__init__(parent)
        self.field_info = field_info

    def createEditor(self, parent, option, index):
        return ValidatedInputWidget(self.field_info, parent)

    def setEditorData(self, editor: QtWidgets.QWidget, index):
        data = index.data(QtCore.Qt.ItemDataRole.DisplayRole)
        editor.set_data(data)
