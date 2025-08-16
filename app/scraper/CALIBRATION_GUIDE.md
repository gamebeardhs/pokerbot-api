# Poker Scraper Calibration Guide

This guide explains how to properly calibrate and test the poker scrapers to ensure they work correctly with real poker sites.

## Overview

The scrapers need calibration because:
- **ACR Scraper**: Uses screen capture + OCR, needs exact pixel coordinates for UI elements
- **ClubWPT Scraper**: Uses browser automation, needs correct CSS selectors for DOM elements

## Quick Start

### 1. Run Calibration Tools

```bash
# Calibrate ACR scraper (screen regions)
python app/scraper/debug_tools.py
# Choose option 1

# Calibrate ClubWPT scraper (CSS selectors)  
python app/scraper/debug_tools.py
# Choose option 2
```

### 2. Test Scrapers

```bash
# Test if scrapers work correctly
python app/scraper/test_scrapers.py
```

## Detailed Calibration Process

### ACR Scraper Calibration

**What you need:**
- ACR poker client installed and running
- Active poker table (can be play money)
- Screen resolution noted (e.g., 1920x1080)

**Steps:**

1. **Open ACR and join a table**
   ```bash
   python app/scraper/debug_tools.py
   # Choose option 1 (ACR calibration)
   ```

2. **The tool will capture your screen and ask for coordinates**
   - Format: `x1,y1,x2,y2` (top-left to bottom-right)
   - Use screenshot viewers or built-in tools to find coordinates

3. **For each UI element, identify the coordinates:**
   - `pot_area`: Where pot size is displayed
   - `hero_cards`: Your hole cards area
   - `board_cards`: Community cards area
   - `action_buttons`: Fold/Call/Raise buttons
   - `stakes_info`: Table stakes (blinds) display
   - `seat_1` through `seat_8`: Each player seat area

4. **The tool will:**
   - Test OCR on each region immediately
   - Show you what text it can extract
   - Save coordinates to `acr_calibrated_regions.json`
   - Create `acr_regions_overlay.png` for visual verification

**Example coordinate entry:**
```
Enter coordinates for pot_area: 850,300,1070,350
OCR Results for pot_area:
  raw: 'Pot: $15.50'
  poker_optimized: '$15.50'
```

### ClubWPT Scraper Calibration

**What you need:**
- ClubWPT Gold account 
- Active browser session at a poker table

**Steps:**

1. **Start calibration tool**
   ```bash
   python app/scraper/debug_tools.py
   # Choose option 2 (ClubWPT calibration)
   ```

2. **The tool will open a browser**
   - Log in manually to ClubWPT Gold
   - Navigate to a poker table
   - Press Enter when ready

3. **For each element, the tool helps you find selectors:**

   **Method 1 - Search by text:**
   ```
   Enter text to search for pot amount: pot
   Found elements:
     0: div.pot-display - 'Pot: $15.50'
     1: span.pot-value - '$15.50'
   Enter index to use: 1
   ```

   **Method 2 - Custom CSS selector:**
   ```
   Enter custom CSS selector for player names: .player-seat .username
   Selector test result:
     Found 6 elements
       span: 'Player1'
       span: 'Hero123'
   Use this selector? (y/n): y
   ```

4. **Elements to calibrate:**
   - Player seats and names
   - Stack amounts
   - Pot size
   - Hero cards
   - Board cards
   - Action buttons
   - Dealer button
   - Current bets

5. **The tool saves:**
   - `clubwpt_calibrated_selectors.json` with all selectors
   - Test results showing what data each selector finds

## Testing Your Calibration

### 1. Basic Functionality Test

```bash
python app/scraper/test_scrapers.py
```

This will:
- Test scraper setup
- Check table detection  
- Extract sample data
- Validate data completeness
- Save sample data to JSON files

### 2. Validation Report Example

```
VALIDATION REPORT: ACR Scraper
=====================================
Overall Valid: ✅ YES

COMPLETENESS:
  Basic: 6/6
  Enhanced: 5/6
  Seats: 4/6

DATA SAMPLE:
  stakes: $0.01/$0.02
  players: 6
  hero_cards: 2
  board_cards: 3
  positioned_players: 6

⚠️  WARNINGS (2):
  - Missing enhanced field: current_aggressor_seat
  - Seat 3 missing position
```

### 3. Common Issues & Solutions

**ACR Issues:**
```
❌ OCR returns gibberish
→ Solution: Adjust region coordinates, try different preprocessing

❌ No table detected  
→ Solution: Ensure ACR window is visible, update is_table_active() logic

❌ Wrong stack amounts
→ Solution: Refine stack extraction regions, improve number parsing
```

**ClubWPT Issues:**
```
❌ Selector finds 0 elements
→ Solution: Update CSS selectors, check if site layout changed

❌ Text extraction returns empty
→ Solution: Try different element attributes (text_content vs innerText)

❌ Hero not identified
→ Solution: Find better selector for active/hero player indicator
```

## Integration Testing

### Test with GTO Service

```bash
# Test full integration
python app/scraper/test_scrapers.py
# Choose option 4 (test data conversion)
```

This verifies:
- Scraped data converts to TableState model
- All required fields are present
- Data types are correct
- GTO service can process the data

### Sample Integration

```python
# Example: Use calibrated scraper with GTO service
scraper = ACRScraper()
table_data = await scraper.scrape_table_state()

# Convert to TableState
state = convert_to_table_state(table_data)

# Get GTO decision
gto_service = EnhancedGTODecisionService()
decision = await gto_service.compute_gto_decision(state)
```

## Maintenance

### When to Recalibrate

**ACR:**
- Screen resolution changes
- ACR client updates change UI layout
- OCR accuracy drops

**ClubWPT:**
- Site updates change HTML structure
- CSS class names change
- New features added to poker table

### Monitoring Scraper Health

```bash
# Regular validation
python app/scraper/debug_tools.py
# Choose option 3 (test existing calibrations)
```

Run this periodically to ensure scrapers still work correctly.

## Files Created

After calibration, you'll have:

```
app/scraper/
├── acr_calibrated_regions.json      # ACR screen coordinates
├── acr_regions_overlay.png          # Visual verification
├── acr_test_data.json              # Sample scraped data
├── clubwpt_calibrated_selectors.json # ClubWPT CSS selectors  
├── clubwpt_test_data.json          # Sample scraped data
└── region_*.png                    # Individual region captures
```

These files are used by the scrapers and can be version controlled for your setup.

## Next Steps

Once calibrated and tested:

1. **Update scraper code** with your calibrated values
2. **Run integration tests** with GTO service
3. **Test in production** with real poker situations
4. **Monitor and adjust** as needed

The calibration process ensures your scrapers work reliably with real poker sites and provide accurate data for GTO decisions.