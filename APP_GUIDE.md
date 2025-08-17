# 🃏 Poker Advisory App - Complete Guide

Your enhanced poker advisory service is running at **http://localhost:5000**

## 🌐 **Web Interfaces**

### **Main Dashboard**: http://localhost:5000/
- Overview of all app features and status

### **API Documentation**: http://localhost:5000/docs
- Interactive FastAPI documentation
- Test all endpoints directly in browser
- Shows request/response examples

### **Training Interface**: http://localhost:5000/training/
- Interactive card template management
- Create and test card templates
- View training statistics

## 🔧 **API Endpoints**

### **Health Check**
```bash
curl http://localhost:5000/health
```
Returns system status and component health

### **GTO Decision Request**
```bash
curl -X POST http://localhost:5000/gto/decision \
  -H "Content-Type: application/json" \
  -d '{
    "hero_cards": ["As", "Kh"],
    "board_cards": ["Qd", "Jc", "Ts"],
    "pot_size": 100,
    "bet_size": 50,
    "position": "BTN",
    "action": "call"
  }'
```

### **Scrape ACR Table**
```bash
curl -X POST http://localhost:5000/scraper/acr/analyze \
  -H "Content-Type: multipart/form-data" \
  -F "image=@your_screenshot.png"
```

### **Training Stats**
```bash
curl http://localhost:5000/training/stats
```

## 🎯 **Command Line Testing**

### **Interactive Testing Menu**
```bash
python test_yourself.py
```
- View all 52 templates
- Test template matching
- Test dual recognition
- Generate training data
- Create new templates

### **Complete Template Extraction**
```bash
python extract_acr_templates.py
```
- Auto-extracts all 52 card templates
- Fallback to open source if ACR not found

### **Direct API Tests**
```bash
# Check all components
curl http://localhost:5000/health

# Test training system
curl http://localhost:5000/training/stats

# View main interface
curl http://localhost:5000/
```

## 📊 **Current System Status**

✅ **Complete**: All 52 card templates loaded  
✅ **Active**: Enhanced GTO decision engine  
✅ **Calibrated**: ACR scraper with 5 regions  
✅ **Ready**: Dual recognition system  
✅ **Available**: Data augmentation (100+ variants per card)  

## 🔒 **Authentication**

For production use, add authentication header:
```bash
curl -H "Authorization: Bearer your-token-here" http://localhost:5000/gto/decision
```

## 🎮 **WebSocket Live Updates**

Connect to real-time table state streaming:
```javascript
const ws = new WebSocket('ws://localhost:5000/ws/table/your-table-id');
ws.onmessage = (event) => {
    console.log('Table update:', JSON.parse(event.data));
};
```

## 🛠 **Development**

The app automatically restarts when you make code changes. To manually restart:
```bash
# App is managed by Replit workflows - just refresh browser
```

## 📈 **Performance**

- **GTO Decisions**: Sub-second response time
- **Card Recognition**: Dual template+OCR system
- **Template Matching**: 100% coverage for all 52 cards
- **Concurrent Users**: WebSocket support for multiple connections

Your poker advisory system is fully operational and ready for real poker analysis!