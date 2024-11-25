"""Tab model/views which are based on a list at the side of the widget."""

from typing import Any, Callable, Generic, TypeVar

import RATapi
from PyQt6 import QtCore, QtGui, QtWidgets
from RATapi.utils.enums import BackgroundActions, LayerModels

from rascal2.config import path_for
from rascal2.widgets.delegates import ProjectFieldDelegate

T = TypeVar("T")


class ClassListItemModel(QtCore.QAbstractListModel, Generic[T]):
    """Item model for a project ClassList field.

    Parameters
    ----------
    classlist : ClassList
        The initial classlist to represent in this model.
    field : str
        The name of the field represented by this model.
    parent : QtWidgets.QWidget
        The parent widget for the model.

    """

    def __init__(self, classlist: RATapi.ClassList[T], parent: QtWidgets.QWidget):
        super().__init__(parent)
        self.parent = parent

        self.classlist = classlist
        self.item_type = classlist._class_handle
        self.edit_mode = False

    def rowCount(self, parent=None) -> int:
        return len(self.classlist)

    def data(self, index, role=QtCore.Qt.ItemDataRole.DisplayRole) -> str:
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            row = index.row()
            return self.classlist[row].name

    def get_item(self, row: int) -> T:
        """Get an item from the ClassList.

        Parameters
        ----------
        row : int
            The index of the ClassList to get.

        Returns
        -------
        T
            The relevant item from the classlist.

        """
        return self.classlist[row]

    def set_data(self, row: int, param: str, value: Any):
        """Set data for an item in the ClassList.

        Parameters
        ----------
        row : int
            The index of the ClassList to get.
        param : str
            The parameter of the item to change.
        value : Any
            The value to set the parameter to.

        """
        setattr(self.classlist[row], param, value)
        self.endResetModel()

    def append_item(self):
        """Append an item to the ClassList."""
        self.classlist.append(self.item_type())
        self.endResetModel()

    def delete_item(self, row: int):
        """Delete an item in the ClassList.

        Parameters
        ----------
        row : int
            The row containing the item to delete.

        """
        self.classlist.pop(row)
        self.endResetModel()


class AbstractProjectListWidget(QtWidgets.QWidget):
    """An abstract base widget for editing items kept in a list."""

    item_type = "item"

    def __init__(self, field: str, parent):
        super().__init__(parent)
        self.field = field
        self.parent = parent
        self.project_widget = self.parent.parent
        self.edit_mode = False
        self.model = None

        layout = QtWidgets.QHBoxLayout()

        item_list = QtWidgets.QVBoxLayout()

        self.list = QtWidgets.QListView(parent)
        self.list.setSizePolicy(QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding)

        buttons = QtWidgets.QHBoxLayout()

        self.add_button = QtWidgets.QPushButton("+")
        self.add_button.setHidden(True)
        self.add_button.pressed.connect(self.append_item)
        buttons.addWidget(self.add_button)

        self.delete_button = QtWidgets.QPushButton(icon=QtGui.QIcon(path_for("delete.png")))
        self.delete_button.setHidden(True)
        self.delete_button.pressed.connect(self.delete_item)
        buttons.addWidget(self.delete_button)

        item_list.addWidget(self.list)
        item_list.addLayout(buttons)

        layout.addLayout(item_list)

        self.item_view = QtWidgets.QScrollArea(parent)
        self.item_view.setWidgetResizable(True)
        layout.addWidget(self.item_view)

        self.setLayout(layout)

    def update_model(self, classlist):
        """Update the list model to synchronise with the project field.

        Parameters
        ----------
        classlist: RATapi.ClassList
            The classlist to set in the model.

        """
        self.model = ClassListItemModel(classlist, self)
        self.list.setModel(self.model)
        # this signal changes the current contrast shown in the editor to be the currently highlighted list item
        self.list.selectionModel().currentChanged.connect(lambda index, _: self.view_stack.setCurrentIndex(index.row()))

        self.update_item_view()

    def update_item_view(self):
        """Update the item views to correspond with the list model."""

        self.view_stack = QtWidgets.QStackedWidget(self)

        if self.model is not None:
            # if there are no items, replace the widget with information
            if self.model.rowCount() == 0:
                self.view_stack = QtWidgets.QLabel(
                    f"No {self.item_type}s are currently defined! Edit the project to add a {self.item_type}."
                )
                self.view_stack.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

            for i in range(0, self.model.rowCount()):
                if self.edit_mode:
                    widget = self.create_editor(i)
                else:
                    widget = self.create_view(i)
                self.view_stack.addWidget(widget)

            self.item_view.setWidget(self.view_stack)

    def edit(self):
        """Update the view to be in edit mode."""
        self.add_button.setVisible(True)
        self.delete_button.setVisible(True)
        self.edit_mode = True
        self.update_item_view()

    def append_item(self):
        """Append an item to the model if the model exists."""
        if self.model is not None:
            self.model.append_item()

        new_widget_index = self.model.rowCount() - 1
        # handle if no contrasts currently exist
        if isinstance(self.view_stack, QtWidgets.QLabel):
            self.view_stack = QtWidgets.QStackedWidget(self)
            self.item_view.setWidget(self.view_stack)

        # add contrast viewer/editor to stack without resetting entire stack
        if self.edit_mode:
            self.view_stack.addWidget(self.create_editor(new_widget_index))
        else:
            self.view_stack.addWidget(self.create_view(new_widget_index))

    def delete_item(self):
        """Delete the currently selected item."""
        if self.model is not None:
            selection_model = self.list.selectionModel()
            self.model.delete_item(selection_model.currentIndex().row())

        self.update_item_view()

    def create_view(self, i: int) -> QtWidgets.QWidget:
        """Create the view widget for a specific item.

        Parameters
        ----------
        i : int
            The index of the classlist item displayed by this widget.

        Returns
        -------
        QtWidgets.QWidget
            The widget that displays the classlist item.

        """
        raise NotImplementedError

    def create_editor(self, i: int) -> QtWidgets.QWidget:
        """Create the edit widget for a specific item.

        Parameters
        ----------
        i : int
            The index of the classlist item displayed by this widget.

        Returns
        -------
        QtWidgets.QWidget
            The widget that allows the classlist item to be edited.

        """
        raise NotImplementedError


