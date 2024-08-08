import tkinter as tk
from tkinter import ttk

class ResourceSelectionDialog(tk.Toplevel):
    def __init__(self, parent, resources, on_select_callback):
        super().__init__(parent)
        self.title("Select Resource and Purity")
        self.geometry("300x200")
        
        self.resources = resources
        self.on_select_callback = on_select_callback

        # Resource dropdown
        tk.Label(self, text="Resource:").pack(pady=5)
        self.resource_var = tk.StringVar()
        resource_names = list(self.resources.keys())
        self.resource_dropdown = ttk.Combobox(self, textvariable=self.resource_var, values=resource_names)
        self.resource_dropdown.pack(pady=5)

        # Purity dropdown
        tk.Label(self, text="Purity:").pack(pady=5)
        self.purity_var = tk.StringVar()
        purity_levels = ["Impure", "Normal", "Pure"]
        self.purity_dropdown = ttk.Combobox(self, textvariable=self.purity_var, values=purity_levels)
        self.purity_dropdown.pack(pady=5)

        # Submit button
        submit_button = tk.Button(self, text="Submit", command=self.submit_selection)
        submit_button.pack(pady=20)

    def submit_selection(self):
        resource = self.resource_var.get()
        purity = self.purity_var.get()
        self.on_select_callback(resource, purity)
        self.destroy()
