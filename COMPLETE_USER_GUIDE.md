# 🃏 Complete Poker Advisory App Guide

## 🚀 Quick Start (5 Minutes)

### **Step 1: Installation**
```bash
# Download the project and run:
python start_app.py
```
That's it! The app installs dependencies automatically and opens at http://localhost:5000

---

## 🎯 What You Can Do

### **1. Test GTO Decisions (Most Useful)**
**URL: http://localhost:5000/gui**
- Enter your cards (e.g., "Ah", "Kd") 
- Set board cards, pot size, position
- Get optimal poker advice instantly

### **2. Live ACR Scraping (Advanced)**  
**URL: http://localhost:5000/manual/analyze**
- Works with ACR poker client
- Takes screenshot and analyzes your current hand
- Requires calibration first

### **3. Train Card Recognition (Optional)**
**URL: http://localhost:5000/training-interface**  
- View the 52 card templates
- Test card recognition accuracy
- Create new templates if needed

---

## 📋 Step-by-Step Walkthrough

### **Getting Your First GTO Decision**

1. **Start the app**: `python start_app.py`
2. **Open your browser**: Go to http://localhost:5000/gui
3. **Enter a hand**:
   - Hero Cards: `As`, `Kh`
   - Board: `Qd`, `Jc`, `Ts` (leave empty for preflop)
   - Position: Select your position
   - Pot Size: Enter current pot
4. **Click "Get GTO Decision"**
5. **Read the advice**: Optimal action, bet size, reasoning

### **Setting Up ACR Live Analysis** 

1. **Open ACR poker client** and sit at a table
2. **Run calibration**:
   ```bash
   python acr_complete_calibrator.py
   ```
3. **Follow prompts** to mark card areas, pot, buttons
4. **Test it**: Go to http://localhost:5000/gui and click "Analyze Current ACR Hand"

### **Understanding Your Results**

**GTO Decision Format**:
- **Action**: Fold, Check, Call, Bet, Raise
- **Size**: Bet/raise amount (e.g., 0.75x pot)
- **Confidence**: How strong the recommendation is
- **Equity**: Your winning chances
- **Reasoning**: Why this action is optimal

---

## 🛠 Core Features Explained

### **What Works Out of the Box**
✅ **GTO Analysis** - Mathematical poker advice  
✅ **Card Recognition** - 52 card template system  
✅ **Position Analysis** - Knows all poker positions  
✅ **Board Texture** - Understands wet/dry boards  
✅ **Multiple Players** - 2-6 player games  

### **What Requires Setup**
⚙️ **ACR Live Scraping** - Needs calibration  
⚙️ **Advanced CFR** - Install OpenSpiel for true GTO  
⚙️ **Custom Templates** - For non-standard card designs  

---

## 🎮 Most Common Use Cases

### **1. Study Session**
- Open `/gui` interface
- Input interesting hands from your session
- Compare your decisions to GTO advice
- Learn optimal bet sizes and frequencies

### **2. Live Play Assistant**  
- Set up ACR calibration once
- Use "Analyze Current ACR Hand" button
- Get real-time advice on difficult decisions
- *Note: Check your site's rules on decision aids*

### **3. Training Card Recognition**
- Use `/training-interface` 
- Test recognition on your poker site's cards
- Create templates for new card designs
- Improve accuracy for better live analysis

---

## 📊 Technical Details

### **API Endpoints (For Developers)**
- `GET /` - Service info
- `GET /health` - System status  
- `POST /decide` - GTO analysis (requires auth token)
- `GET /gui` - Web interface
- `POST /manual/analyze` - Screenshot analysis
- `GET /training-interface` - Card trainer

### **Authentication**
Most endpoints require a bearer token. Default token: `demo-token-123`

```bash
curl -H "Authorization: Bearer demo-token-123" \
     -H "Content-Type: application/json" \
     -d '{"hero_hole":["As","Kh"],"board":[],"pot_size":15}' \
     http://localhost:5000/decide
```

### **Files You Can Ignore**
- `test_*.py` - Developer testing scripts
- `extract_*.py` - One-time template creation
- `debug_*.png` - Calibration screenshots
- `attached_assets/` - Development artifacts

### **Files That Matter**
- `start_app.py` - **Main launcher**
- `acr_calibration_results.json` - ACR setup data
- `app/` - Core application code
- `training_data/templates/` - Card recognition templates

---

## 🔧 Troubleshooting

### **"Module not found" errors**
```bash
# Try manual installation:
pip install fastapi uvicorn pillow numpy requests
python start_app.py
```

### **"No OpenSpiel" warning**
This is normal! The app works without OpenSpiel using mathematical approximations.

### **Port already in use**  
```bash
python -m uvicorn app.api.main:app --host 0.0.0.0 --port 8000
```
Then visit http://localhost:8000

### **ACR calibration fails**
1. Make sure ACR is running and visible
2. Use a standard table layout (not mini-view)
3. Ensure cards are clearly visible
4. Run `python acr_complete_calibrator.py` again

### **Card recognition is inaccurate**
1. Visit http://localhost:5000/training-interface
2. Test current templates
3. Create new templates for your card design
4. Re-run recognition tests

---

## 🎯 Success Checklist

After setup, you should be able to:

- [ ] Get GTO advice for any poker hand
- [ ] Use the web interface at `/gui`
- [ ] See all 52 card templates in training interface
- [ ] Get responses from `/health` endpoint  
- [ ] (Optional) Analyze live ACR hands after calibration

---

## 💡 Pro Tips

1. **Study Mode**: Input challenging hands from your sessions to learn GTO play
2. **Position Matters**: Same cards play differently from UTG vs Button
3. **Stack Depths**: 100bb vs 20bb strategies are very different  
4. **Board Texture**: Wet boards (QJT) require different play than dry (A72)
5. **Multiple Solutions**: Sometimes GTO allows both betting and checking

---

## 🚨 Important Notes

- **Poker Site Rules**: Check if your site allows decision assistance tools
- **Study Tool**: Best used for learning, not as a crutch during play
- **Mathematical Advice**: GTO is optimal but may not be best against weak opponents
- **Windows Compatible**: Works on Windows desktop without complex setup

---

**Ready to improve your poker game? Start with `python start_app.py` and visit http://localhost:5000/gui!**