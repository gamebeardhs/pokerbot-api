#!/usr/bin/env python3
"""
Complete ACR Poker Scraper Calibration Tool
Includes all regions needed for full GTO bot functionality.

Requirements:
- pip install pillow opencv-python pytesseract tkinter
- Install Tesseract OCR: https://github.com/tesseract-ocr/tesseract
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

class CompleteACRCalibrator:
    """Complete calibration tool for all ACR poker table regions."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Complete ACR Calibration Tool")
        self.root.geometry("1400x900")
        
        # Data
        self.screenshot = None
        self.calibrated_regions = {}
        self.current_region = None
        self.selection_start = None
        self.selection_rect = None
        self.scale = 1.0
        
        # Colors for different region types
        self.region_colors = {
            # Critical game state
            'pot_area': '#FF0000',
            'hero_cards': '#00FF00',
            'board_cards': '#0000FF',
            'action_buttons': '#FFFF00',
            'current_bet': '#FF8800',
            
            # Table info
            'stakes_info': '#FF00FF',
            'button_indicator': '#8800FF',
            'dealer_position': '#FF0088',
            
            # Player seats (6-max typical)
            'seat_1_name': '#00FFFF', 'seat_1_stack': '#88FFFF',
            'seat_2_name': '#FFA500', 'seat_2_stack': '#FFCC88',
            'seat_3_name': '#800080', 'seat_3_stack': '#CC88CC',
            'seat_4_name': '#FFC0CB', 'seat_4_stack': '#FFDDDD',
            'seat_5_name': '#A52A2A', 'seat_5_stack': '#CC8888',
            'seat_6_name': '#808080', 'seat_6_stack': '#CCCCCC',
            
            # Betting info per seat
            'seat_1_bet': '#CCFFFF', 'seat_2_bet': '#FFDDAA',
            'seat_3_bet': '#DDAADD', 'seat_4_bet': '#FFEEEE',
            'seat_5_bet': '#DDAAAA', 'seat_6_bet': '#DDDDDD',
            
            # Hero specific
            'hero_stack': '#00AA00',
            'hero_position_indicator': '#AAFF00'
        }
        
        # Complete region definitions
        self.regions_info = {
            # === CRITICAL GAME STATE ===
            'pot_area': {
                'desc': 'Main Pot Amount',
                'category': 'Game State',
                'example': 'Pot $4.06',
                'priority': 'CRITICAL',
                'ocr_tips': 'Look for "Pot" text with dollar amount'
            },
            'hero_cards': {
                'desc': 'Your Hole Cards',
                'category': 'Game State', 
                'example': '3s Ah',
                'priority': 'CRITICAL',
                'ocr_tips': 'Two cards with rank+suit (3s, Ah, Kh, etc.)'
            },
            'board_cards': {
                'desc': 'Community Cards (Flop/Turn/River)',
                'category': 'Game State',
                'example': 'Ks 8h 5h 5s 5c',
                'priority': 'CRITICAL',
                'ocr_tips': 'Up to 5 cards, rank+suit format'
            },
            'action_buttons': {
                'desc': 'Fold/Check/Call/Bet/Raise Buttons',
                'category': 'Game State',
                'example': 'Check, Bet $0.50',
                'priority': 'CRITICAL',
                'ocr_tips': 'Button text with amounts'
            },
            'current_bet': {
                'desc': 'Current Bet to Call',
                'category': 'Game State',
                'example': '$0.50 to call',
                'priority': 'HIGH',
                'ocr_tips': 'Amount needed to call current bet'
            },
            
            # === TABLE INFORMATION ===
            'stakes_info': {
                'desc': 'Table Stakes/Blinds',
                'category': 'Table Info',
                'example': '$0.25/$0.50 | No Limit',
                'priority': 'HIGH',
                'ocr_tips': 'Usually at top of table'
            },
            'button_indicator': {
                'desc': 'Dealer Button Position',
                'category': 'Table Info',
                'example': 'White button disk',
                'priority': 'HIGH',
                'ocr_tips': 'Look for button symbol or "D" marker'
            },
            
            # === PLAYER SEATS (Names) ===
            'seat_1_name': {
                'desc': 'Player 1 Name',
                'category': 'Players',
                'example': 'TSudden1',
                'priority': 'MEDIUM',
                'ocr_tips': 'Player username'
            },
            'seat_2_name': {
                'desc': 'Player 2 Name', 
                'category': 'Players',
                'example': 'EvroeN85',
                'priority': 'MEDIUM',
                'ocr_tips': 'Player username'
            },
            'seat_3_name': {
                'desc': 'Player 3 Name',
                'category': 'Players', 
                'example': 'drtyprist',
                'priority': 'MEDIUM',
                'ocr_tips': 'Player username'
            },
            'seat_4_name': {
                'desc': 'Player 4 Name',
                'category': 'Players',
                'example': 'SandersPro', 
                'priority': 'MEDIUM',
                'ocr_tips': 'Player username'
            },
            'seat_5_name': {
                'desc': 'Player 5 Name',
                'category': 'Players',
                'example': 'thepokerbank',
                'priority': 'MEDIUM', 
                'ocr_tips': 'Player username'
            },
            'seat_6_name': {
                'desc': 'Player 6 Name',
                'category': 'Players',
                'example': 'YourName',
                'priority': 'MEDIUM',
                'ocr_tips': 'Player username'
            },
            
            # === PLAYER STACKS ===
            'seat_1_stack': {
                'desc': 'Player 1 Stack Size',
                'category': 'Stacks',
                'example': '$50.00',
                'priority': 'HIGH',
                'ocr_tips': 'Dollar amount under player name'
            },
            'seat_2_stack': {
                'desc': 'Player 2 Stack Size',
                'category': 'Stacks', 
                'example': '$50.02',
                'priority': 'HIGH',
                'ocr_tips': 'Dollar amount under player name'
            },
            'seat_3_stack': {
                'desc': 'Player 3 Stack Size',
                'category': 'Stacks',
                'example': '$48.61', 
                'priority': 'HIGH',
                'ocr_tips': 'Dollar amount under player name'
            },
            'seat_4_stack': {
                'desc': 'Player 4 Stack Size',
                'category': 'Stacks',
                'example': '$50.00',
                'priority': 'HIGH',
                'ocr_tips': 'Dollar amount under player name'
            },
            'seat_5_stack': {
                'desc': 'Player 5 Stack Size',
                'category': 'Stacks',
                'example': '$63.60',
                'priority': 'HIGH', 
                'ocr_tips': 'Dollar amount under player name'
            },
            'seat_6_stack': {
                'desc': 'Player 6 Stack Size',
                'category': 'Stacks',
                'example': '$45.25',
                'priority': 'HIGH',
                'ocr_tips': 'Dollar amount under player name'
            },
            
            # === CURRENT BETS ===
            'seat_1_bet': {
                'desc': 'Player 1 Current Bet',
                'category': 'Betting',
                'example': '$0.25',
                'priority': 'MEDIUM',
                'ocr_tips': 'Chips in front of player'
            },
            'seat_2_bet': {
                'desc': 'Player 2 Current Bet',
                'category': 'Betting',
                'example': '$0.50', 
                'priority': 'MEDIUM',
                'ocr_tips': 'Chips in front of player'
            },
            'seat_3_bet': {
                'desc': 'Player 3 Current Bet',
                'category': 'Betting',
                'example': '$2.00',
                'priority': 'MEDIUM',
                'ocr_tips': 'Chips in front of player'
            },
            'seat_4_bet': {
                'desc': 'Player 4 Current Bet',
                'category': 'Betting',
                'example': '$0.00',
                'priority': 'MEDIUM',
                'ocr_tips': 'Chips in front of player'
            },
            'seat_5_bet': {
                'desc': 'Player 5 Current Bet',
                'category': 'Betting',
                'example': '$0.00',
                'priority': 'MEDIUM',
                'ocr_tips': 'Chips in front of player'
            },
            'seat_6_bet': {
                'desc': 'Player 6 Current Bet',
                'category': 'Betting',
                'example': '$0.00',
                'priority': 'MEDIUM',
                'ocr_tips': 'Chips in front of player'
            }
        }
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the user interface."""
        # Main layout
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left panel for controls  
        control_frame = ttk.Frame(main_frame, width=350)
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
        title = ttk.Label(parent, text="Complete ACR Calibrator", font=('Arial', 14, 'bold'))
        title.pack(pady=(0, 10))
        
        # Instructions
        instructions = tk.Text(parent, height=5, wrap=tk.WORD, bg='#f0f0f0')
        instructions.pack(fill=tk.X, pady=(0, 10))
        instructions.insert(tk.END, 
            "COMPLETE ACR CALIBRATION:\n"
            "1. Capture ACR table screenshot\n"
            "2. Select region category\n" 
            "3. Click region button\n"
            "4. Click-drag to select area\n"
            "5. Verify OCR results")
        instructions.config(state=tk.DISABLED)
        
        # Capture button
        capture_btn = ttk.Button(parent, text="📸 Capture ACR Table", 
                               command=self.capture_acr_screen)
        capture_btn.pack(fill=tk.X, pady=(0, 10))
        
        # Progress
        self.progress_label = ttk.Label(parent, text="0 regions calibrated")
        self.progress_label.pack(pady=(0, 10))
        
        # Category selection
        self.setup_category_tabs(parent)
        
        # OCR Results
        ttk.Label(parent, text="OCR Results:", 
                 font=('Arial', 12, 'bold')).pack(anchor=tk.W, pady=(20, 5))
        
        self.ocr_text = tk.Text(parent, height=6, wrap=tk.WORD)
        self.ocr_text.pack(fill=tk.X, pady=(0, 10))
        
        # Action buttons
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(button_frame, text="Test OCR", 
                  command=self.test_current_ocr).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Clear", 
                  command=self.clear_current_region).pack(side=tk.LEFT)
        
        # Save button
        ttk.Button(parent, text="💾 Save Complete Calibration", 
                  command=self.save_calibration).pack(fill=tk.X, pady=(20, 0))
        
    def setup_category_tabs(self, parent):
        """Setup tabbed interface for region categories."""
        # Category notebook
        self.notebook = ttk.Notebook(parent)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        # Group regions by category
        categories = {}
        for region_name, info in self.regions_info.items():
            category = info['category']
            if category not in categories:
                categories[category] = []
            categories[category].append((region_name, info))
        
        # Create tabs for each category
        self.region_buttons = {}
        for category, regions in categories.items():
            # Create tab frame
            tab_frame = ttk.Frame(self.notebook)
            self.notebook.add(tab_frame, text=category)
            
            # Add scrollable frame
            canvas = tk.Canvas(tab_frame)
            scrollbar = ttk.Scrollbar(tab_frame, orient="vertical", command=canvas.yview)
            scrollable_frame = ttk.Frame(canvas)
            
            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )
            
            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)
            
            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            
            # Add region buttons to this category
            for region_name, info in sorted(regions, key=lambda x: x[1]['priority'], reverse=True):
                self.create_region_button(scrollable_frame, region_name, info)
                
    def create_region_button(self, parent, region_name, info):
        """Create a region selection button."""
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, pady=2, padx=5)
        
        # Priority badge
        priority_colors = {'CRITICAL': '#ff4444', 'HIGH': '#ff8844', 'MEDIUM': '#ffaa44', 'LOW': '#44ff44'}
        priority_color = priority_colors.get(info['priority'], '#888888')
        
        # Button with priority and description
        btn_text = f"[{info['priority']}] {info['desc']}"
        
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
        
        # OCR tips (tooltip-style)
        tips_label = ttk.Label(frame, text=f"💡 {info['ocr_tips']}", 
                             foreground='blue', font=('Arial', 7))
        tips_label.pack(fill=tk.X)
        
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
        self.status_label = ttk.Label(parent, text="Click 'Capture ACR Table' to begin")
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)
        
    def capture_acr_screen(self):
        """Capture ACR screen after countdown."""
        self.status_label.config(text="Preparing to capture...")
        self.root.withdraw()  # Hide window
        
        # Countdown in separate window
        countdown_window = tk.Toplevel()
        countdown_window.title("Capturing ACR Table")
        countdown_window.geometry("300x100")
        countdown_window.attributes('-topmost', True)
        
        countdown_label = ttk.Label(countdown_window, text="Make ACR table visible and active...", 
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
            self.screenshot.save("acr_complete_screenshot.png")
            self.display_screenshot()
            self.status_label.config(text=f"ACR table captured: {self.screenshot.size[0]}x{self.screenshot.size[1]}")
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
        self.scale = min(scale_x, scale_y, 0.8)  # Scale down a bit for easier viewing
        
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
            font = ImageFont.truetype("arial.ttf", 10)
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
                
                # Shorter label for display
                short_name = region_name.replace('_', ' ').title()
                draw.text((x1, y1 - 12), short_name, fill=color, font=font)
                
    def select_region(self, region_name):
        """Select a region for calibration."""
        if not self.screenshot:
            messagebox.showwarning("Warning", "Please capture ACR table first!")
            return
            
        self.current_region = region_name
        region_info = self.regions_info[region_name]
        
        self.status_label.config(text=f"Selected: {region_info['desc']} - Click and drag on image to select area")
        
        # Show OCR tips for this region
        self.ocr_text.delete(1.0, tk.END)
        self.ocr_text.insert(tk.END, f"📍 Calibrating: {region_info['desc']}\n")
        self.ocr_text.insert(tk.END, f"💡 Tips: {region_info['ocr_tips']}\n")
        self.ocr_text.insert(tk.END, f"📝 Example: {region_info['example']}\n\n")
        self.ocr_text.insert(tk.END, "Click and drag on the image to select this region...")
        
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
            
        self.status_label.config(text=f"'{self.current_region}' calibrated! Check OCR results.")
        
    def test_current_ocr(self):
        """Test OCR on current region with card-specific optimization."""
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
            results = self.test_ocr_methods(region_img, self.current_region)
            
            # Display results
            self.ocr_text.delete(1.0, tk.END)
            self.ocr_text.insert(tk.END, f"🔍 OCR Results for {self.current_region}:\n")
            self.ocr_text.insert(tk.END, f"📐 Coordinates: {coords}\n\n")
            
            best_result = ""
            best_confidence = 0
            
            for method, text in results.items():
                status = "✅" if text and len(text.strip()) > 0 else "❌"
                confidence = len(text.strip()) if text else 0
                self.ocr_text.insert(tk.END, f"{status} {method:15}: '{text}'\n")
                
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_result = text.strip()
                    
            if best_result:
                self.ocr_text.insert(tk.END, f"\n🎯 Best result: '{best_result}'\n")
                
                # Validate result for card regions
                if 'cards' in self.current_region:
                    card_validation = self.validate_card_ocr(best_result)
                    self.ocr_text.insert(tk.END, f"🃏 Card validation: {card_validation}\n")
            else:
                self.ocr_text.insert(tk.END, "\n❌ No readable text found\n")
                self.ocr_text.insert(tk.END, "💡 Try adjusting the selection area or check image quality\n")
                
            # Save region image for manual inspection
            region_img.save(f"acr_region_{self.current_region}.png")
            
        except Exception as e:
            self.ocr_text.delete(1.0, tk.END)
            self.ocr_text.insert(tk.END, f"❌ OCR Error: {e}")
            
    def test_ocr_methods(self, region_img, region_name):
        """Test different OCR methods with region-specific optimization."""
        results = {}
        
        try:
            cv_img = cv2.cvtColor(np.array(region_img), cv2.COLOR_RGB2BGR)
            gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
            
            # Method 1: Raw OCR
            results['Raw'] = pytesseract.image_to_string(region_img).strip()
            
            # Method 2: Binary threshold
            _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
            binary_pil = Image.fromarray(binary)
            results['Binary'] = pytesseract.image_to_string(binary_pil).strip()
            
            # Method 3: Inverted binary (for dark text on light background)
            _, inv_binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)
            inv_binary_pil = Image.fromarray(inv_binary)
            results['Inverted'] = pytesseract.image_to_string(inv_binary_pil).strip()
            
            # Method 4: Card-specific OCR (for card regions)
            if 'cards' in region_name or 'card' in region_name:
                card_config = r'--oem 3 --psm 8 -c tessedit_char_whitelist=23456789TJQKAHSCDhscd '
                results['Card-Optimized'] = pytesseract.image_to_string(binary_pil, config=card_config).strip()
                
                # Enhanced card preprocessing
                # Try different thresholds for cards
                _, binary_150 = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
                binary_150_pil = Image.fromarray(binary_150)
                results['Card-High-Thresh'] = pytesseract.image_to_string(binary_150_pil, config=card_config).strip()
            
            # Method 5: Money/number optimized (for amounts)
            elif any(keyword in region_name for keyword in ['stack', 'bet', 'pot', 'stakes']):
                money_config = r'--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789$.,/ '
                results['Money-Optimized'] = pytesseract.image_to_string(binary_pil, config=money_config).strip()
            
            # Method 6: Name optimized (for player names)
            elif 'name' in region_name:
                name_config = r'--oem 3 --psm 8 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_- '
                results['Name-Optimized'] = pytesseract.image_to_string(binary_pil, config=name_config).strip()
            
            # Method 7: General poker optimized
            else:
                poker_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz$.,/ '
                results['Poker-General'] = pytesseract.image_to_string(binary_pil, config=poker_config).strip()
            
        except Exception as e:
            results['Error'] = str(e)
            
        return results
        
    def validate_card_ocr(self, text):
        """Validate OCR results for card regions."""
        if not text:
            return "❌ No text detected"
            
        # Expected card format: rank + suit (2-9, T, J, Q, K, A + h, s, c, d)
        valid_ranks = '23456789TJQKA'
        valid_suits = 'hscd'
        
        # Split into potential cards
        cards = text.replace(' ', '').replace(',', ' ').split()
        valid_cards = []
        
        for card in cards:
            if len(card) == 2:
                rank, suit = card[0].upper(), card[1].lower()
                if rank in valid_ranks and suit in valid_suits:
                    valid_cards.append(f"{rank}{suit}")
        
        if valid_cards:
            return f"✅ Found {len(valid_cards)} valid cards: {', '.join(valid_cards)}"
        else:
            return f"⚠️ Text detected but no valid cards: '{text}'"
            
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
        """Save complete calibration results."""
        if not self.calibrated_regions:
            messagebox.showwarning("Warning", "No calibration data to save!")
            return
            
        # Save coordinates
        with open('acr_complete_calibration.json', 'w') as f:
            json.dump(self.calibrated_regions, f, indent=2)
            
        # Save visual overlay
        if self.screenshot:
            overlay_img = self.screenshot.copy()
            self.draw_regions_on_original(overlay_img)
            overlay_img.save('acr_complete_overlay.png')
            
        # Generate comprehensive report
        self.generate_comprehensive_report()
        
        messagebox.showinfo("Success", 
                          "Complete calibration saved!\n"
                          "Files: acr_complete_calibration.json, acr_complete_overlay.png, acr_complete_report.txt")
        
    def draw_regions_on_original(self, img):
        """Draw all calibrated regions on original full-size image."""
        draw = ImageDraw.Draw(img)
        
        try:
            font = ImageFont.truetype("arial.ttf", 12)
        except:
            font = ImageFont.load_default()
            
        for region_name, coords in self.calibrated_regions.items():
            if coords:
                x1, y1, x2, y2 = coords
                color = self.region_colors.get(region_name, '#FFFFFF')
                
                draw.rectangle([x1, y1, x2, y2], outline=color, width=2)
                
                # Label with background
                label = region_name.replace('_', ' ')
                draw.rectangle([x1, y1 - 20, x1 + len(label) * 8, y1], fill=color)
                draw.text((x1 + 2, y1 - 18), label, fill='black', font=font)
                
    def generate_comprehensive_report(self):
        """Generate comprehensive calibration report."""
        total_regions = len(self.regions_info)
        calibrated_regions = len(self.calibrated_regions)
        
        # Calculate success by category
        category_stats = {}
        for region_name, info in self.regions_info.items():
            category = info['category']
            if category not in category_stats:
                category_stats[category] = {'total': 0, 'calibrated': 0}
            category_stats[category]['total'] += 1
            if region_name in self.calibrated_regions:
                category_stats[category]['calibrated'] += 1
        
        # Priority breakdown
        priority_stats = {}
        for region_name, info in self.regions_info.items():
            priority = info['priority']
            if priority not in priority_stats:
                priority_stats[priority] = {'total': 0, 'calibrated': 0}
            priority_stats[priority]['total'] += 1
            if region_name in self.calibrated_regions:
                priority_stats[priority]['calibrated'] += 1
        
        success_rate = (calibrated_regions / total_regions) * 100 if total_regions > 0 else 0
        
        report = f"""
