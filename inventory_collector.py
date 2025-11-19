#!/usr/bin/env python3
"""
IT Helpdesk Inventory Collector
Automatically collects PC specifications and sends them to the IT Helpdesk API.

Compatible with Windows 7/8/10/11.
"""

import platform
import socket
import psutil
import requests
import json
import sys
import time
from datetime import datetime

# For Windows-specific info (optional, using wmi if available)
# Removed manufacturer collection as it will be input manually by admin

def get_cpu_info():
    """Get CPU information."""
    try:
        cpu_info = psutil.cpu_info()
        return cpu_info.brand_raw if cpu_info.brand_raw else f"{cpu_info.count} cores"
    except:
        return "Unknown"

def get_ram_info():
    """Get RAM information in GB."""
    try:
        ram_gb = psutil.virtual_memory().total / (1024 ** 3)
        return f"{ram_gb:.1f} GB"
    except:
        return "Unknown"

def get_os_info():
    """Get OS information."""
    try:
        return platform.platform()
    except:
        return platform.system()

def get_ip_address():
    """Get IP address."""
    try:
        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)
        return ip_address
    except:
        return "Unknown"

def get_hostname():
    """Get hostname."""
    try:
        return platform.node()
    except:
        return "Unknown"

def get_storage_info():
    """Get total storage in GB."""
    try:
        disk = psutil.disk_usage('/')
        total_gb = disk.total / (1024 ** 3)
        return f"{total_gb:.1f} GB"
    except:
        return "Unknown"

def collect_system_info():
    """Collect all system information."""
    return {
        'manufaktur': None,  # Manual input
        'jenis': None,  # Manual input
        'cpu': get_cpu_info(),
        'ram': get_ram_info(),
        'os': get_os_info(),
        'lisensi_windows': None,
        'ipaddress': get_ip_address(),
        'hostname': get_hostname(),
        'credential': None,
        'storage': get_storage_info(),
        'office': None,
        'lisensi_office': None
    }

def send_to_api(email, data, api_url):
    """Send collected data to API."""
    payload = {
        'email': email,
        'data': data,
        'timestamp': datetime.now().isoformat()
    }

    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'IT-Helpdesk-Inventory-Collector/1.0'
    }

    try:
        response = requests.post(api_url, json=payload, headers=headers, timeout=30)
        return response
    except requests.exceptions.RequestException as e:
        return None, str(e)

def main():
    print("=== IT Helpdesk Inventory Collector ===")
    print("This script will collect your PC specifications and send them to the IT Helpdesk system.")
    print()

    # Get API URL (could be hardcoded or prompted)
    api_url = "http://localhost/ithelpdeskwillbes/api/update-main-device"  # Adjust as needed

    # Get user email
    while True:
        email = input("Enter your registered email address: ").strip()
        if '@' in email and '.' in email:
            break
        print("Please enter a valid email address.")

    print("\nCollecting system information...")
    data = collect_system_info()

    print("Collected data:")
    for key, value in data.items():
        print(f"  {key}: {value}")
    print()

    # Confirm before sending
    confirm = input("Send this data to the server? (y/N): ").strip().lower()
    if confirm != 'y':
        print("Operation cancelled.")
        sys.exit(0)

    print("Sending data to server...")
    response, error = send_to_api(email, data, api_url)

    if error:
        print(f"Error sending data: {error}")
        sys.exit(1)

    if response.status_code == 200:
        try:
            result = response.json()
            if result.get('status') == 'success':
                print("✓ Data sent successfully!")
                print(result.get('message', 'Inventory updated.'))
            else:
                print("✗ Server error:", result.get('message', 'Unknown error'))
        except:
            print("✓ Data sent successfully! (Response not in expected format)")
    else:
        print(f"✗ Server error (HTTP {response.status_code}): {response.text}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)
