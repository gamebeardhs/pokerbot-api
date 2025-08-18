
#!/usr/bin/env python3
import requests
import time
import json
from datetime import datetime

def monitor_database_performance():
    while True:
        try:
            # Get stats
            start_time = time.time()
            response = requests.get("http://localhost:5000/database/database-stats", timeout=5)
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                stats = response.json()
                timestamp = datetime.now().strftime("%H:%M:%S")
                print(f"[{timestamp}] Status: {stats['status']} | "
                      f"Situations: {stats['total_situations']:,} | "
                      f"Avg Query: {stats['average_query_time_ms']:.1f}ms | "
                      f"API Response: {response_time:.1f}ms")
            else:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] API Error: {response.status_code}")
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Monitor Error: {e}")
        
        time.sleep(30)  # Check every 30 seconds

if __name__ == "__main__":
    print("🔍 Database Performance Monitor Started")
    print("Press Ctrl+C to stop")
    monitor_database_performance()
    