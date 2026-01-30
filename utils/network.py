import subprocess
import platform
import logging
import re
from config.settings import OFFICE_WIFI_SSID

logger = logging.getLogger(__name__)

def is_connected_to_office_network():
    """
    Checks if the device is connected to the specific Office Wi-Fi SSID.
    Supports Windows (netsh) and Linux (nmcli/iwgetid).
    """
    if not OFFICE_WIFI_SSID:
        logger.warning("OFFICE_WIFI_SSID is not set in .env. Skipping check.")
        return True # Fail-open for development if env is missing

    current_ssid = None
    os_type = platform.system()

    try:
        if os_type == "Windows":
            # Windows: Parse 'netsh wlan show interfaces'
            output = subprocess.check_output("netsh wlan show interfaces", shell=True).decode('utf-8', errors='ignore')
            # Look for "SSID                   : MyWifiName"
            match = re.search(r"^\s*SSID\s*:\s*(.*)$", output, re.MULTILINE)
            if match:
                current_ssid = match.group(1).strip()
                
        elif os_type == "Linux":
            # Linux: Try iwgetid first (common in Ubuntu/Mint)
            try:
                output = subprocess.check_output("iwgetid -r", shell=True).decode('utf-8').strip()
                current_ssid = output
            except subprocess.CalledProcessError:
                # Fallback to nmcli
                output = subprocess.check_output("nmcli -t -f active,ssid dev wifi | grep '^yes'", shell=True).decode('utf-8')
                current_ssid = output.split(':')[1].strip() if ':' in output else None

        logger.info(f"Network Check: Required='{OFFICE_WIFI_SSID}', Connected='{current_ssid}'")
        return current_ssid == OFFICE_WIFI_SSID

    except Exception as e:
        logger.error(f"Network Check Failed: {e}")
        return False