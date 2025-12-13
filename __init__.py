# -*- coding: utf-8 -*-


from picard.plugin3.api import (
    BaseAction,
    File,
    PluginApi,
    Track,
)
from picard.tags import preserved_tag_names

from PyQt6 import QtWidgets

from .ui_variables_dialog import Ui_VariablesDialog


class ViewVariables(BaseAction):
    NAME = 'View script variables'

    def __init__(self):
        super().__init__(api=self.api)
        self.setText(self.api.tr("action.name", "View script variables"))

    def callback(self, objs):
        obj = objs[0]
        files = self.api.tagger.get_files_from_objects(objs)
        if files:
            obj = files[0]
        dialog = ViewVariablesDialog(obj, api=self.api)
        dialog.exec()


class ViewVariablesDialog(QtWidgets.QDialog):

    def __init__(self, obj, parent=None, api: PluginApi = None):
        super().__init__(parent)
        self.api = api
        self.PRESERVED_TAGS = list(preserved_tag_names())
        self.ui = Ui_VariablesDialog()
        self.ui.setupUi(self)
        font = self.ui.metadata_table.font()
        font.setBold(True)
        self.ui.metadata_table.horizontalHeaderItem(0).setFont(font)
        self.ui.metadata_table.horizontalHeaderItem(1).setFont(font)
        self.ui.metadata_table.horizontalHeaderItem(0).setText(self.api.tr('ui.header0', "Variable"))
        self.ui.metadata_table.horizontalHeaderItem(1).setText(self.api.tr('ui.header1', "Value"))
        self.ui.buttonBox.rejected.connect(self.reject)
        metadata = obj.metadata
        if isinstance(obj, File):
            self.setWindowTitle(self.api.tr('ui.title_file', "File: %s") % obj.base_filename)
        elif isinstance(obj, Track):
            tn = metadata['tracknumber']
            if len(tn) == 1:
                tn = "0" + tn
            self.setWindowTitle(self.api.tr('ui.title_track',"Track: %s %s") % (tn, metadata['title']))
        else:
            self.setWindowTitle(self.api.tr('ui.title_variables', "Variables"))
        self._display_metadata(metadata)

    def _display_metadata(self, metadata):
        keys = metadata.keys()
        keys = sorted(keys, key=lambda key:
                      '0' + key if key in self.PRESERVED_TAGS and key.startswith('~') else
                      '1' + key if key.startswith('~') else
                      '2' + key)
        media = hidden = album = False
        table = self.ui.metadata_table
        key_example, value_example = self.get_table_items(table, 0)
        self.key_flags = key_example.flags()
        self.value_flags = value_example.flags()
        table.setRowCount(len(keys) + 3)
        i = 0
        for key in keys:
            if key in self.PRESERVED_TAGS and key.startswith('~'):
                if not media:
                    self.add_separator_row(table, i, self.api.tr('ui.section_file', "File variables"))
                    i += 1
                    media = True
            elif key.startswith('~'):
                if not hidden:
                    self.add_separator_row(table, i, self.api.tr('ui.section_hidden', "Hidden variables"))
                    i += 1
                    hidden = True
            else:
                if not album:
                    self.add_separator_row(table, i, self.api.tr('ui.section_tag', "Tag variables"))
                    i += 1
                    album = True

            key_item, value_item = self.get_table_items(table, i)
            i += 1
            key_item.setText("_" + key[1:] if key.startswith('~') else key)
            if key in metadata:
                value = metadata.getall(key)
                if len(value) == 1 and value[0] != '':
                    value = value[0]
                else:
                    value = repr(value)
                value_item.setText(value)

    def add_separator_row(self, table, i, title):
        key_item, value_item = self.get_table_items(table, i)
        font = key_item.font()
        font.setBold(True)
        key_item.setFont(font)
        key_item.setText(title)

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


def enable(api: PluginApi):
    """Called when plugin is enabled."""
    api.register_file_action(ViewVariables)
    api.register_track_action(ViewVariables)
