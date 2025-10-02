# Import required libraries
import network, time, socket

class WlanManager:
    """Manages WLAN (Wi-Fi) connections for the device."""
    def __init__(self):
        """
        Initializes the WlanManager, deactivating and then activating the WLAN interface.
        """
        self.wlan = network.WLAN(network.STA_IF)
        self.was_connected_before = False
        if self.wlan.active():
            self.wlan.active(False)
            time.sleep(5)
        
        self.wlan.active(True)

    def connect(self, ssid, psk):
        """
        Attempts to connect to a WLAN network with the given SSID and PSK.

        Args:
            ssid (str): The SSID of the Wi-Fi network.
            psk (str): The password (pre-shared key) for the Wi-Fi network.
        """
        if self.wlan.isconnected():
            return

        self.wlan.connect(ssid, psk)

    def is_connected_boolean(self):
        """
        Checks if the device is currently connected to a WLAN network.

        Returns:
            bool: True if connected, False otherwise.
        """
        if self.wlan.isconnected():
            return True
        else:
            return False

    def is_connected(self):
        """
        Checks the WLAN connection status and returns an error code if not connected.

        Returns:
            tuple: A tuple containing an error code (or "OK") and a list of error messages (or None).
        """
        if self.wlan.isconnected():
            self.was_connected_before = True
            return "OK", None
        elif self.was_connected_before:
            return "2302", ["Connection to the WLAN lost!",
                            "Please make sure that your WLAN is in",
                            "a close enough range for stable",
                            "operation. Trying to reconnect soon."]
        else:
            return "2301", ["Connection to WLAN failed!",
                            "Please make sure that your WLAN is in",
                            "range, your SSID and PSK are correct,",
                            "and the router operates at 2.4GHz!"]

    def get_ip(self):
        """
        Retrieves the IP address of the device if connected to WLAN.

        Returns:
            str or None: The IP address as a string, or None if not connected.
        """
        return self.wlan.ifconfig()[0] if self.wlan.isconnected() else None

    def device_online(self):
        """
        Checks if the device has an active internet connection by attempting to reach a public IP.

        Returns:
            tuple: A tuple containing an error code (or "OK") and a list of error messages (or None).
        """
        try:
            addr = socket.getaddrinfo("1.1.1.1", 53)[0][-1]
            socket.socket().connect(addr)
            return "OK", None
        
        except Exception as e:
            return "2401", ["No internet conenction!",
                        "Although your WLAN works, there is no",
                        "internet connection. Please restart your",
                        "WLAN router and check for an outage."]
        
    def close(self):
        """
        Disconnects from the WLAN and deactivates the WLAN interface.
        """
        if self.wlan.isconnected():
            self.wlan.disconnect()
        self.wlan.active(False)

