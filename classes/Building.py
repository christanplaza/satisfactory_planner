# Building.py
import textwrap

class Building:
    def __init__(self, canvas, x, y, name, config, grid_size, deselect_all_callback, node_select_callback, update_connections_callback, on_click_callback=None):
        self.canvas = canvas
        self.name = name
        self.width = config["width"]
        self.height = config["height"]
        self.connectors = config["connectors"]
        self.deselect_all_callback = deselect_all_callback
        self.node_select_callback = node_select_callback
        self.update_connections_callback = update_connections_callback
        self.on_click_callback = on_click_callback
        self.grid_size = grid_size

        # Create the building rectangle
        self.rect = self.canvas.create_rectangle(x, y, x + self.width, y + self.height, fill="blue")

        # Create the label for the building
        self.label = self.canvas.create_text(x + self.width / 2, y + self.height / 2, text=name, fill="white", width=self.width)

        # Create snapping points based on connectors
        self.snapping_points = self.create_snapping_points()

        # Bind events for dragging
        self.canvas.tag_bind(self.rect, "<ButtonPress-1>", self.on_press)
        self.canvas.tag_bind(self.rect, "<B1-Motion>", self.on_drag)
        self.canvas.tag_bind(self.rect, "<ButtonRelease-1>", self.on_release)

        # Bind label dragging to rectangle dragging
        self.canvas.tag_bind(self.label, "<ButtonPress-1>", self.on_press)
        self.canvas.tag_bind(self.label, "<B1-Motion>", self.on_drag)
        self.canvas.tag_bind(self.label, "<ButtonRelease-1>", self.on_release)

        # Bind on-click callback if provided
        if self.on_click_callback:
            self.canvas.tag_bind(self.rect, "<Double-Button-1>", self.on_double_click)
            self.canvas.tag_bind(self.label, "<Double-Button-1>", self.on_double_click)

        self.drag_data = {"x": 0, "y": 0}
        self.selected = False

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

            # Bind event for node selection
            self.canvas.tag_bind(point, "<ButtonPress-1>", lambda event, node=point, ntype=point_type: self.node_select_callback(self, node, ntype))
            points.append((point, point_type))

        return points

    def on_press(self, event):
        self.deselect_all_callback()  # Deselect other buildings and connections
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

        # Update connections
        self.update_connections_callback(self)

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

        # Update connections
        self.update_connections_callback(self)

    def on_double_click(self, event):
        if self.on_click_callback:
            self.on_click_callback(self)

    def select(self):
        self.selected = True
        self.canvas.itemconfig(self.rect, outline="blue", width=2)

    def deselect(self):
        self.selected = False
        self.canvas.itemconfig(self.rect, outline="", width=1)

    def is_selected(self):
        return self.selected

    def update_output_label(self, text):
        # Calculate the maximum width in characters based on the building width
        char_width = int(self.width // 8)  # Roughly 8 pixels per character

        # Wrap the text to fit within the building width
        wrapped_text = textwrap.fill(text, width=char_width)

        # Update the label text to show resource and purity
        self.canvas.itemconfig(self.label, text=wrapped_text)
