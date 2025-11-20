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
    """Get CPU information with better formatting."""
    try:
        # Try to get CPU brand name using cpuinfo library
        import cpuinfo
        cpu_info = cpuinfo.get_cpu_info()
        brand = cpu_info.get('brand_raw', '')

        # Clean up common CPU names for better readability
        brand = brand.replace('(R)', '').replace('(TM)', '').replace('CPU', '').strip()
        brand = brand.replace('  ', ' ')  # Remove double spaces

        # Extract key information for AMD Ryzen
        if 'AMD' in brand.upper():
            # Try to extract Ryzen model
            import re
            ryzen_match = re.search(r'Ryzen\s*\d+\s*\d*[A-Za-z]*', brand, re.IGNORECASE)
            if ryzen_match:
                return ryzen_match.group().strip()

        # Extract key information for Intel Core
        if 'Intel' in brand.upper() or 'Core' in brand:
            import re
            core_match = re.search(r'(?:Intel\s*)?(?:Core\s+)?i\d+[-\s]*\d*[A-Za-z]*', brand, re.IGNORECASE)
            if core_match:
                return core_match.group().strip()

        return brand if brand else "Unknown CPU"

    except ImportError:
        # Fallback if cpuinfo is not available
        try:
            # Try using wmic for Windows
            import subprocess
            result = subprocess.check_output(
                'wmic cpu get name /value', shell=True
            ).decode(errors='ignore').strip()

            # Parse the result
            for line in result.split('\n'):
                if line.startswith('Name='):
                    cpu_name = line.split('=', 1)[1].strip()
                    # Clean up the name
                    cpu_name = cpu_name.replace('(R)', '').replace('(TM)', '').replace('CPU', '').strip()
                    return cpu_name

        except:
            pass

        # Final fallback
        try:
            cpu = platform.processor()
            if cpu and cpu.strip():
                return cpu
        except:
            pass

        return "Unknown CPU"


def get_ram_info():
    """Get physical RAM information in GB."""
    try:
        import wmi
        wmi_obj = wmi.WMI()
        
        # Get physical memory modules
        total_ram = 0
        for memory in wmi_obj.Win32_PhysicalMemory():
            capacity = int(memory.Capacity)
            total_ram += capacity
        
        # Convert bytes to GB
        ram_gb = total_ram / (1024 ** 3)
        
        # Round to common RAM sizes
        if ram_gb >= 15 and ram_gb < 17:
            return "16"
        elif ram_gb >= 7 and ram_gb < 9:
            return "8"
        elif ram_gb >= 31 and ram_gb < 33:
            return "32"
        elif ram_gb >= 3 and ram_gb < 5:
            return "4"
        elif ram_gb >= 63 and ram_gb < 65:
            return "64"
        else:
            return f"{ram_gb:.0f}"
    except:
        # Fallback to psutil
        try:
            ram_gb = psutil.virtual_memory().total / (1024 ** 3)
            # Round to nearest common size
            if ram_gb >= 15 and ram_gb < 17:
                return "16"
            elif ram_gb >= 7 and ram_gb < 9:
                return "8"
            else:
                return f"{ram_gb:.0f}"
        except:
            return "Unknown"


