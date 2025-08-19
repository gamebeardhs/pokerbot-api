# ACR Poker System Troubleshooting Matrix

## Quick Diagnostics (< 30 seconds per issue)

| **Symptom** | **Likely Cause** | **Fix** | **Verification** |
|-------------|------------------|---------|------------------|
| **Pot/stack values jumping around** | Crop includes moving chips/graphics; OCR threshold too aggressive | Reduce region by 10-20% to exclude chip animations; check `pot.png` in debug captures for clean background | Values should stabilize within 2 readings |
| **Buttons not detected during action** | ACR theme has weak font contrast; button region too small | Temporarily enlarge buttons region by 20%; try PSM mode 7; confirm whitelist includes all letters | `is_our_turn` should be `true` when action buttons visible |
| **All crops offset after moving window** | System using absolute pixels instead of percentages; DPI not applied | Ensure `acr_calibration_results.json` contains values 0.0-1.0; verify `env.json` shows `dpi_aware: true` | Resize window 15% - readings should stay accurate |
| **Black or empty frame captures** | Grabbing wrong monitor area; window not found | Check `table_full.png` in captures; log client rect coordinates; verify ACR window detection | Debug captures should show actual table content |
| **OCR confusing 1O vs 10, l1 vs II** | Common character misclassification | Built-in normalization maps O→0, l→1; verify `ocr.json` shows clean `pot_norm` values | Raw OCR may show errors but normalized should be correct |
| **Turn detection false positives** | Timer colors bleeding from other UI elements | Reduce `hero_timer_arc` region size; adjust HSV ranges in config; check timer crop shows only arc area | Should only trigger during actual turn |
| **Calibration not persisting** | Filename mismatch between save/load | Verify both save to and load from `acr_calibration_results.json`; check file permissions | Restart system - calibration should reload |
| **System too slow (>5sec response)** | OCR processing bottleneck; image too large | Verify 2x upscaling only (not 4x+); check Tesseract PSM settings; consider GPU acceleration | Target <3 seconds per complete table read |

## Advanced Debugging Steps

### 1. Check Debug Bundle Contents
```bash
# Latest captures directory
ls -la captures/$(ls captures/ | tail -1)/

# Should contain:
# - table_full.png (full ACR screenshot)  
# - pot.png, hero_stack.png, buttons.png (region crops)
# - ocr.json (raw vs normalized text results)
# - env.json (system environment info)
```

### 2. Validate OCR Pipeline
```bash
# Test offline regression
python -m app.tools.run_offline_ocr_test tests/acr_golden

# Should show:
# ✅ All assertions passed
# REGRESSION TEST PASSED
```

### 3. Verify Configuration Loading
```bash
curl http://localhost:5000/production/test-regions

# Check percentage calculations are correct
# Verify region coordinates within 0.0-1.0 bounds
```

### 4. Monitor State Stabilization
```bash
curl http://localhost:5000/production/test-stabilizer

# Should show debouncing working:
# - reading_1_stable: false  
# - reading_2_stable: true (same value)
# - reading_3_stable: false (different value)
# - reading_4_stable: true (same as reading 3)
```

## Performance Optimization

### CPU Usage Too High
- **Cause**: OCR running too frequently or on oversized images
- **Fix**: Increase FPS delay in `config/acr_runtime.json`
- **Target**: 2-5 FPS with jitter

### Memory Leaks
- **Cause**: CV2 images not released; debug captures accumulating  
- **Fix**: Check `max_debug_sessions` in config; restart periodically
- **Monitor**: Memory usage should be stable over hours

### OCR Accuracy Below 95%
- **Cause**: Poor region selection; wrong PSM mode; lighting changes
- **Fix**: Recalibrate regions; try different PSM values; check image preprocessing
- **Test**: Use regression harness with known good images

## Configuration Tuning

### Common Config Adjustments

```json
{
  "fps_timing": {
    "min_delay": 0.25,  // Increase for less CPU usage
    "max_delay": 0.50   // Wider jitter range
  },
  "timer_detection": {
    "pixel_threshold": 3.0  // Lower = more sensitive
  },
  "ocr_settings": {
    "money_psm": 8,    // Try PSM 8 for better number recognition
    "stack_psm": 7     // PSM 7 usually best for single lines  
  }
}
```

### Region Fine-Tuning
- **Pot Region**: Keep background solid, avoid chip stacks
- **Stack Region**: Include full number, exclude username
- **Button Region**: Cover all action buttons, avoid chat
- **Timer Arc**: Small region around hero position only

## Emergency Recovery

### System Completely Broken
1. **Reset Calibration**: Delete `acr_calibration_results.json`
2. **Clear Debug Data**: `rm -rf captures/*`
3. **Restart Service**: Kill and restart the API server
4. **Recalibrate**: Run auto-calibration from scratch

### ACR UI Changes (Updates/Themes)
1. **Save Current Table**: Capture `table_full.png` manually
2. **Adjust Regions**: Use calibration UI to redefine regions  
3. **Test Regression**: Update `tests/acr_golden/meta.json` expectations
4. **Update Config**: Modify HSV ranges if needed

### False Turn Detection
1. **Check Timer Colors**: Verify HSV ranges match current ACR theme
2. **Tighten Region**: Reduce timer arc area to avoid UI bleed
3. **Increase Threshold**: Raise pixel percentage requirement
4. **Test Manually**: Use color picker on timer screenshots

## Monitoring & Alerts

### Key Metrics to Track
- **OCR Accuracy**: >95% on money/stack fields
- **Response Time**: <5 seconds average
- **Turn Detection**: No false positives in 1 hour
- **Memory Usage**: Stable over 4+ hours
- **Debug File Size**: <100MB per session

### Warning Signs
- OCR results changing rapidly (>10% variation)
- Turn detection triggering outside action windows  
- Response times increasing over time
- Large debug capture files (>50MB)
- Calibration data corruption

This troubleshooting matrix covers 90% of real-world issues. For complex problems, examine the debug bundle artifacts and run the regression test to isolate the root cause.