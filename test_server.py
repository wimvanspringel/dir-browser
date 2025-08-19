#!/usr/bin/env python3
"""
Test script to stress test the directory server and identify hanging issues
"""

import requests
import threading
import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed

def test_single_request(endpoint, timeout=10):
    """Test a single request to an endpoint"""
    try:
        start_time = time.time()
        response = requests.get(f'http://localhost:5000{endpoint}', timeout=timeout)
        duration = time.time() - start_time
        
        if response.status_code == 200:
            print(f"✅ {endpoint} - {response.status_code} ({duration:.3f}s)")
            return True
        else:
            print(f"❌ {endpoint} - {response.status_code} ({duration:.3f}s)")
            return False
    except requests.exceptions.Timeout:
        print(f"⏰ {endpoint} - TIMEOUT after {timeout}s")
        return False
    except requests.exceptions.RequestException as e:
        print(f"💥 {endpoint} - ERROR: {e}")
        return False

def test_slideshow_requests():
    """Test slideshow functionality with multiple concurrent requests"""
    print("\n🎬 Testing slideshow functionality...")
    
    # Test endpoints that might cause hangs
    endpoints = [
        '/api/health',
        '/api/directory?path=/mnt/nassys/$SystemRestore/$bin/temp/SystemCache',
        '/api/slideshow?path=/mnt/nassys/$SystemRestore/$bin/temp/SystemCache/8T/abby%201',
        '/api/image/0001.jpg?dir=/mnt/nassys/$SystemRestore/$bin/temp/SystemCache/8T/abby%201',
        '/api/image/0002.jpg?dir=/mnt/nassys/$SystemRestore/$bin/temp/SystemCache/8T/abby%201',
        '/api/image/0003.jpg?dir=/mnt/nassys/$SystemRestore/$bin/temp/SystemCache/8T/abby%201',
    ]
    
    # Test with different concurrency levels
    for concurrency in [1, 5, 10]:
        print(f"\n🔄 Testing with {concurrency} concurrent requests...")
        
        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            futures = []
            for endpoint in endpoints:
                for _ in range(2):  # Make 2 requests per endpoint
                    future = executor.submit(test_single_request, endpoint)
                    futures.append(future)
            
            # Wait for all requests to complete
            completed = 0
            failed = 0
            for future in as_completed(futures, timeout=30):
                try:
                    result = future.result(timeout=5)
                    if result:
                        completed += 1
                    else:
                        failed += 1
                except Exception as e:
                    print(f"💥 Future error: {e}")
                    failed += 1
            
            print(f"📊 Results: {completed} completed, {failed} failed")

def test_large_directory():
    """Test browsing large directories that might cause hangs"""
    print("\n📁 Testing large directory browsing...")
    
    # Test directories that might have many files
    test_paths = [
        '/mnt/nassys/$SystemRestore/$bin/temp/SystemCache',
        '/mnt/nassys/$SystemRestore/$bin/temp/SystemCache/8T',
        '/mnt/nassys/$SystemRestore/$bin/temp/SystemCache/GLAM',
    ]
    
    for path in test_paths:
        endpoint = f'/api/directory?path={path}'
        print(f"\n🔍 Testing directory: {path}")
        test_single_request(endpoint, timeout=15)

def test_concurrent_slideshows():
    """Test multiple slideshow requests simultaneously"""
    print("\n🎭 Testing concurrent slideshows...")
    
    def slideshow_test():
        # Start slideshow
        response = requests.get('http://localhost:5000/api/slideshow?path=/mnt/nassys/$SystemRestore/$bin/temp/SystemCache/8T/abby%201', timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data['images']:
                # Request first few images
                for i in range(min(5, len(data['images']))):
                    img_name = data['images'][i]['name']
                    img_url = f'/api/image/{img_name}?dir=/mnt/nassys/$SystemRestore/$bin/temp/SystemCache/8T/abby%201'
                    test_single_request(img_url, timeout=5)
    
    # Run multiple slideshow tests concurrently
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(slideshow_test) for _ in range(3)]
        
        for future in as_completed(futures, timeout=60):
            try:
                future.result(timeout=30)
            except Exception as e:
                print(f"💥 Slideshow test error: {e}")

def main():
    """Run all tests"""
    print("🧪 Starting server stress tests...")
    print("Make sure the directory server is running on http://localhost:5000")
    
    # Test basic functionality
    print("\n🔧 Testing basic endpoints...")
    test_single_request('/api/health')
    test_single_request('/api/debug/requests')
    
    # Test directory browsing
    test_large_directory()
    
    # Test slideshow functionality
    test_slideshow_requests()
    
    # Test concurrent slideshows
    test_concurrent_slideshows()
    
    print("\n✅ All tests completed!")

if __name__ == '__main__':
    main() 