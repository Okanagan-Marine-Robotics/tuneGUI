# tune_gui

PyQt5-based GUI for tuning ROS2 node parameters and editing `params.yaml` files in real-time.

## Features

- **Live Parameter Tuning**: View and edit parameters on running ROS2 nodes
- **YAML File Editing**: Load, edit, and save `params.yaml` files
- **Dual View**: Side-by-side comparison of live node parameters and YAML configuration
- **Type-Safe Editing**: Custom editors for integers, floats, booleans, and strings
- **Apply to Nodes**: Push YAML parameter changes to running nodes
- **Auto-Refresh**: Continuously monitors parameter changes (500ms update rate)

## Installation

### Dependencies

```bash
# Install PyQt5
sudo apt install python3-pyqt5

# Or via pip
pip3 install PyQt5
```

### Building

From the `ros2_ws` directory:

```bash
colcon build --packages-select tune_gui
source install/setup.bash
```

## Usage

### Launch with GUI

```bash
# Launch with default params.yaml (from okmr_automated_planner if available)
ros2 launch tune_gui tune_gui_launch.py

# Launch with specific params.yaml file
ros2 launch tune_gui tune_gui_launch.py params_file:=/path/to/params.yaml
```

### Run Directly

```bash
# Run without params file
ros2 run tune_gui tune_gui

# Run with params file as argument
ros2 run tune_gui tune_gui /path/to/params.yaml
```

## Workflows

### Tuning Parameters Live

1. Launch your ROS2 nodes (e.g., `automated_planner`)
2. Launch tune_gui
3. Select node from dropdown (e.g., `automated_planner`)
4. Edit parameter values in the left tree
5. Changes apply immediately to the running node

### Updating params.yaml

1. Launch tune_gui
2. Click "Load params.yaml" and select your file
3. Edit values in the right tree
4. Click "Save params.yaml" to write changes to disk
5. (Optional) Click "Apply YAML to Nodes" to push changes to running nodes

### Syncing YAML to Nodes

If you've manually edited `params.yaml` and want to apply it:

1. Load the YAML file
2. Click "Apply YAML to Nodes"
3. All matching parameters will be updated on running nodes

## Parameter Path Format

The GUI uses dot-notation for parameter paths:

```
node_name.ros__parameters.param_name
```

For example:
```
automated_planner.ros__parameters.finding_gate.scan_speed
```

The GUI automatically handles the `ros__parameters` prefix when communicating with nodes.

## Keyboard Shortcuts

- **Ctrl+O**: Load params.yaml
- **Ctrl+S**: Save params.yaml
- **F5**: Refresh node list

## Development

To add new parameter types: 
- Extend `ParameterItemDelegate` in `parameter_tree_widget.py`

## License

This project is licensed under the [GPLv3](https://www.gnu.org/licenses/gpl-3.0.en.html).