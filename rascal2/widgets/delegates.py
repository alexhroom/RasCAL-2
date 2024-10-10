"""Delegates for items in Qt tables."""


from PyQt6 import QtCore, QtGui, QtWidgets

from rascal2.widgets.inputs import ValidatedInputWidget


class ValidatedInputDelegate(QtWidgets.QStyledItemDelegate):
    """Item delegate for validated inputs."""

    def __init__(self, field_info, parent):
        super().__init__(parent)
        self.table = parent
        self.field_info = field_info

    def createEditor(self, parent, option, index):
        widget = ValidatedInputWidget(self.field_info, parent)

        # without this signal, data isn't committed unless the user presses 'enter' on the cell
        widget.edited_signal.connect(lambda: self.table.commitData(widget))

        # fill in background as otherwise you can see the original View text underneath
        widget.setAutoFillBackground(True)
        widget.setBackgroundRole(QtGui.QPalette.ColorRole.Base)

        return widget

    def setEditorData(self, editor: QtWidgets.QWidget, index):
        data = index.data(QtCore.Qt.ItemDataRole.DisplayRole)
        editor.set_data(data)

    def setModelData(self, editor, model, index):
        data = editor.get_data()
        model.setData(index, data, QtCore.Qt.ItemDataRole.EditRole)
