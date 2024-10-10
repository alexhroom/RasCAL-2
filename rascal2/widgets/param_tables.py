"""Add to project.py once PR #39 merged..."""

from enum import Enum

import RATapi
from pydantic import ValidationError
from PyQt6 import QtCore, QtWidgets

from rascal2.widgets.delegates import ValidatedInputDelegate


class ClassListModel(QtCore.QAbstractTableModel):
    """Qt table model for a project ClassList field.

    Parameters
    ----------
    classlist : ClassList
        The initial classlist to represent in this model.
    parent : QtWidgets.QWidget
        The parent widget for the model.

    """

    def __init__(self, classlist: RATapi.ClassList, parent: QtWidgets.QWidget):
        super().__init__(parent)
        self.classlist = classlist
        self.item_type = classlist._class_handle
        self.headers = list(self.item_type.model_fields)
        self.edit_mode = False

        self.protected_indices = []
        if self.item_type is RATapi.models.Parameter:
            for i, item in enumerate(classlist):
                if isinstance(item, RATapi.models.ProtectedParameter):
                    self.protected_indices.append((i, 0))

    def flags(self, index):
        flags = super().flags(index)
        if (self.edit_mode or index.column() == self.headers.index("fit")) and (
            index.row(),
            index.column(),
        ) not in self.protected_indices:
            flags |= QtCore.Qt.ItemFlag.ItemIsEditable
        return flags

    def rowCount(self, parent=None) -> int:
        return len(self.classlist)

    def columnCount(self, parent=None) -> int:
        return len(self.headers)

    def data(self, index, role):
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            row = index.row()
            col = index.column()
            param = self.headers[col]
            data = getattr(self.classlist[row], param)
            if isinstance(data, Enum):
                return str(data)
            return data

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
        self.classlist.append(self.item_type())
        self.endResetModel()


class ProjectFieldWidget(QtWidgets.QWidget):
    """Widget to show a project ClassList.

    Parameters
    ----------
    field : str
        The Project field to display.
    view : MainWindowView
        The parent View for the GUI.

    """

    def __init__(self, field: str, view):
        super().__init__(view)
        self.view = view
        self.table = QtWidgets.QTableView(view)
        self.field = field
        self.model = None
        self.error = None

        layout = QtWidgets.QVBoxLayout()
        # change to icon: remember to mention that plus.png in the icons is wonky
        self.add_button = QtWidgets.QPushButton("+")
        self.add_button.setHidden(True)
        self.add_button.pressed.connect(self.append_item)

        layout.addWidget(self.table)
        layout.addWidget(self.add_button)
        self.setLayout(layout)

    def update_model(self):
        """Update the table model to synchronise with the project field."""
        classlist = getattr(self.view.presenter.model.project, self.field)
        self.model = ClassListModel(classlist, self)

        self.table.setModel(self.model)
        fit_col = self.model.headers.index("fit")
        for i, header in enumerate(self.model.headers):
            self.table.setItemDelegateForColumn(
                i, ValidatedInputDelegate(self.model.item_type.model_fields[header], self.table)
            )
        for i in range(0, self.model.rowCount()):
            self.table.openPersistentEditor(self.model.createIndex(i, fit_col))

    def append_item(self):
        """Append an item to the model if the model exists."""
        if self.model is not None:
            self.model.append_item()

        # call edit again to fix persistent editors
        self.edit()

    def edit(self):
        """Change the widget to be in edit mode."""
        self.model.edit_mode = True
        self.add_button.setHidden(False)
        for i in range(0, self.model.rowCount()):
            for j in range(0, self.model.columnCount()):
                if (i, j) not in self.model.protected_indices:
                    self.table.openPersistentEditor(self.model.createIndex(i, j))

    def display(self):
        """Change the widget to be in display mode."""
        self.error = None
        self.model.edit_mode = False
        self.add_button.setHidden(True)
        self.update_model()

        fit_col = self.model.headers.index("fit")
        for i in range(0, self.model.rowCount()):
            for j in range(0, self.model.columnCount()):
                if j != fit_col:
                    self.table.closePersistentEditor(self.model.createIndex(i, j))


class ExperimentalParamsWidget(QtWidgets.QWidget):
    """Widget for the 'experimental parameters' tab of the project window."""

    def __init__(self, view):
        super().__init__(view)
        self.fields = ["resolution_parameters", "scalefactors", "bulk_in", "bulk_out"]
        headers = ["Resolution Parameters", "Scale Factors", "Bulk In", "Bulk Out"]
        self.tables = {}

        layout = QtWidgets.QVBoxLayout()
        for field, header in zip(self.fields, headers):
            header = QtWidgets.QLabel(header)
            self.tables[field] = ProjectFieldWidget(field, view)
            layout.addWidget(header)
            layout.addWidget(self.tables[field])


        # TEST BUTTON PLEASE REMOVE
        button = QtWidgets.QPushButton()
        button.pressed.connect(self.edit)
        layout.addWidget(button)
        self.setLayout(layout)

    def update_model(self):
        for table in self.tables.values():
            table.update_model()

    def edit(self):
        """Change the tables in the widget to be in edit mode."""
        for field in self.fields:
            self.tables[field].edit()

    def display(self):
        """Change the tables in the widget to be in display mode."""
        for field in self.fields:
            self.tables[field].display()
