"""Add to project.py once PR #39 merged..."""

from enum import Enum

import RATapi
from pydantic import ValidationError
from PyQt6 import QtCore, QtGui, QtWidgets

from rascal2.config import path_for
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
                    self.protected_indices.append(i)

    def flags(self, index):
        flags = super().flags(index)
        if not (self.edit_mode or (index.row() not in self.protected_indices and index.column() == 1)):
            flags |= QtCore.Qt.ItemFlag.ItemIsEditable
        return flags

    def rowCount(self, parent=None) -> int:
        return len(self.classlist)

    def columnCount(self, parent=None) -> int:
        return len(self.headers) + 1

    def data(self, index, role):
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            row = index.row()
            col = index.column()

            if col == 0:
                return ""

            param = self.headers[col-1]
            data = getattr(self.classlist[row], param)
            # pyqt can't manually coerce enums to strings...
            if isinstance(data, Enum):
                return str(data)
            return data

    def setData(self, index, value, role) -> bool:
        if role == QtCore.Qt.ItemDataRole.EditRole:
            row = index.row()
            col = index.column()
            if col > 0:
                param = self.headers[col-1]
                try:
                    setattr(self.classlist[row], param, value)
                except ValidationError:
                    return False
                return True

    def headerData(self, section, orientation, role):
        if orientation == QtCore.Qt.Orientation.Horizontal and role == QtCore.Qt.ItemDataRole.DisplayRole and section != 0:
                return self.headers[section-1]
        return None

    def append_item(self):
        """Append an item to the ClassList."""
        self.classlist.append(self.item_type())
        self.endResetModel()

    def delete_item(self, i):
        """Delete an item in the ClassList."""
        self.classlist.pop(i)
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
        self.table.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.MinimumExpanding,
            QtWidgets.QSizePolicy.Policy.MinimumExpanding)
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
        self.table.hideColumn(0)
        fit_col = self.model.headers.index("fit") + 1
        for i, header in enumerate(self.model.headers):
            self.table.setItemDelegateForColumn(
                i+1, ValidatedInputDelegate(self.model.item_type.model_fields[header], self.table)
            )

        for i in range(0, self.model.rowCount()):
            for j in range(2, self.model.columnCount()):
                self.table.openPersistentEditor(self.model.createIndex(i, j))

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.Stretch)

    def append_item(self):
        """Append an item to the model if the model exists."""
        if self.model is not None:
            self.model.append_item()

        # call edit again to fix persistent editors
        self.edit()

    def delete_item(self, index):
        """Delete an item at the index if the model exists.

        Parameters
        ----------
        index : int
            The row to be deleted.

        """
        if self.model is not None:
            self.model.delete_item(index)

        # call edit again to fix persistent editors
        self.edit()

    def edit(self):
        """Change the widget to be in edit mode."""
        self.model.edit_mode = True
        self.add_button.setHidden(False)
        self.table.showColumn(0)
        for i in range(0, self.model.rowCount()):
            for j in range(1, self.model.columnCount()):
                # skip name and delete button for protected indices
                if i in self.model.protected_indices:
                    continue
                if j == 1:
                    self.table.setIndexWidget(self.model.createIndex(i, 0), self.make_delete_button(i))
                else:
                    self.table.openPersistentEditor(self.model.createIndex(i, j))

    def display(self):
        """Change the widget to be in display mode."""
        self.error = None
        self.model.edit_mode = False
        self.add_button.setHidden(True)
        self.table.hideColumn(0)
        self.update_model()

        for i in range(0, self.model.rowCount()):
            self.table.closePersistentEditor(self.model.createIndex(i, 1))

    def make_delete_button(self, index):
        """Make a button that deletes index `index` from the list."""
        button = QtWidgets.QPushButton(icon=QtGui.QIcon(path_for("delete.png")))
        button.resize(button.sizeHint().width(), button.sizeHint().width())
        button.pressed.connect(lambda: self.delete_item(index))

        return button

class ProjectTabWidget(QtWidgets.QWidget):
    """Widget that combines multiple ProjectFieldWidgets to create a tab of the project window.

    Parameters
    ----------
    fields : list[str]
        The fields to display in the tab.
    view : MainWindowView
        The parent view to this widget.

    """
    def __init__(self, fields: list[str], view):
        super().__init__(view)
        self.fields = fields
        headers = [f.replace("_", " ").title() for f in self.fields]
        self.tables = {}

        layout = QtWidgets.QVBoxLayout()
        for field, header in zip(self.fields, headers):
            header = QtWidgets.QLabel(header)
            self.tables[field] = ProjectFieldWidget(field, view)
            layout.addWidget(header)
            layout.addWidget(self.tables[field])

        scroll_area = QtWidgets.QScrollArea()
        # one widget must be given, not a layout,
        # or scrolling won't work properly!
        tab_widget = QtWidgets.QFrame()
        tab_widget.setLayout(layout)
        scroll_area.setWidget(tab_widget)
        scroll_area.setWidgetResizable(True)

        # TEST BUTTON PLEASE REMOVE
        button = QtWidgets.QPushButton()
        button.pressed.connect(self.edit)

        widget_layout = QtWidgets.QVBoxLayout()
        widget_layout.addWidget(scroll_area)
        widget_layout.addWidget(button)

        self.setLayout(widget_layout)

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
