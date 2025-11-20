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

# ============================================
# CONFIGURATION - EDIT BAGIAN INI
# ============================================

# API endpoint URL - sesuaikan dengan server CI4 Anda
API_URL = "http://192.168.0.250:8000/api/update-main-device"

# API Key untuk autentikasi - HARUS SAMA dengan yang ada di .env file CI4
API_KEY = "VyyLY87xmeQ712gGkWR72YNDhFHFbfR6"

# ============================================
# JANGAN EDIT DIBAWAH INI
# ============================================


def get_cpu_info():
    """Get CPU information."""
    try:
        # Try to get CPU brand name
        import cpuinfo
        cpu_info = cpuinfo.get_cpu_info()
        return cpu_info['brand_raw']
    except:
        try:
            # Fallback to platform.processor()
            cpu = platform.processor()
            if cpu and cpu.strip():
                return cpu
            # If still empty, try psutil
            return f"{psutil.cpu_count(logical=False)} cores @ {psutil.cpu_freq().max:.0f}MHz"
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
    """Get total storage in GB from all partitions."""
    try:
        total_storage = 0
        partitions = psutil.disk_partitions()
        
        for partition in partitions:
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                total_storage += usage.total
            except PermissionError:
                # Skip partitions we can't access
                continue
        
        total_gb = total_storage / (1024 ** 3)
        return f"{total_gb:.1f} GB"
    except:
        return "Unknown"


def collect_system_info():
    """Collect all system information."""
    return {
        # Removed manufaktur, jenis, lisensi_windows, credential, office, lisensi_office
        # These will be filled manually by admin (role 1) through the web interface
        'cpu': get_cpu_info(),
        'ram': get_ram_info(),
        'os': get_os_info(),
        'ipaddress': get_ip_address(),
        'hostname': get_hostname(),
        'storage': get_storage_info()
    }


def send_to_api(email, data):
    """Send collected data to API."""
    # Structure payload as expected by API
    payload = {
        'email': email,
        'data': data,
        'timestamp': datetime.now().isoformat()
    }

    # Headers with API Key
    headers = {
        'Content-Type': 'application/json',
        'X-API-Key': API_KEY,  # Now accessible because it's defined at module level
        'User-Agent': 'IT-Helpdesk-Inventory-Collector/1.0'
    }

    try:
        response = requests.post(API_URL, json=payload, headers=headers, timeout=30)
        return response, None
    except requests.exceptions.ConnectionError:
        return None, "Connection error: Cannot connect to server. Please check if the server is running."
    except requests.exceptions.Timeout:
        return None, "Timeout error: Server took too long to respond."
    except requests.exceptions.RequestException as e:
        return None, f"Request error: {str(e)}"


def main():
    print("=" * 60)
    print("=== IT Helpdesk Inventory Collector ===".center(60))
    print("=" * 60)
    print()
    print("This script will collect your PC specifications and send them")
    print("to the IT Helpdesk system.")
    print()
    
    # Check if API_KEY is configured
    if not API_KEY or API_KEY == "your-api-key-here":
        print("⚠ ERROR: API Key is not configured!")
        print("Please contact your IT administrator to get the API Key.")
        print("Then edit this script and update the API_KEY variable.")
        input("\nPress Enter to exit...")
        sys.exit(1)

    # Get user email
    print("Please enter your registered email address.")
    while True:
        email = input("Email: ").strip()
        if '@' in email and '.' in email:
            break
        print("⚠ Please enter a valid email address.")
        print()

    print()
    print("Collecting system information...")
    print()
    
    try:
        data = collect_system_info()
    except Exception as e:
        print(f"✗ Error collecting system information: {e}")
        input("\nPress Enter to exit...")
        sys.exit(1)

    # Display collected data
    print("Collected data:")
    print("-" * 60)
    for key, value in data.items():
        if value is not None:
            print(f"  {key:20s}: {value}")
    print("-" * 60)
    print()

    # Confirm before sending
    confirm = input("Send this data to the server? (y/N): ").strip().lower()
    if confirm != 'y':
        print("Operation cancelled.")
        input("\nPress Enter to exit...")
        sys.exit(0)

    print()
    print("Sending data to server...")
    
    response, error = send_to_api(email, data)

    if error:
        print(f"✗ Error: {error}")
        print()
        print("Troubleshooting:")
        print("  1. Check if CI4 server is running")
        print("  2. Verify the API URL is correct")
        print("  3. Check your network connection")
        input("\nPress Enter to exit...")
        sys.exit(1)

    # Handle response
    print()
    if response.status_code == 200 or response.status_code == 201:
        try:
            result = response.json()
            if result.get('status') == 'success':
                print("✓ SUCCESS: Data sent successfully!")
                print(f"✓ {result.get('message', 'Inventory updated.')}")
                print()
                print("Your PC information has been recorded in the system.")
            else:
                print("✗ Server returned an error:")
                print(f"  {result.get('message', 'Unknown error')}")
        except:
            print("✓ SUCCESS: Data sent successfully!")
            print("(Server response format was unexpected, but data was received)")
            
    elif response.status_code == 401:
        print("✗ AUTHENTICATION ERROR (401)")
        print("  Invalid API Key!")
        print()
        print("Please check:")
        print("  1. API_KEY in this script matches the one in CI4 .env file")
        print("  2. Contact IT administrator if you need a new API Key")
        
    elif response.status_code == 404:
        print("✗ ERROR (404): Email not found in database")
        print()
        print("Please make sure:")
        print("  1. You have registered an account in the IT Helpdesk system")
        print("  2. The email you entered is correct")
        
    elif response.status_code == 422:
        print("✗ VALIDATION ERROR (422)")
        try:
            result = response.json()
            print(f"  {result.get('message', 'Invalid data format')}")
            if 'errors' in result:
                for field, error in result['errors'].items():
                    print(f"  - {field}: {error}")
        except:
            print(f"  {response.text}")
            
    else:
        print(f"✗ SERVER ERROR (HTTP {response.status_code})")
        try:
            result = response.json()
            print(f"  {result.get('message', 'Unknown error')}")
        except:
            print(f"  Response: {response.text[:200]}")

    print()
    input("Press Enter to exit...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ An unexpected error occurred: {e}")
        print("\nPlease contact IT support if this problem persists.")
        input("\nPress Enter to exit...")
        sys.exit(1)