class LayerStringListModel(QtCore.QStringListModel):
    """A string list that supports drag and drop."""

    def flags(self, index):
        # we disable ItemIsDropEnabled to disable overwriting of items via drop
        flags = super().flags(index)
        if index.isValid():
            flags &= ~QtCore.Qt.ItemFlag.ItemIsDropEnabled

        return flags

    def supportedDropActions(self):
        return QtCore.Qt.DropAction.MoveAction

class StandardLayerModelWidget(QtWidgets.QWidget):
    """Widget for standard layer contrast models."""

    def __init__(self, init_list: list[str], parent=None):
        super().__init__(parent)

        self.model = LayerStringListModel(init_list, self)
        self.layer_list = QtWidgets.QListView(parent)
        self.layer_list.setModel(self.model)
        self.layer_list.setItemDelegateForColumn(0, ProjectFieldDelegate(parent.project_widget, "layers", self))
        self.layer_list.setDragEnabled(True)
        self.layer_list.setAcceptDrops(True)
        self.layer_list.setDropIndicatorShown(True)

        add_button = QtWidgets.QPushButton("+")
        add_button.pressed.connect(self.append_item)
        delete_button = QtWidgets.QPushButton(icon=QtGui.QIcon(path_for("delete.png")))
        delete_button.pressed.connect(self.delete_item)

        buttons = QtWidgets.QHBoxLayout()
        buttons.addWidget(add_button)
        buttons.addWidget(delete_button)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.layer_list)
        layout.addLayout(buttons)

        self.setLayout(layout)

    def append_item(self):
        """Append an item below the currently selected item."""
        if self.model is not None:
            selection_model = self.layer_list.selectionModel()
            self.model.insertRow(selection_model.currentIndex().row() + 1)
            self.model.setData(self.model.index(selection_model.currentIndex().row() + 1, 0), "Choose Layer...")

    def delete_item(self):
        """Delete the currently selected item."""
        if self.model is not None:
            selection_model = self.layer_list.selectionModel()
            index = selection_model.currentIndex()
            self.model.removeRow(index.row())
            self.model.dataChanged.emit(index, index)


