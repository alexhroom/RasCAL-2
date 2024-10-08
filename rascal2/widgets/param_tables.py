"""Add to project.py once PR #39 merged..."""

from pydantic import ValidationError
from PyQt6 import QtCore, QtWidgets
from RATapi import ClassList


class ClassListModel(QtCore.QAbstractTableModel):
    """Qt table model for a project ClassList field.

    Parameters
    ----------
    classlist : ClassList
        The initial classlist to represent in this model.
    parent : QtWidgets.QWidget
        The parent widget for the model.

    """

    def __init__(self, classlist: ClassList, parent: QtWidgets.QWidget):
        super().__init__(parent)
        self.classlist = classlist
        self.item_type = classlist._class_handle
        self.headers = list(self.item_type.model_fields)

    def rowCount(self, parent) -> int:
        return len(self.classlist)

    def columnCount(self, parent) -> int:
        return len(self.headers)

    def data(self, index, role):
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            row = index.row()
            col = index.column()
            param = self.headers[col]
            return getattr(self.classlist[row], param)

    def setData(self, index, value, role) -> bool:
        if role == QtCore.Qt.ItemDataRole.EditRole:
            row = index.row()
            col = index.column()
            param = self.headers[col]

            try:
                setattr(self.classlist[row], param, value)
            except ValidationError:
                return False
            return True

    def headerData(self, section, orientation, role):
        if orientation == QtCore.Qt.Orientation.Horizontal and role == QtCore.Qt.ItemDataRole.DisplayRole:
            return self.headers[section]
        return None

    def append_item(self):
        """Append an item to the ClassList."""
        self.beginInsertRows()
        self.classlist.append(self.item_type())
        self.endInsertRows()


class ProjectFieldDisplayWidget(QtWidgets.QWidget):
    """Widget to show a project ClassList field in display mode.

    Parameters
    ----------
    field : str
        The Project field to display.
    view : MainWindowView
        The View for the GUI.

    """

    def __init__(self, field: str, parent):
        super().__init__(parent)
        self.view = parent
        self.table = QtWidgets.QTableView(parent)
        self.table.horizontalHeader()
        self.field = field

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.table)
        self.setLayout(layout)

    def update_model(self):
        """Update the table model to synchronise with the project field."""
        classlist = getattr(self.view.presenter.model.project, self.field)
        model = ClassListModel(classlist, self)

        self.table.setModel(model)


class ProjectFieldEditWidget(QtWidgets.QWidget):
    """Widget to show a project ClassList in edit mode."""

    pass
