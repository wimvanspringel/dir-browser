#!/usr/bin/env python3
"""
Debug script to monitor directory server health and performance
"""

import requests
import time
import json
from datetime import datetime

def check_server_health():
    """Check server health status"""
    try:
        response = requests.get('http://localhost:5000/api/health', timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Server Status: {data['status']}")
            print(f"   Active Requests: {data['active_requests']}")
            print(f"   Oldest Request Age: {data['oldest_request_age']}")
            print(f"   Server Uptime: {data['server_uptime']}")
            return True
        else:
            print(f"❌ Server returned status code: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to server: {e}")
        return False

def check_active_requests():
    """Check for stuck requests"""
    try:
        response = requests.get('http://localhost:5000/api/debug/requests', timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"\n📊 Active Requests: {data['total_active']}")
            if data['active_requests']:
                print("   Stuck requests:")
                for req in data['active_requests']:
                    print(f"     - {req['id']} (age: {req['age']})")
            else:
                print("   No active requests")
            return data['total_active']
        else:
            print(f"❌ Debug endpoint returned status code: {response.status_code}")
            return 0
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to debug endpoint: {e}")
        return 0

def monitor_server(interval=10):
    """Continuously monitor server health"""
    print(f"🔍 Starting server monitoring (checking every {interval} seconds)")
    print("Press Ctrl+C to stop monitoring\n")
    
    try:
        while True:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"\n[{timestamp}] Checking server health...")
            
            if check_server_health():
                active_count = check_active_requests()
                
                # Alert if there are stuck requests
                if active_count > 5:
                    print(f"⚠️  WARNING: {active_count} active requests detected!")
                elif active_count > 0:
                    print(f"ℹ️  {active_count} active requests")
                else:
                    print("✅ No stuck requests")
            
            print("-" * 50)
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print("\n🛑 Monitoring stopped")

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--once':
        # Single check mode
        check_server_health()
        check_active_requests()
    else:
        # Continuous monitoring mode
        monitor_server() 