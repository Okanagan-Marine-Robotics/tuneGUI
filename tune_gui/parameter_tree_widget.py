#!/usr/bin/env python3

from PyQt5.QtWidgets import (QTreeWidget, QTreeWidgetItem, QStyledItemDelegate,
                             QLineEdit, QDoubleSpinBox, QSpinBox, QCheckBox, QWidget, QHBoxLayout)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor

class Columns:
    """Constants for Tree Widget Columns"""
    NAME = 0
    VALUE = 1
    TYPE = 2

def get_param_category(type_name: str) -> str:
    """Normalize parameter type names to basic categories."""
    type_name = type_name.lower()
    if type_name in ['int', 'integer', 'int64']:
        return 'int'
    elif type_name in ['float', 'double']:
        return 'float'
    elif type_name in ['bool', 'boolean']:
        return 'bool'
    return 'str'

class ParameterItemDelegate(QStyledItemDelegate):
    """Custom delegate for parameter editing"""
    
    def createEditor(self, parent, option, index):
        """Create appropriate editor based on parameter type"""
        if index.column() != Columns.VALUE:
            return super().createEditor(parent, option, index)
            
        tree_widget = self.parent()
        if not isinstance(tree_widget, QTreeWidget):
            return super().createEditor(parent, option, index)

        item = tree_widget.itemFromIndex(index)
        if item is None:
            return super().createEditor(parent, option, index)
            
        param_type = item.text(Columns.TYPE)
        category = get_param_category(param_type)
        
        if category == 'int':
            editor = QSpinBox(parent)
            editor.setRange(-2147483648, 2147483647)
            return editor
        elif category == 'float':
            editor = QDoubleSpinBox(parent)
            editor.setRange(-1e6, 1e6)
            editor.setDecimals(4)
            return editor
        elif category == 'bool':
            container = QWidget(parent)
            layout = QHBoxLayout(container)
            layout.setContentsMargins(0, 0, 0, 0)
            
            layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            checkbox = QCheckBox(container)
            layout.addWidget(checkbox)
            
            checkbox.toggled.connect(lambda: self.commitAndClose(container))
            return container
        else:
            return QLineEdit(parent)

    def commitAndClose(self, editor):
        """Helper to commit data and close editor immediately"""
        self.commitData.emit(editor)
        self.closeEditor.emit(editor)
            
    def setEditorData(self, editor, index):
        """Set initial data in editor"""
        if index.column() != Columns.VALUE:
            return super().setEditorData(editor, index)
            
        value = index.data(Qt.ItemDataRole.EditRole)
        if value is None:
            value = index.data(Qt.ItemDataRole.DisplayRole)
        
        if isinstance(editor, QSpinBox):
            try:
                editor.setValue(int(value))
            except (ValueError, TypeError):
                pass
        elif isinstance(editor, QDoubleSpinBox):
            try:
                editor.setValue(float(value))
            except (ValueError, TypeError):
                pass
        elif isinstance(editor, QWidget): # Boolean container
            checkbox = editor.findChild(QCheckBox)
            if checkbox:
                is_checked = str(value).lower() in ['true', '1', 'yes', 'on']
                checkbox.blockSignals(True)
                checkbox.setChecked(is_checked)
                checkbox.blockSignals(False)
        elif isinstance(editor, QLineEdit):
            editor.setText(str(value))
            
    def setModelData(self, editor, model, index):
        """Save editor data back to model"""
        if index.column() != Columns.VALUE or model is None:
            return super().setModelData(editor, model, index)
            
        value = None
        str_value = ""
        
        if isinstance(editor, QSpinBox):
            value = editor.value()
            str_value = str(value)
        elif isinstance(editor, QDoubleSpinBox):
            value = editor.value()
            str_value = str(value)
        elif isinstance(editor, QWidget): # Boolean
            checkbox = editor.findChild(QCheckBox)
            if checkbox:
                value = checkbox.isChecked()
                str_value = str(value)
        elif isinstance(editor, QLineEdit):
            value = editor.text()
            str_value = value

        if value is not None:
            model.setData(index, value, Qt.ItemDataRole.EditRole)
            model.setData(index, str_value, Qt.ItemDataRole.DisplayRole)