class ContrastWidget(AbstractProjectListWidget):
    """Widget for viewing and editing Contrasts."""

    item_type = "contrast"

    def compose_widget(self, i: int, data_widget: Callable[[str], QtWidgets.QWidget]) -> QtWidgets.QWidget:
        """Create the base grid layouts for the widget.

        Parameters
        ----------
        i : int
            The row of the contrasts list to display in this widget.
        data_widget : Callable[[str], QtWidgets.QWidget]
            A function which takes a field name and returns the data widget for that field.

        Returns
        -------
        QtWidgets.QWidget
            The resulting widget for the item.

        """
        top_grid = QtWidgets.QGridLayout()
        top_grid.addWidget(QtWidgets.QLabel("Contrast Name:"), 0, 0)
        top_grid.addWidget(data_widget("name"), 0, 1, 1, -1)

        top_grid.addWidget(QtWidgets.QLabel("Background:"), 1, 0)
        top_grid.addWidget(data_widget("background"), 1, 1, 1, 2)
        top_grid.addWidget(QtWidgets.QLabel("Background Action:"), 1, 3)
        top_grid.addWidget(data_widget("background_action"), 1, 4, 1, 2)

        top_grid.addWidget(QtWidgets.QLabel("Resolution:"), 2, 0)
        top_grid.addWidget(data_widget("resolution"), 2, 1)
        top_grid.addWidget(QtWidgets.QLabel("Scalefactor:"), 2, 2)
        top_grid.addWidget(data_widget("scalefactor"), 2, 3)
        top_grid.addWidget(QtWidgets.QLabel("Data:"), 2, 4)
        top_grid.addWidget(data_widget("data"), 2, 5)

        top_grid.setVerticalSpacing(10)

        settings_row = QtWidgets.QHBoxLayout()
        settings_row.addWidget(QtWidgets.QLabel("Use resampling:"))
        resampling_checkbox = QtWidgets.QCheckBox()
        resampling_checkbox.setChecked(self.model.get_item(i).resample)
        resampling_checkbox.checkStateChanged.connect(
            lambda s: self.model.set_data(i, "resample", (s == QtCore.Qt.CheckState.Checked))
        )
        settings_row.addWidget(resampling_checkbox)
        settings_row.addStretch()

        model_grid = QtWidgets.QGridLayout()
        model_grid.addWidget(QtWidgets.QLabel("Bulk in:"), 0, 0)
        model_grid.addWidget(data_widget("bulk_in"), 0, 1)
        model_grid.addWidget(QtWidgets.QLabel("Model:"), 1, 0)
        model_grid.addWidget(data_widget("model"), 1, 1)
        model_grid.addWidget(QtWidgets.QLabel("Bulk out:"), 2, 0)
        model_grid.addWidget(data_widget("bulk_out"), 2, 1)

        layout = QtWidgets.QVBoxLayout()
        layout.addLayout(top_grid)
        layout.addLayout(settings_row)
        layout.addStretch()
        layout.addLayout(model_grid)

        widget = QtWidgets.QWidget(self)
        widget.setLayout(layout)

        return widget

    def create_view(self, i: int) -> QtWidgets.QWidget:
        def data_box(field: str) -> QtWidgets.QWidget:
            """Create a read only line edit box for display."""
            current_data = getattr(self.model.get_item(i), field)
            if field == "model":
                if self.project_widget.parent_model.project.model == LayerModels.StandardLayers:
                    widget = QtWidgets.QListWidget(parent=self)
                    widget.addItems(current_data)
                else:
                    widget = QtWidgets.QLineEdit(current_data[0])
                    widget.setReadOnly(True)
            else:
                widget = QtWidgets.QLineEdit(current_data)
                widget.setReadOnly(True)

            return widget

        return self.compose_widget(i, data_box)

    def create_editor(self, i: int) -> QtWidgets.QWidget:
        self.comboboxes = {}

        def data_combobox(field: str) -> QtWidgets.QWidget:
            current_data = getattr(self.model.get_item(i), field)
            match field:
                case "name":
                    widget = QtWidgets.QLineEdit(current_data)
                    widget.textChanged.connect(lambda text: self.model.set_data(i, "name", text))
                    return widget
                case "background_action":
                    widget = QtWidgets.QComboBox()
                    for action in BackgroundActions:
                        widget.addItem(str(action), action)
                    widget.setCurrentText(current_data)
                    widget.currentTextChanged.connect(
                        lambda: self.model.set_data(i, "background_action", widget.currentData())
                    )
                    return widget
                case "model":
                    if self.project_widget.draft_project["model"] == LayerModels.StandardLayers:
                        widget = StandardLayerModelWidget(current_data, self)
                        widget.model.dataChanged.connect(lambda: self.model.set_data(i, field, widget.model.stringList()))
                        widget.model.rowsMoved.connect(lambda: self.model.set_data(i, field, widget.model.stringList()))
                        return widget
                    else:
                        widget = QtWidgets.QComboBox(self)
                        widget.addItem("", [])
                        for file in self.project_widget.draft_project["custom_files"]:
                            widget.addItem(file.name, [file.name])
                        widget.setCurrentText(current_data[0])
                        widget.currentTextChanged.connect(lambda: self.model.set_data(i, field, widget.currentData()))
                        return widget
                # all other cases are comboboxes with data from other widget tables
                case "data" | "bulk_in" | "bulk_out":
                    project_field_name = field
                    pass
                case _:
                    project_field_name = field + "s"
                    pass

            project_field = self.project_widget.draft_project[project_field_name]
            combobox = QtWidgets.QComboBox(self)
            items = [""] + [item.name for item in project_field]
            combobox.addItems(items)
            combobox.setCurrentText(current_data)
            combobox.currentTextChanged.connect(lambda: self.model.set_data(i, field, combobox.currentText()))
            combobox.setSizePolicy(QtWidgets.QSizePolicy.Policy.MinimumExpanding, QtWidgets.QSizePolicy.Policy.Fixed)

            return combobox

        return self.compose_widget(i, data_combobox)
