"""Interactive visual calibration tool for ACR scraper."""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import cv2
import numpy as np
import pytesseract
import json
from PIL import Image, ImageGrab, ImageTk, ImageDraw, ImageFont
from typing import Dict, Tuple, Optional, Any
import logging

logger = logging.getLogger(__name__)


class ACRInteractiveCalibrator:
    """Interactive visual calibration tool for ACR scraper regions."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("ACR Scraper Calibration Tool")
        self.root.geometry("1400x900")
        
        # Data storage
        self.screenshot = None
        self.calibrated_regions = {}
        self.current_region = None
        self.selection_start = None
        self.selection_rect = None
        
        # Colors for different regions
        self.region_colors = {
            'pot_area': '#FF0000',           # Red
            'hero_cards': '#00FF00',         # Green  
            'board_cards': '#0000FF',        # Blue
            'action_buttons': '#FFFF00',     # Yellow
            'stakes_info': '#FF00FF',        # Magenta
            'seat_1': '#00FFFF', 'seat_2': '#FFA500', 'seat_3': '#800080',
            'seat_4': '#FFC0CB', 'seat_5': '#A52A2A', 'seat_6': '#808080',
            'seat_7': '#000080', 'seat_8': '#008000'
        }
        
        # Region descriptions and importance
        self.regions_info = {
            'pot_area': {'desc': 'Pot Amount Display', 'priority': 'HIGH', 'example': 'Pot: $15.50'},
            'hero_cards': {'desc': 'Your Hole Cards', 'priority': 'HIGH', 'example': 'Ah Ks'},
            'board_cards': {'desc': 'Community Cards', 'priority': 'HIGH', 'example': '7h 2s 2d'},
            'action_buttons': {'desc': 'Fold/Call/Raise Buttons', 'priority': 'HIGH', 'example': 'Call $2.00'},
            'stakes_info': {'desc': 'Table Stakes/Blinds', 'priority': 'MEDIUM', 'example': '$0.01/$0.02'},
            'seat_1': {'desc': 'Player Seat 1', 'priority': 'MEDIUM', 'example': 'Player1 $100.00'},
            'seat_2': {'desc': 'Player Seat 2', 'priority': 'MEDIUM', 'example': 'Player2 $95.50'},
            'seat_3': {'desc': 'Player Seat 3', 'priority': 'MEDIUM', 'example': 'Player3 $200.00'},
            'seat_4': {'desc': 'Player Seat 4', 'priority': 'MEDIUM', 'example': 'Player4 $150.00'},
            'seat_5': {'desc': 'Player Seat 5', 'priority': 'MEDIUM', 'example': 'Player5 $75.00'},
            'seat_6': {'desc': 'Player Seat 6', 'priority': 'MEDIUM', 'example': 'Player6 $120.00'},
            'seat_7': {'desc': 'Player Seat 7', 'priority': 'LOW', 'example': 'Player7 $90.00'},
            'seat_8': {'desc': 'Player Seat 8', 'priority': 'LOW', 'example': 'Player8 $110.00'}
        }
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the user interface."""
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left panel for controls
        control_frame = ttk.Frame(main_frame, width=300)
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        control_frame.pack_propagate(False)
        
        # Right panel for image
        image_frame = ttk.Frame(main_frame)
        image_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.setup_controls(control_frame)
        self.setup_image_panel(image_frame)
    
    def setup_controls(self, parent):
        """Setup control panel."""
        # Title and instructions
        title_label = ttk.Label(parent, text="ACR Calibration Tool", font=('Arial', 14, 'bold'))
        title_label.pack(pady=(0, 10))
        
        instructions = tk.Text(parent, height=4, wrap=tk.WORD)
        instructions.pack(fill=tk.X, pady=(0, 10))
        instructions.insert(tk.END, 
            "1. Click 'Capture Screen' with ACR table visible\\n"
            "2. Click a region button below\\n"  
            "3. Click and drag on the image to select that region\\n"
            "4. Check OCR results and adjust if needed")
        instructions.config(state=tk.DISABLED)
        
        # Capture button
        capture_btn = ttk.Button(parent, text="📸 Capture Screen", command=self.capture_screen)
        capture_btn.pack(fill=tk.X, pady=(0, 10))
        
        # Progress info
        self.progress_label = ttk.Label(parent, text="No regions calibrated")
        self.progress_label.pack(pady=(0, 10))
        
        # Regions list
        regions_label = ttk.Label(parent, text="Select Region to Calibrate:", font=('Arial', 12, 'bold'))
        regions_label.pack(anchor=tk.W, pady=(10, 5))
        
        # Create scrollable frame for regions
        canvas = tk.Canvas(parent, height=400)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self.setup_region_buttons(scrollable_frame)
        
        # OCR Results
        ttk.Label(parent, text="OCR Results:", font=('Arial', 12, 'bold')).pack(anchor=tk.W, pady=(20, 5))
        
        self.ocr_text = tk.Text(parent, height=6, wrap=tk.WORD)
        self.ocr_text.pack(fill=tk.X, pady=(0, 10))
        
        # Action buttons
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(button_frame, text="Clear Region", command=self.clear_current_region).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Test OCR", command=self.test_current_ocr).pack(side=tk.LEFT, padx=(0, 5))
        
        # Save/Load buttons
        save_frame = ttk.Frame(parent)
        save_frame.pack(fill=tk.X, pady=(20, 0))
        
        ttk.Button(save_frame, text="💾 Save Calibration", command=self.save_calibration).pack(fill=tk.X, pady=(0, 5))
        ttk.Button(save_frame, text="📁 Load Calibration", command=self.load_calibration).pack(fill=tk.X)
    
    def setup_region_buttons(self, parent):
        """Setup region selection buttons."""
        self.region_buttons = {}
        
        for region_name, info in self.regions_info.items():
            # Create frame for each region
            region_frame = ttk.Frame(parent)
            region_frame.pack(fill=tk.X, pady=2)
            
            # Priority indicator color
            priority_color = {'HIGH': '#ff4444', 'MEDIUM': '#ffaa44', 'LOW': '#44ff44'}[info['priority']]
            
            # Region button
            btn_text = f"{info['desc']} ({info['priority']})"
            btn = ttk.Button(region_frame, text=btn_text, 
                           command=lambda r=region_name: self.select_region(r))
            btn.pack(fill=tk.X)
            
            # Status indicator
            status_frame = ttk.Frame(region_frame)
            status_frame.pack(fill=tk.X)
            
            status_label = ttk.Label(status_frame, text="❌ Not calibrated", foreground='red')
            status_label.pack(side=tk.LEFT)
            
            # Example text
            example_label = ttk.Label(status_frame, text=f"Ex: {info['example']}", foreground='gray', font=('Arial', 8))
            example_label.pack(side=tk.RIGHT)
            
            self.region_buttons[region_name] = {
                'button': btn,
                'status': status_label,
                'frame': region_frame
            }
    
    def setup_image_panel(self, parent):
        """Setup image display panel."""
        # Image canvas
        self.image_canvas = tk.Canvas(parent, bg='white', cursor='crosshair')
        self.image_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Bind mouse events for region selection
        self.image_canvas.bind("<Button-1>", self.start_selection)
        self.image_canvas.bind("<B1-Motion>", self.update_selection)
        self.image_canvas.bind("<ButtonRelease-1>", self.end_selection)
        
        # Status bar
        self.status_label = ttk.Label(parent, text="Click 'Capture Screen' to begin")
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)
    
    def capture_screen(self):
        """Capture the current screen."""
        try:
            # Hide window temporarily
            self.root.withdraw()
            self.root.after(500, self._do_capture)  # Small delay for window to hide
        except Exception as e:
            messagebox.showerror("Error", f"Failed to capture screen: {e}")
            self.root.deiconify()
    
    def _do_capture(self):
        """Actually capture the screen."""
        try:
            self.screenshot = ImageGrab.grab()
            self.display_screenshot()
            self.root.deiconify()  # Show window again
            self.status_label.config(text=f"Screen captured: {self.screenshot.size[0]}x{self.screenshot.size[1]}")
        except Exception as e:
            self.root.deiconify()
            messagebox.showerror("Error", f"Failed to capture screen: {e}")
    
    def display_screenshot(self):
        """Display the screenshot in the canvas."""
        if not self.screenshot:
            return
        
        # Calculate scaling to fit canvas
        canvas_width = self.image_canvas.winfo_width()
        canvas_height = self.image_canvas.winfo_height()
        
        if canvas_width <= 1 or canvas_height <= 1:
            self.root.after(100, self.display_screenshot)  # Try again after canvas is sized
            return
        
        img_width, img_height = self.screenshot.size
        scale_x = canvas_width / img_width
        scale_y = canvas_height / img_height
        self.scale = min(scale_x, scale_y, 1.0)  # Don't scale up, only down
        
        # Resize image
        new_width = int(img_width * self.scale)
        new_height = int(img_height * self.scale)
        
        display_img = self.screenshot.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Draw existing regions on the image
        self.draw_regions_on_image(display_img)
        
        # Convert to PhotoImage
        self.photo_image = ImageTk.PhotoImage(display_img)
        
        # Clear canvas and display image
        self.image_canvas.delete("all")
        self.image_canvas.create_image(0, 0, anchor=tk.NW, image=self.photo_image)
        
        # Update canvas scroll region
        self.image_canvas.configure(scrollregion=(0, 0, new_width, new_height))
    
    def draw_regions_on_image(self, img):
        """Draw existing calibrated regions on the image."""
        if not self.calibrated_regions:
            return
        
        draw = ImageDraw.Draw(img)
        
        try:
            font = ImageFont.truetype("arial.ttf", 12)
        except:
            font = ImageFont.load_default()
        
        for region_name, coords in self.calibrated_regions.items():
            if coords:
                x1, y1, x2, y2 = coords
                # Scale coordinates
                x1 = int(x1 * self.scale)
                y1 = int(y1 * self.scale)
                x2 = int(x2 * self.scale)
                y2 = int(y2 * self.scale)
                
                color = self.region_colors.get(region_name, '#FFFFFF')
                
                # Draw rectangle
                draw.rectangle([x1, y1, x2, y2], outline=color, width=2)
                
                # Draw label
                draw.text((x1, y1 - 15), region_name, fill=color, font=font)
    
    def select_region(self, region_name):
        """Select a region for calibration."""
        if not self.screenshot:
            messagebox.showwarning("Warning", "Please capture screen first!")
            return
        
        self.current_region = region_name
        self.status_label.config(text=f"Selected: {region_name} - Click and drag on image to define region")
        
        # Highlight selected button
        for name, btn_info in self.region_buttons.items():
            if name == region_name:
                btn_info['button'].config(style='Accent.TButton')
            else:
                btn_info['button'].config(style='TButton')
    
    def start_selection(self, event):
        """Start region selection."""
        if not self.current_region:
            messagebox.showinfo("Info", "Please select a region button first!")
            return
        
        self.selection_start = (event.x, event.y)
        
        # Clear any existing selection rectangle
        if self.selection_rect:
            self.image_canvas.delete(self.selection_rect)
    
    def update_selection(self, event):
        """Update selection rectangle."""
        if not self.selection_start:
            return
        
        # Clear previous rectangle
        if self.selection_rect:
            self.image_canvas.delete(self.selection_rect)
        
        # Draw new rectangle
        color = self.region_colors.get(self.current_region, '#FFFFFF')
        self.selection_rect = self.image_canvas.create_rectangle(
            self.selection_start[0], self.selection_start[1], 
            event.x, event.y, 
            outline=color, width=2
        )
    
    def end_selection(self, event):
        """End region selection and save coordinates."""
        if not self.selection_start or not self.current_region:
            return
        
        # Calculate actual coordinates (unscaled)
        x1 = min(self.selection_start[0], event.x) / self.scale
        y1 = min(self.selection_start[1], event.y) / self.scale
        x2 = max(self.selection_start[0], event.x) / self.scale
        y2 = max(self.selection_start[1], event.y) / self.scale
        
        # Save coordinates
        self.calibrated_regions[self.current_region] = (int(x1), int(y1), int(x2), int(y2))
        
        # Update button status
        self.region_buttons[self.current_region]['status'].config(
            text="✅ Calibrated", foreground='green'
        )
        
        # Test OCR immediately
        self.test_current_ocr()
        
        # Update progress
        calibrated_count = len([r for r in self.calibrated_regions.values() if r])
        total_count = len(self.regions_info)
        self.progress_label.config(text=f"Calibrated: {calibrated_count}/{total_count} regions")
        
        # Reset selection
        self.selection_start = None
        if self.selection_rect:
            self.image_canvas.delete(self.selection_rect)
            self.selection_rect = None
        
        self.status_label.config(text=f"Region '{self.current_region}' calibrated! Check OCR results below.")
    
    def test_current_ocr(self):
        """Test OCR on current region."""
        if not self.current_region or self.current_region not in self.calibrated_regions:
            return
        
        coords = self.calibrated_regions[self.current_region]
        if not coords:
            return
        
        try:
            # Extract region from screenshot
            x1, y1, x2, y2 = coords
            region_img = self.screenshot.crop((x1, y1, x2, y2))
            
            # Test different OCR methods
            results = self.test_ocr_methods(region_img)
            
            # Display results
            self.ocr_text.delete(1.0, tk.END)
            self.ocr_text.insert(tk.END, f"OCR Results for {self.current_region}:\\n")
            self.ocr_text.insert(tk.END, f"Region: {coords}\\n\\n")
            
            for method, text in results.items():
                self.ocr_text.insert(tk.END, f"{method}: '{text}'\\n")
            
            # Save region image for inspection
            region_img.save(f"region_{self.current_region}.png")
            
        except Exception as e:
            self.ocr_text.delete(1.0, tk.END)
            self.ocr_text.insert(tk.END, f"OCR Error: {e}")
    
    def test_ocr_methods(self, region_img):
        """Test different OCR preprocessing methods."""
        results = {}
        
        try:
            # Convert to OpenCV format
            cv_img = cv2.cvtColor(np.array(region_img), cv2.COLOR_RGB2BGR)
            gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
            
            # Raw OCR
            results['Raw'] = pytesseract.image_to_string(region_img).strip()
            
            # Threshold OCR
            _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
            binary_pil = Image.fromarray(binary)
            results['Threshold'] = pytesseract.image_to_string(binary_pil).strip()
            
            # Poker-optimized OCR
            poker_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz$.,/ '
            results['Poker Optimized'] = pytesseract.image_to_string(binary_pil, config=poker_config).strip()
            
        except Exception as e:
            results['Error'] = str(e)
        
        return results
    
    def clear_current_region(self):
        """Clear the current region calibration."""
        if not self.current_region:
            messagebox.showinfo("Info", "No region selected!")
            return
        
        if self.current_region in self.calibrated_regions:
            del self.calibrated_regions[self.current_region]
        
        # Update button status
        self.region_buttons[self.current_region]['status'].config(
            text="❌ Not calibrated", foreground='red'
        )
        
        # Update progress
        calibrated_count = len([r for r in self.calibrated_regions.values() if r])
        total_count = len(self.regions_info)
        self.progress_label.config(text=f"Calibrated: {calibrated_count}/{total_count} regions")
        
        # Refresh display
        self.display_screenshot()
        
        self.status_label.config(text=f"Cleared region '{self.current_region}'")
    
    def save_calibration(self):
        """Save calibration to file."""
        if not self.calibrated_regions:
            messagebox.showwarning("Warning", "No calibration data to save!")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialvalue="acr_calibrated_regions.json"
        )
        
        if filename:
            try:
                with open(filename, 'w') as f:
                    json.dump(self.calibrated_regions, f, indent=2)
                
                messagebox.showinfo("Success", f"Calibration saved to {filename}")
                
                # Also save a visual overlay
                if self.screenshot:
                    overlay_img = self.screenshot.copy()
                    self.draw_regions_on_original(overlay_img)
                    overlay_filename = filename.replace('.json', '_overlay.png')
                    overlay_img.save(overlay_filename)
                    
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save: {e}")
    
    def draw_regions_on_original(self, img):
        """Draw regions on original full-size image."""
        draw = ImageDraw.Draw(img)
        
        try:
            font = ImageFont.truetype("arial.ttf", 16)
        except:
            font = ImageFont.load_default()
        
        for region_name, coords in self.calibrated_regions.items():
            if coords:
                x1, y1, x2, y2 = coords
                color = self.region_colors.get(region_name, '#FFFFFF')
                
                # Draw rectangle
                draw.rectangle([x1, y1, x2, y2], outline=color, width=3)
                
                # Draw label with background
                draw.rectangle([x1, y1 - 25, x1 + len(region_name) * 10, y1], fill=color)
                draw.text((x1 + 2, y1 - 23), region_name, fill='black', font=font)
    
    def load_calibration(self):
        """Load calibration from file."""
        filename = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'r') as f:
                    self.calibrated_regions = json.load(f)
                
                # Update button statuses
                for region_name in self.regions_info.keys():
                    if region_name in self.calibrated_regions and self.calibrated_regions[region_name]:
                        self.region_buttons[region_name]['status'].config(
                            text="✅ Calibrated", foreground='green'
                        )
                    else:
                        self.region_buttons[region_name]['status'].config(
                            text="❌ Not calibrated", foreground='red'
                        )
                
                # Update progress
                calibrated_count = len([r for r in self.calibrated_regions.values() if r])
                total_count = len(self.regions_info)
                self.progress_label.config(text=f"Calibrated: {calibrated_count}/{total_count} regions")
                
                # Refresh display
                if self.screenshot:
                    self.display_screenshot()
                
                messagebox.showinfo("Success", f"Calibration loaded from {filename}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load: {e}")
    
    def run(self):
        """Run the calibration tool."""
        self.root.mainloop()


def main():
    """Run the interactive calibration tool."""
    print("Starting ACR Interactive Calibration Tool...")
    
    calibrator = ACRInteractiveCalibrator()
    calibrator.run()


if __name__ == "__main__":
    main()