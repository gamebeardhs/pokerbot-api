# Windows 10-Minute Smoke Test Plan

## Pre-Test Setup (2 minutes)

### Windows Environment
- **Display Scaling**: Set to 100% for initial test
  - Right-click desktop → Display settings → Scale and layout → 100%
- **ACR Setup**: Single table, default theme, default table scale
- **Tesseract**: Verify installation at `C:\Program Files\Tesseract-OCR\`

### Verify System Ready
```bash
# Check production readiness
curl http://localhost:5000/production/deployment-checklist

# Verify Windows compatibility
curl http://localhost:5000/production/test-windows-compatibility
```

## Phase 1: Calibration (2 minutes)

### Run Calibration Once
```bash
curl -X POST http://localhost:5000/calibration/auto-calibrate
```

### Verify Calibration Results
- Check calibration saved as **percentages** in `acr_calibration_results.json`
- Verify live previews show readable crops (pot, stack, buttons)
- Ensure regions are resolution-independent

### Expected Results
✅ Calibration saves relative coordinates (0.0-1.0 range)  
✅ Preview images show clear text regions  
✅ No hard-coded pixel coordinates  

## Phase 2: Live Scraper Test (3 minutes)

### Start Scraper
```bash
curl http://localhost:5000/auto/table-data
```

### Monitor Logs
Expected log entries:
- Tesseract version and path
- Client rectangle dimensions (x, y, width, height)
- FPS timing with jitter
- DPI awareness status

### Verify Core Functionality
- **Pot/Stack Stabilization**: Values should stabilize after 2 identical reads
- **Turn Detection**: During action, `is_our_turn` → `True` 
- **Debug Capture**: Check `captures/<timestamp>/` directory created

### Expected Results
✅ Stable pot/stack readings (no jumping values)  
✅ Turn detection works when action buttons appear  
✅ Debug bundles auto-generated with screenshots + OCR data  

## Phase 3: Resilience Testing (2 minutes)

### Window Resize Test
1. Resize ACR window by ~15%
2. Check readings remain accurate **without recalibration**
3. Verify percentage-based regions work correctly

### DPI Scaling Test
1. Change Windows scaling to 125%
   - Right-click desktop → Display settings → Scale → 125%
2. Verify coordinates remain stable with DPI awareness
3. Check readings still accurate

### Expected Results
✅ Window resize: OCR accuracy maintained  
✅ DPI scaling: No coordinate drift  
✅ System adapts automatically without recalibration  

## Phase 4: Regression Test (1 minute)

### Run Offline Test
```bash
cd /path/to/poker-system
python -m app.tools.run_offline_ocr_test tests/acr_golden
```

### Expected Output
```
✅ All assertions passed for N expected values
REGRESSION TEST PASSED
```

## Troubleshooting Quick Reference

| Symptom | Likely Cause | Quick Fix |
|---------|--------------|-----------|
| Pot/stack values jumping | Crop includes graphics/chips | Reduce region size, check `pot.png` in captures |
| Buttons not detected | Font/contrast issues | Enlarge buttons region, verify in debug images |
| Offsets after window move | Percentage regions not used | Check `acr_calibration_results.json` has 0.0-1.0 values |
| Black/empty captures | Wrong monitor/coordinates | Verify table_full.png not black, check client rect |
| OCR confusion (1O vs 10) | Character misclassification | Check normalization in `ocr.json` (O→0, l→1) |

## Success Criteria

### ✅ All Tests Pass If:
- Calibration saves percentage coordinates
- OCR readings stabilize within 2 frames
- Turn detection responds to action buttons
- Window resize doesn't break accuracy
- DPI scaling doesn't cause coordinate drift
- Regression test passes all assertions
- Debug captures show clear region crops

### 📊 Performance Targets:
- **Response Time**: < 5 seconds per reading
- **FPS**: 2-5 Hz with random jitter
- **Accuracy**: 95%+ for money/stack values
- **Stability**: No false positives in turn detection

## Debug Artifacts

If anything fails, examine:
- `captures/<timestamp>/table_full.png` - Full screen capture
- `captures/<timestamp>/pot.png` - Individual region crops
- `captures/<timestamp>/ocr.json` - Raw vs normalized text results  
- `captures/<timestamp>/env.json` - System environment info

## Next Steps After Success

1. **Production Deployment**: System ready for real ACR use
2. **Advanced Testing**: Multiple table scenarios
3. **Performance Tuning**: Adjust config/acr_runtime.json as needed
4. **Monitoring Setup**: Log analysis for long-term stability