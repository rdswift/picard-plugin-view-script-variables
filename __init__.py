# -*- coding: utf-8 -*-

from collections import namedtuple
from enum import IntEnum

from PyQt6 import QtCore, QtWidgets

from picard.plugin3.api import (
    BaseAction,
    File,
    PluginApi,
    Track,
    t_,
)
from picard.tags import preserved_tag_names

from .ui_variables_dialog import Ui_VariablesDialog


TagValue = namedtuple("TagValue", "value type")


class ValueTypes(IntEnum):
    SINGLE = 1
    MULTI = 2


class ViewVariables(BaseAction):
    TITLE = t_("action.title", "View script variables")

    def callback(self, objs):
        obj = objs[0]
        files = self.api.tagger.get_files_from_objects(objs)
        if files:
            obj = files[0]
        dialog = ViewVariablesDialog(obj, api=self.api)
        dialog.exec()


class ViewVariableDetails(QtWidgets.QDialog):
    def __init__(self, name: str, data: TagValue, parent=None, api: PluginApi = None):
        super().__init__(parent)
        self.api = api
        self.name = name
        self.value = data.value
        self.type = data.type
        self.setup_ui()

    def setup_ui(self):
        title = self.api.trn(
            "ui.details.window.title",
            "%{tag_name}% value",
            "%{tag_name}% values",
            self.type,
            tag_name=self.name
        )

        # Set window width to display full tag name without elipses if possible (within reason)
        window_width = min(len(title) * 10 + 100, 1000)
        self.setMinimumWidth(window_width)
        self.setMaximumWidth(1000)
        self.setMaximumHeight(500)

        self.setWindowTitle(title)
        self.setWindowModality(QtCore.Qt.WindowModality.ApplicationModal)
        self.verticallayout = QtWidgets.QVBoxLayout(self)

        if self.type == ValueTypes.MULTI:
            content = QtWidgets.QListWidget()
            content.addItems(self.value)
        else:
            content = QtWidgets.QScrollArea()
            text = QtWidgets.QLabel()
            text.setWordWrap(True)
            text.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
            text.setText(
                self.value
                if self.type == ValueTypes.SINGLE
                else self.api.tr("ui.type_error", "Unknown value type.")
            )
            content.setWidget(text)

        self.verticallayout.addWidget(content)


class ViewVariablesDialog(QtWidgets.QDialog):
    def __init__(self, obj, parent=None, api: PluginApi = None):
        super().__init__(parent)
        self.api = api
        self.separator_rows = set()
        self.PRESERVED_TAGS = list(preserved_tag_names())
        self.ui = Ui_VariablesDialog()
        self.ui.setupUi(self)
        font = self.ui.metadata_table.font()
        font.setBold(True)
        self.ui.metadata_table.horizontalHeaderItem(0).setFont(font)
        self.ui.metadata_table.horizontalHeaderItem(1).setFont(font)
        self.ui.metadata_table.horizontalHeaderItem(0).setText(
            self.api.tr("ui.header0", "Variable")
        )
        self.ui.metadata_table.horizontalHeaderItem(1).setText(
            self.api.tr("ui.header1", "Value")
        )
        self.ui.buttonBox.rejected.connect(self.reject)
        metadata = obj.metadata
        if isinstance(obj, File):
            self.setWindowTitle(
                self.api.tr("ui.title_file", "File: %s") % obj.base_filename
            )
        elif isinstance(obj, Track):
            tn = metadata["tracknumber"]
            if len(tn) == 1:
                tn = "0" + tn
            self.setWindowTitle(
                self.api.tr("ui.title_track", "Track: %s %s") % (tn, metadata["title"])
            )
        else:
            self.setWindowTitle(self.api.tr("ui.title_variables", "Variables"))
        self._display_metadata(metadata)
        self.ui.metadata_table.cellDoubleClicked.connect(self.show_details)

    def _display_metadata(self, metadata):
        keys = metadata.keys()
        keys = sorted(
            keys,
            key=lambda key: "0" + key
            if key in self.PRESERVED_TAGS and key.startswith("~")
            else "1" + key
            if key.startswith("~")
            else "2" + key,
        )
        media = hidden = album = False
        table = self.ui.metadata_table
        key_example, value_example = self.get_table_items(table, 0)
        self.key_flags = key_example.flags()
        self.value_flags = value_example.flags()
        table.setRowCount(len(keys) + 3)
        i = 0
        for key in keys:
            if key in self.PRESERVED_TAGS and key.startswith("~"):
                if not media:
                    self.add_separator_row(
                        table, i, self.api.tr("ui.section_file", "File variables")
                    )
                    i += 1
                    media = True
            elif key.startswith("~"):
                if not hidden:
                    self.add_separator_row(
                        table, i, self.api.tr("ui.section_hidden", "Hidden variables")
                    )
                    i += 1
                    hidden = True
            else:
                if not album:
                    self.add_separator_row(
                        table, i, self.api.tr("ui.section_tag", "Tag variables")
                    )
                    i += 1
                    album = True

            key_item, value_item = self.get_table_items(table, i)
            tooltip = self.api.tr("ui.tooltip", "Double-click for details")
            key_item.setToolTip(tooltip)
            value_item.setToolTip(tooltip)
            i += 1
            key_item.setText("_" + key[1:] if key.startswith("~") else key)
            if key in metadata:
                value = metadata.getall(key)
                if len(value) == 1 and value[0] != "":
                    value = value[0]
                    value_item.setData(
                        QtCore.Qt.ItemDataRole.UserRole,
                        TagValue(value=value, type=ValueTypes.SINGLE),
                    )
                else:
                    value_item.setData(
                        QtCore.Qt.ItemDataRole.UserRole,
                        TagValue(value=value, type=ValueTypes.MULTI),
                    )
                    value = repr(value)
                value_item.setText(value)

    def add_separator_row(self, table, i, title):
        key_item, value_item = self.get_table_items(table, i)
        font = key_item.font()
        font.setBold(True)
        key_item.setFont(font)
        key_item.setText(title)
        self.separator_rows.add(i)

    def get_table_items(self, table, i):
        key_item = table.item(i, 0)
        value_item = table.item(i, 1)
        if not key_item:
            key_item = QtWidgets.QTableWidgetItem()
            key_item.setFlags(self.key_flags)
            table.setItem(i, 0, key_item)
        if not value_item:
            value_item = QtWidgets.QTableWidgetItem()
            value_item.setFlags(self.value_flags)
            table.setItem(i, 1, value_item)
        return key_item, value_item

    def show_details(self, row: int, column: int):
        if row in self.separator_rows:
            return
        dialog = ViewVariableDetails(
            name=self.ui.metadata_table.item(row, 0).text(),
            data=self.ui.metadata_table.item(row, 1).data(
                QtCore.Qt.ItemDataRole.UserRole
            ),
            parent=self,
            api=self.api,
        )
        dialog.exec()


def enable(api: PluginApi):
    """Called when plugin is enabled."""
    api.register_file_action(ViewVariables)
    api.register_track_action(ViewVariables)