def get_os_info():
    """Get OS information using WMI."""
    try:
        import wmi
        wmi_obj = wmi.WMI()
        os_info = wmi_obj.Win32_OperatingSystem()[0]
        os_name = os_info.Caption
        return os_name
    except:
        return "Unknown OS"


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
    """Get physical storage information."""
    try:
        import wmi
        wmi_obj = wmi.WMI()
        
        # Get first physical disk
        disk = wmi_obj.Win32_DiskDrive()[0]
        storage_name = disk.Model  # contoh: "Samsung MZVL2512HCJQ-00B00"
        storage_size_bytes = int(disk.Size)
        storage_size_gb = storage_size_bytes / (1024**3)
        
        # Get interface type to determine if it's NVMe
        interface_type = getattr(disk, 'InterfaceType', '').upper()
        
        # Determine storage type
        storage_type = "HDD"
        storage_name_upper = storage_name.upper()
        
        # Check for NVMe - prioritas tertinggi
        if interface_type == "NVME" or "NVME" in storage_name_upper:
            storage_type = "SSD NVMe M.2"
        # Check for other SSD indicators
        elif any(indicator in storage_name_upper for indicator in ["SSD", "SOLID STATE"]):
            storage_type = "SSD"
        # Check based on common SSD manufacturer names
        elif any(brand in storage_name_upper for brand in ["SAMSUNG", "KINGSTON", "WD", "CRUCIAL", "INTEL", "SANDISK", "ADATA", "SK HYNIX", "MICRON", "TOSHIBA", "SEAGATE BARRACUDA SSD"]):
            # Most modern SSDs from these brands in M.2 form factor are NVMe
            if storage_size_gb >= 240:  # M.2 NVMe typically 256GB+
                storage_type = "SSD NVMe M.2"
            else:
                storage_type = "SSD"
        # Default to HDD if no SSD indicators found
        else:
            storage_type = "HDD"
        
        # Round to common storage sizes
        if storage_size_gb >= 480 and storage_size_gb < 550:
            storage_capacity = "512"
        elif storage_size_gb >= 240 and storage_size_gb < 270:
            storage_capacity = "256"
        elif storage_size_gb >= 120 and storage_size_gb < 135:
            storage_capacity = "128"
        elif storage_size_gb >= 950 and storage_size_gb < 1100:
            storage_capacity = "1024"
        elif storage_size_gb >= 1900 and storage_size_gb < 2100:
            storage_capacity = "2048"
        else:
            storage_capacity = f"{storage_size_gb:.0f}"
        
        storage = f"{storage_type} {storage_capacity} GB"
        return storage
    except Exception as e:
        return f"Unknown (Error: {str(e)})"


def get_device_model():
    """Get device model with full product name lookup."""
    try:
        import wmi
        c = wmi.WMI()

        # List of generic names to avoid
        generic_names = [
            "System Product Name", 
            "Computer System Product", 
            "To Be Filled By O.E.M.", 
            "Default String",
            "INVALID"
        ]

        # First, try to get system model/version (often contains full product name)
        try:
            cs = c.Win32_ComputerSystem()[0]
            model = cs.Model or ""
            
            # Check if model contains useful information
            if model and model.strip() and model not in generic_names:
                # For Lenovo, check if it's a short code like "82K2"
                if len(model) <= 6 and model.isalnum():
                    # Try to get the full name from SystemFamily or other properties
                    try:
                        bios = c.Win32_BIOS()[0]
                        # Some manufacturers put full name in version
                        version = getattr(cs, 'SystemFamily', None)
                        if version and version.strip() and version not in generic_names:
                            return version.strip()
                    except:
                        pass
                    
                    # If still short code, try Win32_ComputerSystemProduct
                    try:
                        product = c.Win32_ComputerSystemProduct()[0]
                        version = product.Version or ""
                        if version and version.strip() and version not in generic_names:
                            manufacturer = cs.Manufacturer or ""
                            return f"{manufacturer} {version}".strip()
                    except:
                        pass
                    
                    # Return with manufacturer prefix
                    manufacturer = cs.Manufacturer or ""
                    return f"{manufacturer} {model}".strip()
                else:
                    # Model already contains full name
                    return model.strip()
        except:
            pass

        # Try Win32_ComputerSystemProduct
        try:
            product = c.Win32_ComputerSystemProduct()[0]
            
            # Try Version first (often contains full product name)
            version = product.Version or ""
            if version and version.strip() and version not in generic_names:
                cs = c.Win32_ComputerSystem()[0]
                manufacturer = cs.Manufacturer or ""
                return f"{manufacturer} {version}".strip()
            
            # Try Name
            name = product.Name or ""
            if name and name.strip() and name not in generic_names:
                cs = c.Win32_ComputerSystem()[0]
                manufacturer = cs.Manufacturer or ""
                return f"{manufacturer} {name}".strip()
        except:
            pass

        # Fallback to Manufacturer + Model
        try:
            cs = c.Win32_ComputerSystem()[0]
            manufacturer = cs.Manufacturer or ""
            model = cs.Model or ""
            full_name = f"{manufacturer} {model}".strip()
            
            if full_name and not any(generic in full_name for generic in generic_names):
                return full_name
        except:
            pass

        return "Unknown Device"
        
    except Exception as e:
        return f"Unknown Device (Error: {str(e)})"


def collect_system_info():
    """Collect all system information."""
    return {
        # jenis, lisensi_windows, credential, office, lisensi_office
        # will be filled manually by admin (role 1) through the web interface
        'manufaktur': get_device_model(),
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
        'X-API-Key': API_KEY,
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
