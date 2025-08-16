#!/usr/bin/env python3
"""
Visual ACR Poker Scraper Calibration Tool
Click and drag to select regions instead of entering coordinates manually.

Requirements:
- pip install pillow opencv-python pytesseract tkinter
- Install Tesseract OCR: https://github.com/tesseract-ocr/tesseract

Usage:
1. Open ACR poker client and join a table
2. Run: python acr_visual_calibrator.py
3. Click "Capture Screen" button
4. Click region buttons, then click-and-drag on the image to select areas
"""

import tkinter as tk
from tkinter import ttk, messagebox
import cv2
import numpy as np
import pytesseract
import json
import time
from PIL import Image, ImageGrab, ImageTk, ImageDraw, ImageFont
from typing import Dict, Tuple, Any, Optional

class VisualACRCalibrator:
    """Visual calibration tool with click-and-drag region selection."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("ACR Visual Calibration Tool")
        self.root.geometry("1200x800")
        
        # Data
        self.screenshot = None
        self.calibrated_regions = {}
        self.current_region = None
        self.selection_start = None
        self.selection_rect = None
        self.scale = 1.0
        
        # Colors for different regions
        self.region_colors = {
            'pot_area': '#FF0000',
            'hero_cards': '#00FF00',
            'board_cards': '#0000FF', 
            'action_buttons': '#FFFF00',
            'stakes_info': '#FF00FF'
        }
        
        # Region info
        self.regions_info = {
            'pot_area': {
                'desc': 'Main Pot Amount',
                'example': 'Pot: $47.50',
                'priority': 'HIGH'
            },
            'hero_cards': {
                'desc': 'Your Hole Cards', 
                'example': 'Ah Ks',
                'priority': 'HIGH'
            },
            'board_cards': {
                'desc': 'Community Cards',
                'example': '7h 2s 2d',
                'priority': 'HIGH'
            },
            'action_buttons': {
                'desc': 'Action Buttons',
                'example': 'Call $5.00',
                'priority': 'HIGH'
            },
            'stakes_info': {
                'desc': 'Table Stakes',
                'example': '$0.01/$0.02',
                'priority': 'MEDIUM'
            }
        }
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the user interface."""
        # Main layout
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
        # Title
        title = ttk.Label(parent, text="ACR Visual Calibrator", font=('Arial', 14, 'bold'))
        title.pack(pady=(0, 10))
        
        # Instructions
        instructions = tk.Text(parent, height=6, wrap=tk.WORD, bg='#f0f0f0')
        instructions.pack(fill=tk.X, pady=(0, 10))
        instructions.insert(tk.END, 
            "INSTRUCTIONS:\n"
            "1. Click 'Capture ACR Screen' with poker table visible\n"
            "2. Click a region button below\n"
            "3. Click and DRAG on the image to select that area\n"
            "4. Check OCR results\n"
            "5. Repeat for all regions")
        instructions.config(state=tk.DISABLED)
        
        # Capture button
        capture_btn = ttk.Button(parent, text="📸 Capture ACR Screen", 
                               command=self.capture_acr_screen)
        capture_btn.pack(fill=tk.X, pady=(0, 10))
        
        # Progress
        self.progress_label = ttk.Label(parent, text="No regions calibrated yet")
        self.progress_label.pack(pady=(0, 10))
        
        # Region selection
        ttk.Label(parent, text="Select Region to Calibrate:", 
                 font=('Arial', 12, 'bold')).pack(anchor=tk.W, pady=(10, 5))
        
        # Region buttons
        self.region_buttons = {}
        for region_name, info in self.regions_info.items():
            self.create_region_button(parent, region_name, info)
        
        # OCR Results
        ttk.Label(parent, text="OCR Results:", 
                 font=('Arial', 12, 'bold')).pack(anchor=tk.W, pady=(20, 5))
        
        self.ocr_text = tk.Text(parent, height=8, wrap=tk.WORD)
        self.ocr_text.pack(fill=tk.X, pady=(0, 10))
        
        # Action buttons
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(button_frame, text="Test OCR", 
                  command=self.test_current_ocr).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Clear Region", 
                  command=self.clear_current_region).pack(side=tk.LEFT)
        
        # Save button
        ttk.Button(parent, text="💾 Save Calibration", 
                  command=self.save_calibration).pack(fill=tk.X, pady=(20, 0))
        
    def create_region_button(self, parent, region_name, info):
        """Create a region selection button."""
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, pady=2)
        
        # Button text with priority
        btn_text = f"{info['desc']} ({info['priority']})"
        
        # Button
        btn = ttk.Button(frame, text=btn_text,
                        command=lambda: self.select_region(region_name))
        btn.pack(fill=tk.X)
        
        # Status and example
        status_frame = ttk.Frame(frame)
        status_frame.pack(fill=tk.X)
        
        status_label = ttk.Label(status_frame, text="❌ Not calibrated", 
                               foreground='red', font=('Arial', 8))
        status_label.pack(side=tk.LEFT)
        
        example_label = ttk.Label(status_frame, text=f"Ex: {info['example']}", 
                                foreground='gray', font=('Arial', 8))
        example_label.pack(side=tk.RIGHT)
        
        self.region_buttons[region_name] = {
            'button': btn,
            'status': status_label,
            'frame': frame
        }
        
    def setup_image_panel(self, parent):
        """Setup image display panel."""
        # Image canvas with scrollbars
        canvas_frame = ttk.Frame(parent)
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        self.image_canvas = tk.Canvas(canvas_frame, bg='white', cursor='crosshair')
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.image_canvas.yview)
        h_scrollbar = ttk.Scrollbar(canvas_frame, orient="horizontal", command=self.image_canvas.xview)
        self.image_canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Pack scrollbars and canvas
        v_scrollbar.pack(side="right", fill="y")
        h_scrollbar.pack(side="bottom", fill="x")
        self.image_canvas.pack(side="left", fill="both", expand=True)
        
        # Mouse events for region selection
        self.image_canvas.bind("<Button-1>", self.start_selection)
        self.image_canvas.bind("<B1-Motion>", self.update_selection) 
        self.image_canvas.bind("<ButtonRelease-1>", self.end_selection)
        
        # Status bar
        self.status_label = ttk.Label(parent, text="Click 'Capture ACR Screen' to begin")
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)
        
    def capture_acr_screen(self):
        """Capture ACR screen after countdown."""
        self.status_label.config(text="Preparing to capture...")
        self.root.withdraw()  # Hide window
        
        # Countdown in separate window
        countdown_window = tk.Toplevel()
        countdown_window.title("Capturing Screen")
        countdown_window.geometry("300x100")
        countdown_window.attributes('-topmost', True)
        
        countdown_label = ttk.Label(countdown_window, text="Make ACR table visible...", 
                                  font=('Arial', 12))
        countdown_label.pack(expand=True)
        
        for i in range(3, 0, -1):
            countdown_label.config(text=f"Capturing in {i}...")
            countdown_window.update()
            time.sleep(1)
        
        countdown_window.destroy()
        
        # Capture screen
        try:
            self.screenshot = ImageGrab.grab()
            self.screenshot.save("acr_screenshot.png")
            self.display_screenshot()
            self.status_label.config(text=f"Screenshot captured: {self.screenshot.size[0]}x{self.screenshot.size[1]}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to capture screen: {e}")
        
        self.root.deiconify()  # Show window again
        
    def display_screenshot(self):
        """Display screenshot in canvas with scaling."""
        if not self.screenshot:
            return
            
        # Calculate scaling to fit canvas
        canvas_width = self.image_canvas.winfo_width()
        canvas_height = self.image_canvas.winfo_height()
        
        if canvas_width <= 1 or canvas_height <= 1:
            self.root.after(100, self.display_screenshot)
            return
            
        img_width, img_height = self.screenshot.size
        scale_x = canvas_width / img_width
        scale_y = canvas_height / img_height
        self.scale = min(scale_x, scale_y, 1.0)  # Don't scale up
        
        # Resize image
        new_width = int(img_width * self.scale)
        new_height = int(img_height * self.scale)
        
        display_img = self.screenshot.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Draw existing regions
        self.draw_regions_on_image(display_img)
        
        # Display image
        self.photo_image = ImageTk.PhotoImage(display_img)
        self.image_canvas.delete("all")
        self.image_canvas.create_image(0, 0, anchor=tk.NW, image=self.photo_image)
        self.image_canvas.configure(scrollregion=(0, 0, new_width, new_height))
        
    def draw_regions_on_image(self, img):
        """Draw calibrated regions on the image."""
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
                
                # Draw rectangle and label
                draw.rectangle([x1, y1, x2, y2], outline=color, width=2)
                draw.text((x1, y1 - 15), region_name, fill=color, font=font)
                
    def select_region(self, region_name):
        """Select a region for calibration."""
        if not self.screenshot:
            messagebox.showwarning("Warning", "Please capture screen first!")
            return
            
        self.current_region = region_name
        self.status_label.config(text=f"Selected: {region_name} - Click and drag on image to select area")
        
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
        
        # Clear existing selection
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
            
        self.status_label.config(text=f"Region '{self.current_region}' calibrated! Check OCR results.")
        
    def test_current_ocr(self):
        """Test OCR on current region."""
        if not self.current_region or self.current_region not in self.calibrated_regions:
            return
            
        coords = self.calibrated_regions[self.current_region]
        if not coords:
            return
            
        try:
            # Extract region
            x1, y1, x2, y2 = coords
            region_img = self.screenshot.crop((x1, y1, x2, y2))
            
            # Test OCR methods
            results = self.test_ocr_methods(region_img)
            
            # Display results
            self.ocr_text.delete(1.0, tk.END)
            self.ocr_text.insert(tk.END, f"🔍 OCR Results for {self.current_region}:\n")
            self.ocr_text.insert(tk.END, f"📐 Region: {coords}\n\n")
            
            best_result = ""
            for method, text in results.items():
                status = "✅" if text and len(text.strip()) > 0 else "❌"
                self.ocr_text.insert(tk.END, f"{status} {method}: '{text}'\n")
                if text and len(text.strip()) > len(best_result):
                    best_result = text.strip()
                    
            if best_result:
                self.ocr_text.insert(tk.END, f"\n🎯 Best: '{best_result}'\n")
            else:
                self.ocr_text.insert(tk.END, "\n❌ No readable text found\n")
                
            # Save region image
            region_img.save(f"acr_region_{self.current_region}.png")
            
        except Exception as e:
            self.ocr_text.delete(1.0, tk.END)
            self.ocr_text.insert(tk.END, f"❌ OCR Error: {e}")
            
    def test_ocr_methods(self, region_img):
        """Test different OCR methods."""
        results = {}
        
        try:
            cv_img = cv2.cvtColor(np.array(region_img), cv2.COLOR_RGB2BGR)
            gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
            
            # Raw OCR
            results['Raw'] = pytesseract.image_to_string(region_img).strip()
            
            # Binary threshold
            _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
            binary_pil = Image.fromarray(binary)
            results['Binary'] = pytesseract.image_to_string(binary_pil).strip()
            
            # Poker optimized
            poker_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz$.,/ '
            results['Poker'] = pytesseract.image_to_string(binary_pil, config=poker_config).strip()
            
        except Exception as e:
            results['Error'] = str(e)
            
        return results
        
    def clear_current_region(self):
        """Clear current region calibration."""
        if not self.current_region:
            messagebox.showinfo("Info", "No region selected!")
            return
            
        if self.current_region in self.calibrated_regions:
            del self.calibrated_regions[self.current_region]
            
        self.region_buttons[self.current_region]['status'].config(
            text="❌ Not calibrated", foreground='red'
        )
        
        # Update progress and display
        calibrated_count = len([r for r in self.calibrated_regions.values() if r])
        total_count = len(self.regions_info)
        self.progress_label.config(text=f"Calibrated: {calibrated_count}/{total_count} regions")
        
        self.display_screenshot()
        self.status_label.config(text=f"Cleared region '{self.current_region}'")
        
    def save_calibration(self):
        """Save calibration results."""
        if not self.calibrated_regions:
            messagebox.showwarning("Warning", "No calibration data to save!")
            return
            
        # Save coordinates
        with open('acr_calibration_results.json', 'w') as f:
            json.dump(self.calibrated_regions, f, indent=2)
            
        # Save visual overlay
        if self.screenshot:
            overlay_img = self.screenshot.copy()
            self.draw_regions_on_original(overlay_img)
            overlay_img.save('acr_calibration_overlay.png')
            
        messagebox.showinfo("Success", 
                          "Calibration saved!\n"
                          "Files: acr_calibration_results.json, acr_calibration_overlay.png")
        
        # Generate report
        self.generate_final_report()
        
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
                
                draw.rectangle([x1, y1, x2, y2], outline=color, width=3)
                draw.rectangle([x1, y1 - 25, x1 + len(region_name) * 10, y1], fill=color)
                draw.text((x1 + 2, y1 - 23), region_name, fill='black', font=font)
                
    def generate_final_report(self):
        """Generate final calibration report."""
        total_regions = len(self.regions_info)
        calibrated_regions = len(self.calibrated_regions)
        success_rate = (calibrated_regions / total_regions) * 100 if total_regions > 0 else 0
        
        report = f"""
🎯 ACR CALIBRATION RESULTS
{'='*50}
Success Rate: {calibrated_regions}/{total_regions} regions ({success_rate:.1f}%)

"""
        
        if success_rate >= 80:
            report += "🎉 EXCELLENT! ACR scraper should work very well\n"
        elif success_rate >= 60:
            report += "👍 GOOD! ACR scraper should work with minor tuning\n"
        elif success_rate >= 40:
            report += "⚠️ MODERATE! Some regions need adjustment\n"
        else:
            report += "❌ POOR! Significant calibration work needed\n"
            
        report += f"""
📁 Files created:
• acr_screenshot.png - Full captured table
• acr_region_*.png - Individual region extracts  
• acr_calibration_results.json - Coordinate data
• acr_calibration_overlay.png - Visual verification

🚀 Next steps:
"""
        
        if success_rate >= 60:
            report += "✅ Ready to test with full poker advisory API!"
        else:
            report += "🔧 Adjust coordinates for failed regions and re-test"
            
        # Save report
        with open('acr_calibration_report.txt', 'w') as f:
            f.write(report)
            
        # Show in popup
        messagebox.showinfo("Calibration Complete", report)
        
    def run(self):
        """Run the calibration tool."""
        self.root.mainloop()

def main():
    """Main entry point."""
    print("🎮 Starting ACR Visual Calibration Tool...")
    
    # Check prerequisites
    try:
        pytesseract.get_tesseract_version()
        print("✅ Tesseract OCR ready")
    except Exception as e:
        print(f"❌ Tesseract OCR error: {e}")
        print("📥 Install from: https://github.com/tesseract-ocr/tesseract")
        return
        
    calibrator = VisualACRCalibrator()
    calibrator.run()

if __name__ == "__main__":
    main()