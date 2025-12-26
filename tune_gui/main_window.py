#!/usr/bin/env python3

import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QSplitter, QPushButton, QFileDialog,
                             QStatusBar, QLabel, QComboBox, QMessageBox)
from PyQt5.QtCore import Qt, QTimer

import rclpy
from rclpy.node import Node

from tune_gui.parameter_tree_widget import ParameterTreeWidget
from tune_gui.ros2_parameter_client import ROS2ParameterClient
from tune_gui.yaml_handler import YAMLHandler
from tune_gui.mission_command_publisher import MissionCommandPublisher


class TuneGUIMainWindow(QMainWindow):
    def __init__(self, node: Node, params_file: str | None = None):
        super().__init__()
        self.node = node
        self.ros2_client = ROS2ParameterClient(node)
        self.yaml_handler = YAMLHandler()
        self.params_file = params_file
        self.mission_command_pub = MissionCommandPublisher(node)
        
        self.init_ui()
        self.setup_timers()
        
        if self.params_file and os.path.exists(self.params_file):
            self.load_yaml_file(self.params_file)
        
        self.refresh_nodes()
        
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("ROS2 Parameter Tuning GUI")
        self.setGeometry(100, 100, 1400, 800)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        self._setup_toolbar(main_layout)
        self._setup_parameter_area(main_layout)
        self._setup_simulation_toggle(main_layout)
        
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.update_status("Ready")

    def _setup_toolbar(self, parent_layout):
        toolbar_layout = QHBoxLayout()
        
        toolbar_layout.addWidget(QLabel("Node:"))
        self.node_selector = QComboBox()
        self.node_selector.currentTextChanged.connect(self.on_node_selected)
        toolbar_layout.addWidget(self.node_selector)
        
        self.refresh_btn = QPushButton("Refresh Nodes")
        self.refresh_btn.clicked.connect(self.refresh_nodes)
        toolbar_layout.addWidget(self.refresh_btn)
        
        toolbar_layout.addStretch()
        
        self.load_yaml_btn = QPushButton("Load params.yaml")
        self.load_yaml_btn.clicked.connect(self.load_yaml_dialog)
        toolbar_layout.addWidget(self.load_yaml_btn)
        
        self.save_yaml_btn = QPushButton("Save params.yaml")
        self.save_yaml_btn.clicked.connect(self.save_yaml_file)
        self.save_yaml_btn.setEnabled(False)
        toolbar_layout.addWidget(self.save_yaml_btn)
        
        self.apply_yaml_btn = QPushButton("Apply YAML to Nodes")
        self.apply_yaml_btn.clicked.connect(self.apply_yaml_to_nodes)
        self.apply_yaml_btn.setEnabled(False)
        toolbar_layout.addWidget(self.apply_yaml_btn)
        
        parent_layout.addLayout(toolbar_layout)
        
    def _setup_simulation_toggle(self, parent_layout):
        self.toggle_sim_btn = QPushButton("Toggle Mission Start")
        self.toggle_sim_btn.clicked.connect(self.toggle_mission_start)
        #self.toggle_sim_btn.setEnabled(False)
        parent_layout.addWidget(self.toggle_sim_btn)

    def _setup_parameter_area(self, parent_layout):
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        node_widget = QWidget()
        node_layout = QVBoxLayout(node_widget)
        node_layout.addWidget(QLabel("<b>Node Parameters</b>"))
        
        self.node_param_tree = ParameterTreeWidget()
        self.node_param_tree.parameter_changed.connect(self.on_node_parameter_changed)
        node_layout.addWidget(self.node_param_tree)
        
        yaml_widget = QWidget()
        yaml_layout = QVBoxLayout(yaml_widget)
        yaml_layout.addWidget(QLabel("<b>params.yaml Parameters</b>"))
        
        self.yaml_param_tree = ParameterTreeWidget()
        self.yaml_param_tree.parameter_changed.connect(self.on_yaml_parameter_changed)
        yaml_layout.addWidget(self.yaml_param_tree)
        
        splitter.addWidget(node_widget)
        splitter.addWidget(yaml_widget)
        splitter.setSizes([700, 700])
        
        parent_layout.addWidget(splitter)
        
    def setup_timers(self):
        """Setup periodic update timers (refresh nodes and parameters every 500ms)"""
        self.param_refresh_timer = QTimer()
        self.param_refresh_timer.timeout.connect(self.refresh_current_node_params)
        self.param_refresh_timer.start(500)
        
    def refresh_nodes(self):
        """Refresh the list of available nodes"""
        self.update_status("Discovering nodes...")
        nodes = self.ros2_client.get_node_names()
        
        current_text = self.node_selector.currentText()
        self.node_selector.clear()
        self.node_selector.addItems(nodes)
        
        # Try to restore previous selection
        if current_text in nodes:
            self.node_selector.setCurrentText(current_text)
        
        self.update_status(f"Found {len(nodes)} nodes")
        
    def on_node_selected(self, node_name: str):
        """Handle node selection change"""
        if not node_name:
            return
            
        self.update_status(f"Loading parameters for {node_name}...")
        params = self.ros2_client.get_node_parameters(node_name)
        self.node_param_tree.set_parameters(node_name, params)
        self.update_status(f"Loaded {len(params)} parameters from {node_name}")
        
    def refresh_current_node_params(self):
        """Refresh parameters for the currently selected node"""
        node_name = self.node_selector.currentText()
        if not node_name:
            return
            
        params = self.ros2_client.get_node_parameters(node_name)
        self.node_param_tree.update_parameter_values(params)
        
    def on_node_parameter_changed(self, param_name: str, new_value):
        """Handle parameter change in node parameter tree"""
        node_name = self.node_selector.currentText()
        if not node_name:
            return
            
        success = self.ros2_client.set_parameter(node_name, param_name, new_value)
        if success:
            self.update_status(f"Updated {node_name}.{param_name} = {new_value}")
        else:
            self.update_status(f"Failed to update {node_name}.{param_name}")
            QMessageBox.warning(self, "Parameter Update Failed", 
                              f"Could not update parameter {param_name}")
            
    def toggle_mission_start(self):
        self.mission_command_pub.toggle_mission_control()
        self.update_status("published?")
            
    def load_yaml_dialog(self):
        """Open file dialog to load params.yaml"""
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Load params.yaml", "", "YAML Files (*.yaml *.yml);;All Files (*)")
        
        if file_name:
            self.load_yaml_file(file_name)
            
    def load_yaml_file(self, file_path: str):
        """Load parameters from YAML file"""
        try:
            self.yaml_handler.load_yaml(file_path)
            self.params_file = file_path
            
            params = self.yaml_handler.get_all_parameters()
            self.yaml_param_tree.set_yaml_parameters(params)
            
            self.save_yaml_btn.setEnabled(True)
            self.apply_yaml_btn.setEnabled(True)
            self.update_status(f"Loaded {file_path}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error Loading YAML", str(e))
            self.update_status(f"Error loading YAML: {e}")
            
    def on_yaml_parameter_changed(self, param_path: str, new_value):
        """Handle parameter change in YAML parameter tree"""
        try:
            self.yaml_handler.update_parameter(param_path, new_value)
            self.update_status(f"Modified YAML parameter: {param_path}")
        except Exception as e:
            QMessageBox.warning(self, "Update Failed", str(e))
            
    def save_yaml_file(self):
        """Save current YAML parameters to file"""
        if not self.params_file:
            file_name, _ = QFileDialog.getSaveFileName(
                self, "Save params.yaml", "", "YAML Files (*.yaml *.yml)")
            if not file_name:
                return
            self.params_file = file_name
            
        try:
            self.yaml_handler.save_yaml(self.params_file)
            self.update_status(f"Saved {self.params_file}")
            QMessageBox.information(self, "Success", f"Parameters saved to {self.params_file}")
        except Exception as e:
            QMessageBox.critical(self, "Save Failed", str(e))
            
    def apply_yaml_to_nodes(self):
        """Apply YAML parameters to running nodes"""
        params = self.yaml_handler.get_all_parameters()
        
        applied_count = 0
        failed_count = 0
        
        for param_path, value in params.items():
            # Parse node name and parameter name from path
            # Format: node_name.ros__parameters.param_name or node_name.param_name
            parts = param_path.split('.')
            if len(parts) < 2:
                continue
                
            node_name = parts[0]
            
            # Skip ros__parameters if present
            if parts[1] == 'ros__parameters':
                param_name = '.'.join(parts[2:])
            else:
                param_name = '.'.join(parts[1:])
            
            success = self.ros2_client.set_parameter(node_name, param_name, value)
            if success:
                applied_count += 1
            else:
                failed_count += 1
                
        msg = f"Applied {applied_count} parameters"
        if failed_count > 0:
            msg += f", {failed_count} failed"
            
        self.update_status(msg)
        QMessageBox.information(self, "Apply Complete", msg)
        
    def update_status(self, message: str):
        """Update status bar message"""
        self.status_bar.showMessage(message)
        
    def closeEvent(self, event):
        """Handle window close event"""
        self.param_refresh_timer.stop()
        event.accept()


def main(args=None):
    """Main entry point for the GUI"""
    rclpy.init(args=args)
    
    node = Node('tune_gui_node')
    
    # Get params file from command line if provided
    params_file: str | None = None
    if len(sys.argv) > 1:
        params_file = sys.argv[1]
    
    app = QApplication(sys.argv)
    app.setStyle('Fusion') 
    
    window = TuneGUIMainWindow(node, params_file)
    window.show()
    
    timer = QTimer()
    timer.timeout.connect(lambda: rclpy.spin_once(node, timeout_sec=0))
    timer.start(10)  # Spin ROS2 every 10ms
    
    exit_code = app.exec_()
    
    node.destroy_node()
    rclpy.shutdown()
    
    sys.exit(exit_code)


if __name__ == '__main__':
    main()