class ParameterTreeWidget(QTreeWidget):
    """Custom tree widget for displaying and editing ROS2 parameters"""
    
    parameter_changed = pyqtSignal(str, object)  # (param_name, new_value)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setColumnCount(3)
        self.setHeaderLabels(["Parameter", "Value", "Type"])
        
        self.setColumnWidth(Columns.NAME, 300)
        self.setColumnWidth(Columns.VALUE, 200)
        self.setColumnWidth(Columns.TYPE, 100)
        
        self.setItemDelegate(ParameterItemDelegate(self))
        self.itemChanged.connect(self.on_item_changed)
        
        self.parameters = {}
        self.param_to_item = {}
        self.updating = False
        
    def set_parameters(self, node_name: str, parameters: dict):
        """Set parameters for a specific node"""
        self.blockSignals(True)
        try:
            self.clear()
            self.parameters = parameters
            self.param_to_item.clear()
            
            self._build_tree(node_name, parameters)
            self.expandAll()
        finally:
            self.blockSignals(False)
        
    def set_yaml_parameters(self, parameters: dict):
        """Set parameters from YAML file (flat structure)"""
        self.blockSignals(True)
        try:
            self.clear()
            self.parameters = parameters
            self.param_to_item.clear()
            
            self._build_tree_from_paths(parameters)
            self.expandAll()
        finally:
            self.blockSignals(False)
        
    def _build_tree(self, node_name: str, parameters: dict):
        for param_name, param_info in parameters.items():
            self._add_parameter_item(None, param_name, param_info)
            
    def _build_tree_from_paths(self, parameters: dict):
        tree_structure = {}
        
        for param_path, value in parameters.items():
            parts = param_path.split('.')
            current = tree_structure
            
            for i, part in enumerate(parts[:-1]):
                if part not in current:
                    current[part] = {}
                current = current[part]
            
            current[parts[-1]] = value
            
        self._add_tree_structure(None, tree_structure, [])
        
    def _add_tree_structure(self, parent, structure, path):
        for key, value in structure.items():
            current_path = path + [key]
            
            if isinstance(value, dict):
                item = QTreeWidgetItem(parent or self)
                item.setText(Columns.NAME, key)
                item.setForeground(Columns.NAME, QColor(150, 150, 150))
                self._add_tree_structure(item, value, current_path)
            else:
                param_path = '.'.join(current_path)
                param_info = {'value': value, 'type': type(value).__name__}
                self._add_parameter_item(parent, key, param_info, param_path)
                
    def _add_parameter_item(self, parent, param_name: str, param_info: dict, full_path: str | None = None):
        item = QTreeWidgetItem(parent or self)
        item.setText(Columns.NAME, param_name)
        
        value = param_info.get('value')
        param_type = param_info.get('type', type(value).__name__)
        
        item.setText(Columns.VALUE, str(value))
        item.setData(Columns.VALUE, Qt.ItemDataRole.EditRole, value)
        
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
        item.setText(Columns.TYPE, param_type)
        
        path = full_path if full_path else param_name
        item.setData(Columns.NAME, Qt.ItemDataRole.UserRole, path)
        self.param_to_item[path] = item
        
        category = get_param_category(param_type)
        color_map = {
            'int': QColor(100, 200, 100),
            'float': QColor(100, 150, 255),
            'bool': QColor(255, 150, 100),
            'str': QColor(200, 200, 100)
        }
        
        if category in color_map:
            item.setForeground(Columns.TYPE, color_map[category])

    def update_parameter_values(self, parameters: dict):
        self.updating = True
        for param_name, param_info in parameters.items():
            item = self.param_to_item.get(param_name)
            
            if item:
                new_value = param_info.get('value')
                current_value = item.text(Columns.VALUE)
                
                if str(new_value) != current_value:
                    item.setText(Columns.VALUE, str(new_value))
                    item.setData(Columns.VALUE, Qt.ItemDataRole.EditRole, new_value)
                    
        self.updating = False
        
    def on_item_changed(self, item: QTreeWidgetItem, column: int):
        if self.updating or column != Columns.VALUE:
            return
        
        param_path = item.data(Columns.NAME, Qt.ItemDataRole.UserRole)
        if not param_path:
            return
            
        new_value_str = item.text(Columns.VALUE)
        param_type = item.text(Columns.TYPE)
        category = get_param_category(param_type)
        
        try:
            new_value = None
            if category == 'int':
                new_value = int(new_value_str)
            elif category == 'float':
                new_value = float(new_value_str)
            elif category == 'bool':
                val_lower = new_value_str.lower()
                if val_lower in ['true', '1', 'yes', 'on']:
                    new_value = True
                elif val_lower in ['false', '0', 'no', 'off']:
                    new_value = False
                else:
                    raise ValueError(f"Invalid boolean string: {new_value_str}")
            else:
                new_value = new_value_str
            
            self.parameter_changed.emit(param_path, new_value)
            
        except ValueError:
            prev_value = item.data(Columns.VALUE, Qt.ItemDataRole.EditRole)
            if prev_value is None and param_path in self.parameters:
                prev_value = self.parameters[param_path].get('value')
                
            self.updating = True
            item.setText(Columns.VALUE, str(prev_value))
            self.updating = False