🎯 COMPLETE ACR CALIBRATION RESULTS
{'='*60}
Overall Success Rate: {calibrated_regions}/{total_regions} regions ({success_rate:.1f}%)

📊 SUCCESS BY CATEGORY:
"""
        
        for category, stats in category_stats.items():
            cat_rate = (stats['calibrated'] / stats['total']) * 100 if stats['total'] > 0 else 0
            report += f"  {category:15}: {stats['calibrated']:2}/{stats['total']:2} ({cat_rate:5.1f}%)\n"
        
        report += f"\n🎖️ SUCCESS BY PRIORITY:\n"
        for priority in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
            if priority in priority_stats:
                stats = priority_stats[priority]
                pri_rate = (stats['calibrated'] / stats['total']) * 100 if stats['total'] > 0 else 0
                report += f"  {priority:10}: {stats['calibrated']:2}/{stats['total']:2} ({pri_rate:5.1f}%)\n"
        
        # Assessment
        critical_success = priority_stats.get('CRITICAL', {}).get('calibrated', 0)
        critical_total = priority_stats.get('CRITICAL', {}).get('total', 1)
        critical_rate = (critical_success / critical_total) * 100
        
        report += f"\n🎯 ASSESSMENT:\n"
        if critical_rate >= 75:
            report += "🎉 EXCELLENT! Critical regions work well - ready for GTO bot!\n"
        elif critical_rate >= 50:
            report += "👍 GOOD! Most critical regions work - minor tuning needed\n"
        elif critical_rate >= 25:
            report += "⚠️ MODERATE! Some critical regions need work\n"
        else:
            report += "❌ POOR! Critical regions need major calibration work\n"
        
        report += f"""
