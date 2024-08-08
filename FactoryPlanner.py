# FactoryPlanner.py

import tkinter as tk
from tkinter import ttk
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
        self.connections = []

        self.bind("<KeyPress-c>", self.connect_snapping_points)
        self.bind("<KeyPress-Delete>", self.delete_selected_building)
        self.bind("<KeyPress-BackSpace>", self.delete_selected_building)

        # Panning
        self.panning_enabled = False
        self.bind("<KeyPress-space>", self.enable_panning)
        self.bind("<KeyRelease-space>", self.disable_panning)

        # Canvas dragging
        self.canvas.bind("<ButtonPress-3>", self.start_pan)  # Use right mouse button for panning
        self.canvas.bind("<B3-Motion>", self.pan_canvas)  # Use right mouse button for panning
        self.canvas.bind("<ButtonRelease-3>", self.stop_panning)

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
            deselect_all_callback=self.deselect_all_buildings
        )
        self.buildings.append(building)
        print(f"Spawned {building_name}")

    def deselect_all_buildings(self):
        # Deselect all buildings
        for building in self.buildings:
            building.deselect()

    def delete_selected_building(self, event):
        # Find and delete the selected building
        for building in self.buildings:
            if building.is_selected():
                self.canvas.delete(building.rect)
                self.canvas.delete(building.label)
                for point, _ in building.snapping_points:
                    self.canvas.delete(point)
                self.buildings.remove(building)
                print(f"Deleted {building.name}")
                break  # Exit after deleting the first selected building

    def connect_snapping_points(self, event):
        if len(self.buildings) < 2:
            return

        # Example connection between the first snapping points of two buildings
        start_point = self.buildings[0].snapping_points[0][0]  # Get the actual point item
        end_point = self.buildings[1].snapping_points[0][0]  # Get the actual point item
        x0, y0, _, _ = self.canvas.coords(start_point)
        x1, y1, _, _ = self.canvas.coords(end_point)

        # Draw line between two snapping points
        connection = self.canvas.create_line(x0, y0, x1, y1, fill="green")
        self.connections.append(connection)

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
