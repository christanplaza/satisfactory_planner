# classes/Building.py

import tkinter as tk

class Building:
    def __init__(self, canvas, x, y, name, config, grid_size, deselect_all_callback):
        self.canvas = canvas
        self.name = name
        self.width = config["width"]
        self.height = config["height"]
        self.connectors = config["connectors"]
        self.grid_size = grid_size
        self.deselect_all_callback = deselect_all_callback  # Callback to deselect other buildings

        # Create the building rectangle
        self.rect = self.canvas.create_rectangle(x, y, x + self.width, y + self.height, fill="blue")

        # Create the label for the building
        self.label = self.canvas.create_text(x + self.width / 2, y + self.height / 2, text=name, fill="white")

        # Create snapping points based on connectors
        self.snapping_points = self.create_snapping_points()

        # Selection state
        self.selected = False

        # Bind events for dragging and selection
        self.canvas.tag_bind(self.rect, "<ButtonPress-1>", self.on_press)
        self.canvas.tag_bind(self.rect, "<B1-Motion>", self.on_drag)
        self.canvas.tag_bind(self.rect, "<ButtonRelease-1>", self.on_release)

        # Bind label dragging to rectangle dragging
        self.canvas.tag_bind(self.label, "<ButtonPress-1>", self.on_press)
        self.canvas.tag_bind(self.label, "<B1-Motion>", self.on_drag)
        self.canvas.tag_bind(self.label, "<ButtonRelease-1>", self.on_release)

        self.drag_data = {"x": 0, "y": 0}

    def create_snapping_points(self):
        snap_positions = []

        for direction, points in self.connectors.items():
            if direction == "north":
                for i in range(points["input"]):
                    x_pos = (i + 1) * self.width / (points["input"] + 1)
                    snap_positions.append((x_pos, 0, "input"))
                for i in range(points["output"]):
                    x_pos = (i + 1) * self.width / (points["output"] + 1)
                    snap_positions.append((x_pos, 0, "output"))

            elif direction == "east":
                for i in range(points["input"]):
                    y_pos = (i + 1) * self.height / (points["input"] + 1)
                    snap_positions.append((self.width, y_pos, "input"))
                for i in range(points["output"]):
                    y_pos = (i + 1) * self.height / (points["output"] + 1)
                    snap_positions.append((self.width, y_pos, "output"))

            elif direction == "south":
                for i in range(points["input"]):
                    x_pos = (i + 1) * self.width / (points["input"] + 1)
                    snap_positions.append((x_pos, self.height, "input"))
                for i in range(points["output"]):
                    x_pos = (i + 1) * self.width / (points["output"] + 1)
                    snap_positions.append((x_pos, self.height, "output"))

            elif direction == "west":
                for i in range(points["input"]):
                    y_pos = (i + 1) * self.height / (points["input"] + 1)
                    snap_positions.append((0, y_pos, "input"))
                for i in range(points["output"]):
                    y_pos = (i + 1) * self.height / (points["output"] + 1)
                    snap_positions.append((0, y_pos, "output"))

        # Create the snapping points
        points = []
        for cx, cy, point_type in snap_positions:
            snap_x = self.canvas.coords(self.rect)[0] + cx
            snap_y = self.canvas.coords(self.rect)[1] + cy
            color = "green" if point_type == "input" else "red"
            point = self.canvas.create_oval(
                snap_x - 3, snap_y - 3, snap_x + 3, snap_y + 3, fill=color
            )
            points.append((point, point_type))

        return points

    def on_press(self, event):
        # Toggle selection
        if self.is_selected():
            self.deselect()
        else:
            self.deselect_all_callback()
            self.select()

        self.drag_data["x"] = event.x
        self.drag_data["y"] = event.y

    def on_drag(self, event):
        # Calculate the delta
        delta_x = event.x - self.drag_data["x"]
        delta_y = event.y - self.drag_data["y"]

        # Move the rectangle, label, and snapping points
        self.canvas.move(self.rect, delta_x, delta_y)
        self.canvas.move(self.label, delta_x, delta_y)
        for point, _ in self.snapping_points:
            self.canvas.move(point, delta_x, delta_y)

        # Update the drag data
        self.drag_data["x"] = event.x
        self.drag_data["y"] = event.y

    def on_release(self, event):
        # Snap to grid logic for the building's center
        x0, y0, x1, y1 = self.canvas.coords(self.rect)
        center_x = (x0 + x1) / 2
        center_y = (y0 + y1) / 2
        new_center_x = round(center_x / self.grid_size) * self.grid_size
        new_center_y = round(center_y / self.grid_size) * self.grid_size
        offset_x = new_center_x - center_x
        offset_y = new_center_y - center_y

        # Move the building, label, and its points to the snapped position
        self.canvas.move(self.rect, offset_x, offset_y)
        self.canvas.move(self.label, offset_x, offset_y)
        for point, _ in self.snapping_points:
            self.canvas.move(point, offset_x, offset_y)

    def select(self):
        # Highlight the building to show selection
        self.selected = True
        self.canvas.itemconfig(self.rect, outline="yellow", width=2)

    def deselect(self):
        # Remove highlight from the building
        self.selected = False
        self.canvas.itemconfig(self.rect, outline="", width=1)

    def is_selected(self):
        return self.selected