📁 FILES CREATED:
• acr_complete_screenshot.png - Full captured table
• acr_region_*.png - Individual region extracts
• acr_complete_calibration.json - All coordinate data
• acr_complete_overlay.png - Visual verification
• acr_complete_report.txt - This report

🚀 NEXT STEPS:
"""
        
        if critical_rate >= 75:
            report += """✅ Ready to integrate with GTO bot!
✅ Test with live ACR tables
✅ Deploy complete poker advisory system"""
        else:
            report += """🔧 Focus on critical regions first
🔧 Adjust coordinates for failed regions
🔧 Test different OCR preprocessing
🔧 Re-run calibration for problem areas"""
        
        # Save report
        with open('acr_complete_report.txt', 'w') as f:
            f.write(report)
            
        # Show summary in popup
        summary = f"""Calibration Complete!

Success Rate: {success_rate:.1f}%
Critical Regions: {critical_success}/{critical_total}

{report.split('ASSESSMENT:')[1].split('FILES CREATED:')[0].strip()}"""
        
        messagebox.showinfo("Complete Calibration Results", summary)
        
    def run(self):
        """Run the complete calibration tool."""
        self.root.mainloop()

def main():
    """Main entry point."""
    print("🎮 Starting Complete ACR Calibration Tool...")
    print("This tool calibrates ALL regions needed for a full GTO poker bot")
    
    # Check prerequisites
    try:
        pytesseract.get_tesseract_version()
        print("✅ Tesseract OCR ready")
    except Exception as e:
        print(f"❌ Tesseract OCR error: {e}")
        print("📥 Install from: https://github.com/tesseract-ocr/tesseract")
        return
        
    calibrator = CompleteACRCalibrator()
    calibrator.run()

if __name__ == "__main__":
    main()