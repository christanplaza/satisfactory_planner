# FactoryPlanner.py

import tkinter as tk
from tkinter import ttk
import tkinter.font as TKFont
import json
from classes.Building import Building

class FactoryPlanner(tk.Tk):
    grid_size = 9

    def __init__(self):
        super().__init__()
        self.title("Factory Planner")
        self.geometry("800x600")

        # Canvas with scroll region for panning
        self.canvas = tk.Canvas(self, width=600, height=400, bg="white", scrollregion=(-2000, -2000, 2000, 2000))
        self.canvas.pack(side=tk.RIGHT, padx=10, pady=20, expand=True, fill=tk.BOTH)


        self.helv36 = TKFont.Font(family='Helvetica', size=12, weight='bold')

        # Scrollbars
        h_scrollbar = tk.Scrollbar(self, orient=tk.HORIZONTAL, command=self.canvas.xview)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        v_scrollbar = tk.Scrollbar(self, orient=tk.VERTICAL, command=self.canvas.yview)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.canvas.config(xscrollcommand=h_scrollbar.set, yscrollcommand=v_scrollbar.set)

        # Load building types from JSON file
        with open('building_types.json', 'r') as f:
            self.building_types = json.load(f)["buildings"]

        # Frame for collapsible list
        self.control_frame = tk.Frame(self)
        self.control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

        self.create_collapsible_buttons()

        self.buildings = []
        self.connections = []  # Store connections as tuples (start_node, end_node, line_id, label_id)
        self.connected_nodes = set()  # Track nodes that are connected
        self.selected_connection = None  # Track the selected connection

        self.bind("<KeyPress-c>", self.connect_snapping_points)
        self.bind("<KeyPress-Delete>", self.delete_selected)
        self.bind("<KeyPress-BackSpace>", self.delete_selected)

        # Panning
        self.panning_enabled = False
        self.bind("<KeyPress-space>", self.enable_panning)
        self.bind("<KeyRelease-space>", self.disable_panning)

        # Canvas dragging
        self.canvas.bind("<ButtonPress-3>", self.start_pan)  # Use right mouse button for panning
        self.canvas.bind("<B3-Motion>", self.pan_canvas)  # Use right mouse button for panning
        self.canvas.bind("<ButtonRelease-3>", self.stop_panning)

        # Node selection
        self.selected_node = None

    def create_collapsible_buttons(self):
        for category, buildings in self.building_types.items():
            # Create a frame for each category
            category_frame = ttk.LabelFrame(self.control_frame, text=category)
            category_frame.pack(fill=tk.X, pady=5)

            # Add buttons for each building
            for building_name, config in buildings.items():
                button = tk.Button(category_frame, text=building_name, command=lambda name=building_name, cfg=config: self.spawn_building(name, cfg))
                button.pack(fill=tk.X, padx=5, pady=2)

    def spawn_building(self, building_name, config):
        # Pass grid_size to Building class and a callback to deselect others
        building = Building(
            self.canvas, 
            x=100, 
            y=100, 
            name=building_name, 
            config=config, 
            grid_size=self.grid_size, 
            deselect_all_callback=self.deselect_all,
            node_select_callback=self.on_node_selected,
            update_connections_callback=self.update_connections
        )
        self.buildings.append(building)
        print(f"Spawned {building_name}")

    def deselect_all(self):
        # Deselect all buildings and connections
        self.deselect_all_buildings()
        self.deselect_all_connections()

    def deselect_all_buildings(self):
        # Deselect all buildings
        for building in self.buildings:
            building.deselect()

    def deselect_all_connections(self):
        # Deselect all connections
        if self.selected_connection is not None:
            line_id, label_id = self.selected_connection
            self.canvas.itemconfig(line_id, fill="gray", width=4)
            self.selected_connection = None

    def delete_selected(self, event):
        # Delete selected building or connection
        if self.selected_connection is not None:
            self.delete_selected_connection()
        else:
            self.delete_selected_building()

    def delete_selected_building(self):
        # Find and delete the selected building
        for building in self.buildings:
            if building.is_selected():
                self.canvas.delete(building.rect)
                self.canvas.delete(building.label)
                for point, _ in building.snapping_points:
                    self.canvas.delete(point)

                # Remove connections related to this building
                connections_to_remove = []
                for start_node, end_node, line_id, label_id in self.connections:
                    if start_node in [point for point, _ in building.snapping_points] or end_node in [point for point, _ in building.snapping_points]:
                        self.canvas.delete(line_id)
                        self.canvas.delete(label_id)
                        self.connected_nodes.discard(start_node)
                        self.connected_nodes.discard(end_node)
                        connections_to_remove.append((start_node, end_node, line_id, label_id))

                # Update connections
                for connection in connections_to_remove:
                    self.connections.remove(connection)

                self.buildings.remove(building)
                print(f"Deleted {building.name}")
                break  # Exit after deleting the first selected building

    def delete_selected_connection(self):
        # Delete the selected connection
        if self.selected_connection is not None:
            line_id, label_id = self.selected_connection
            for start_node, end_node, connection_line_id, connection_label_id in self.connections:
                if connection_line_id == line_id:
                    self.canvas.delete(connection_line_id)
                    self.canvas.delete(connection_label_id)
                    self.connected_nodes.discard(start_node)
                    self.connected_nodes.discard(end_node)
                    self.connections.remove((start_node, end_node, connection_line_id, connection_label_id))
                    print("Deleted connection")
                    break

    def on_node_selected(self, building, node, node_type):
        if node in self.connected_nodes:
            print("Node already connected.")
            return

        self.deselect_all()  # Ensure only one selection at a time

        if self.selected_node is None:
            # First node selection
            self.selected_node = (building, node, node_type)
            self.canvas.itemconfig(node, outline="blue", width=2)  # Highlight selected node
        else:
            # Second node selection, attempt to connect
            other_building, other_node, other_type = self.selected_node

            if node_type != other_type and building != other_building:
                if node not in self.connected_nodes and other_node not in self.connected_nodes:
                    self.create_connection(other_node, node)

            # Reset selection
            self.canvas.itemconfig(other_node, outline="", width=1)
            self.selected_node = None

    def create_connection(self, start_node, end_node, capacity=60):
        x0, y0, _, _ = self.canvas.coords(start_node)
        x1, y1, _, _ = self.canvas.coords(end_node)

        # Draw line between two snapping points with increased thickness
        connection_line = self.canvas.create_line(x0, y0, x1, y1, fill="gray", width=4)

        # Create a label for the capacity
        mid_x, mid_y = (x0 + x1) / 2, (y0 + y1) / 2
        capacity_label = self.canvas.create_text(mid_x, mid_y, text=f"0/{capacity}", fill="black", font=self.helv36)

        self.connections.append((start_node, end_node, connection_line, capacity_label))

        # Bind events for selecting the connection
        self.canvas.tag_bind(connection_line, "<ButtonPress-1>", self.on_connection_click)

        # Mark nodes as connected
        self.connected_nodes.add(start_node)
        self.connected_nodes.add(end_node)

        print("Connection created")

    def on_connection_click(self, event):
        # Select a connection line
        self.deselect_all()  # Ensure only one selection at a time
        line_id = self.canvas.find_withtag("current")[0]
        # Find the corresponding label
        label_id = next((label for _, _, line, label in self.connections if line == line_id), None)
        self.selected_connection = (line_id, label_id)
        self.canvas.itemconfig(line_id, fill="yellow", width=4)  # Highlight selected connection
        print("Connection selected")

    def update_connections(self, building):
        # Update connections for a given building
        valid_connections = []
        for start_node, end_node, line_id, label_id in self.connections:
            # Check if nodes are still valid
            if self.canvas.coords(start_node) and self.canvas.coords(end_node):
                x0, y0, _, _ = self.canvas.coords(start_node)
                x1, y1, _, _ = self.canvas.coords(end_node)
                self.canvas.coords(line_id, x0, y0, x1, y1)
                
                # Update the label position
                mid_x, mid_y = (x0 + x1) / 2, (y0 + y1) / 2
                self.canvas.coords(label_id, mid_x, mid_y)
                
                valid_connections.append((start_node, end_node, line_id, label_id))
            else:
                # Remove connection if any node is invalid
                self.canvas.delete(line_id)
                self.canvas.delete(label_id)
                self.connected_nodes.discard(start_node)
                self.connected_nodes.discard(end_node)
        
        # Update the list of valid connections
        self.connections = valid_connections

    def connect_snapping_points(self, event):
        if len(self.buildings) < 2:
            return

        # Attempt to connect compatible nodes
        for building in self.buildings:
            for point, point_type in building.snapping_points:
                if point_type == "output" and point not in self.connected_nodes:
                    # Find an input node from another building to connect
                    for other_building in self.buildings:
                        if other_building != building:
                            for other_point, other_point_type in other_building.snapping_points:
                                if other_point_type == "input" and other_point not in self.connected_nodes:
                                    self.create_connection(point, other_point)
                                    return  # Exit after making a connection

    def enable_panning(self, event):
        self.panning_enabled = True

    def disable_panning(self, event):
        self.panning_enabled = False

    def start_pan(self, event):
        if self.panning_enabled:
            self.canvas.scan_mark(event.x, event.y)

    def pan_canvas(self, event):
        if self.panning_enabled:
            self.canvas.scan_dragto(event.x, event.y, gain=1)

    def stop_panning(self, event):
        pass  # No action needed here
