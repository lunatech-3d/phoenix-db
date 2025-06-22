import tkinter as tk

#Local Imports
from app.map_viewer import MapViewer

class MapViewerApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.geometry("0x0+0+0")  # Make root window tiny
        self.root.withdraw()  # Hide the root window
        
        self.viewer = MapViewer(self.root)
        # Make viewer dialog the main window
        self.viewer.dialog.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def on_closing(self):
        self.root.quit()
        self.root.destroy()
        
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = MapViewerApp()
    app.run()