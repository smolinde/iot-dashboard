# Import required libraries and SD card driver
import os, ure, json
from machine import Pin, SPI
from drivers.sdcard import SDCard

class FileManager:
    """Manages file system operations, including SD card access and configuration validation."""
    def __init__(self):
        """
        Initializes the FileManager, setting up configuration storage and regex for UUID validation.
        """
        self.configuration = {}
        self.uuid_regex = ure.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")
        self.sd = None
        
    def open_sd_card(self):
        """
        Attempts to open and mount the SD card. If already mounted, it verifies access.

        Returns:
            tuple: A tuple containing an error code (or "OK") and a list of error messages (or None).
        """
        try:
            os.listdir("/sd")
            return "OK", None
        except Exception:
            try:
                self.sd = SDCard(SPI(1, baudrate=2000000, sck=Pin(21), mosi=Pin(39), miso=Pin(40)), Pin(38))
                os.mount(self.sd, "/sd")
                return "OK", None

            except Exception:
                return "1101", ["SD card not found!",
                                "The SD card is either not inserted or",
                                "has wrong format, it should be",
                                "formatted as a FAT32 filesystem!"]

    def validate_sd_card_contents(self):
        """
        Validates the contents of the SD card, checking for the configuration file and other assets.

        Returns:
            tuple: A tuple containing an error code (or "OK") and a list of error messages (or None).
        """
        if "configuration.json" not in os.listdir("/sd"):
            return "1102", ["Missing configuration file!",
                            "Please make sure that the file with",
                            "the name configuration.json is",
                            "present on your SD card."]
        
        try:
            with open("/sd/configuration.json", "r") as f:
                self.configuration = json.load(f)
        except Exception:
            return "1103", ["Failed to load the configuration file!",
                            "The file exists, but there is a problem",
                            "with the contents and/or the structure.",
                            "Please adjust the configuration file."]
        
        if self.__count_station_icons() > 3:
            return "1104", ["More than 3 station icons found!",
                            "To improve startup time, it is not",
                            "allowed to store more than 3 station",
                            "icons in the station_icons folder."]
        
        if not self.__validate_station_icons():
            return "1105", ["Invalid custom station icon(s)!",
                            "Your custom gas station icons(s) don\\'t",
                            "match the expected size or are formatted",
                            "incorrectly. Expected size: 64x64 pixels"]
        
        for name in dir(self):
            if name.startswith("_FileManager__check"):
                configuration_checker = getattr(self, name)
                if callable(configuration_checker):
                    error_code, error_text = configuration_checker()
                    if error_code != "OK":
                        return error_code, error_text

        return "OK", None

    def __is_valid_uuid(self, uuid):
        """
        Checks if a given string is a valid UUID format.

        Args:
            uuid (str): The string to validate.

        Returns:
            bool: True if the string is a valid UUID, False otherwise.
        """
        return self.uuid_regex.match(uuid) is not None

    def __count_station_icons(self):
        """
        Counts the number of .rgb666 station icon files on the SD card.

        Returns:
            int: The number of station icon files found.
        """
        try:
            files = os.listdir("/sd/station_icons")
        except Exception:
            return 0
        
        rgb666_files = [f for f in files if f.endswith(".rgb666")]
        return len(rgb666_files)
    
    def __validate_station_icons(self):
        """
        Validates the size of custom station icon files.

        Returns:
            bool: True if all custom station icons are valid, False otherwise.
        """
        try:
            files = os.listdir("/sd/station_icons")
        except Exception:
            return True

        for f in files:
            if f.endswith(".rgb666"):
                path = "/sd/station_icons/" + f
                try:
                    size = os.stat(path)[6]
                    if size != 64 * 64 * 3:
                        return False
                except Exception:
                    return False
        
        return True
    
    def __check_wlan_ssid(self):
        """
        Checks if the WLAN SSID in the configuration is valid.

        Returns:
            tuple: An error code (or "OK") and a list of error messages (or None).
        """
        wlan_ssid = self.configuration.get("wlan_ssid")
        if isinstance(wlan_ssid, str) and wlan_ssid.strip() and len(wlan_ssid) <= 32:
            return "OK", None
        else:
            return "1201", ["The WLAN SSID is not valid!",
                            "Please provide a valid WLAN SSID in",
                            "the configuration.json file!"]

    def __check_wlan_psk(self):
        """
        Checks if the WLAN password (PSK) in the configuration is valid.

        Returns:
            tuple: An error code (or "OK") and a list of error messages (or None).
        """
        wlan_psk = self.configuration.get("wlan_psk")
        if isinstance(wlan_psk, str) and wlan_psk.strip() and len(wlan_psk) and 8 <= len(wlan_psk) <= 63:
            return "OK", None
        else:
            return "1202", ["The WLAN password is not valid!",
                            "Please provide a valid WLAN password",
                            "in the configuration.json file!"]

    def __check_tankerkoenig_api_key(self):
        """
        Checks if the Tankerkoenig API key in the configuration is a valid UUID.

        Returns:
            tuple: An error code (or "OK") and a list of error messages (or None).
        """
        tankerkoenig_api_key = self.configuration.get("tankerkoenig_api_key")
        if isinstance(tankerkoenig_api_key, str) and tankerkoenig_api_key.strip() and self.__is_valid_uuid(tankerkoenig_api_key):
            return "OK", None
        else:
            return "1203", ["The Tankerkoenig API key is not valid!",
                            "Please provide a valid API key in the",
                            "configuration.json file!"]

    def __check_station_ids(self):
        """
        Checks if the station IDs in the configuration are valid and unique.

        Returns:
            tuple: An error code (or "OK") and a list of error messages (or None).
        """
        station_ids = self.configuration.get("station_ids")
        if (
            isinstance(station_ids, list)
            and len(station_ids) == 3
            and all(isinstance(i, str) and self.__is_valid_uuid(i) and i.strip() for i in station_ids)
        ):
            if any(station_ids.count(x) > 1 for x in station_ids):
                return "1205", ["The station ID\\'s are not unique!",
                            "Please provide three unique station ID\\'s",
                            "in the configuration.json file!"]
            else:
                return "OK", None
        else:
            return "1204", ["The station ID\\'s are not valid!",
                            "Please provide three valid station ID\\'s",
                            "as a list in the configuration.json file!"]
        
    def __check_station_labels(self):
        """
        Checks if the station labels in the configuration are valid (3x3 list of strings).

        Returns:
            tuple: An error code (or "OK") and a list of error messages (or None).
        """
        valid_labels = True
        station_labels = self.configuration.get("station_labels")
        if not isinstance(station_labels, list) or len(station_labels) != 3:
            valid_labels = False

        for row in station_labels:
            if not isinstance(row, list) or len(row) != 3:
                valid_labels = False
                break

            for item in row:
                if not isinstance(item, str):
                    valid_labels = False
                    break
            
            if not valid_labels:
                break

        if valid_labels:
            return "OK", None
        else:
            return "1206", ["The station labels are not valid!",
                            "Please provide valid station labels as a",
                            "3x3 list in the configuration.json file!"]

    def __check_fuel_type(self):
        """
        Checks if the fuel type in the configuration is valid (e5, e10, or diesel).

        Returns:
            tuple: An error code (or "OK") and a list of error messages (or None).
        """
        fuel_type = self.configuration.get("fuel_type")
        if fuel_type in ("e5", "e10", "diesel"):
            return "OK", None
        else:
            return "1207", ["The fuel type is not valid!",
                            "Please provide a valid fuel type in",
                            "the configuration.json file!",
                            "Valid fuel types: e5, e10, diesel"]

    def __check_weather_lat(self):
        """
        Checks if the weather latitude in the configuration is valid (-90 to 90).

        Returns:
            tuple: An error code (or "OK") and a list of error messages (or None).
        """
        weather_lat = self.configuration.get("weather_lat")
        if isinstance(weather_lat, (int, float)) and weather_lat > -90. and weather_lat < 90.:
            return "OK", None
        else:
            return "1208", ["The latitude is not valid!",
                            "Please provide a valid latitude in",
                            "the configuration.json file!",
                            "Valid latitudes are between -90 and 90"]

    def __check_weather_long(self):
        """
        Checks if the weather longitude in the configuration is valid (-180 to 180).

        Returns:
            tuple: An error code (or "OK") and a list of error messages (or None).
        """
        weather_long = self.configuration.get("weather_long")
        if isinstance(weather_long, (int, float)) and weather_long > -180. and weather_long < 180.:
            return "OK", None
        else:
            return "1209", ["The longitude is not valid!",
                            "Please provide a valid longitude in",
                            "the configuration.json file!",
                            "Valid longitudes are between -180 and 180"]
    
    def __check_automatic_updates(self):
        """
        Checks if the automatic updates flag in the configuration is a valid boolean.

        Returns:
            tuple: An error code (or "OK") and a list of error messages (or None).
        """
        automatic_updates = self.configuration.get("automatic_updates")
        if isinstance(automatic_updates, bool):
            return "OK", None
        else:
            return "1210", ["The auto-update flag is not valid!",
                            "Please set the auto-update flag to",
                            "either true or false, without",
                            "additional quotation marks."]

    def get_configuration_value(self, configuration_name):
        """
        Retrieves a configuration value by name, handling type conversion for numbers.

        Args:
            configuration_name (str): The name of the configuration setting to retrieve.

        Returns:
            any: The configuration value, or None if not found.
        """
        configuration = self.configuration.get(configuration_name)
        if configuration is None:
            return None
        elif isinstance(configuration, (int, float)):
            return round(float(configuration), 7)
        else:
            return configuration
        
    def get_image_file(self, image_category, image_name):
        """
        Retrieves image data from the SD card based on category and name.
        Provides fallback images if the requested image is not found.

        Args:
            image_category (str): The category of the image (e.g., "station", "weather", "error", "symbol").
            image_name (str): The name of the image file (without extension).

        Returns:
            bytes: The binary data of the image file.

        Raises:
            Exception: If an unknown image category is provided.
        """
        if image_category == "station":
            folder = "/sd/station_icons"
            fallback = "/symbols/unknown-station.rgb666"
        elif image_category == "weather":
            folder = "/weather_icons"
            fallback = None
        elif image_category == "error":
            folder = "/errors"
            fallback = None
        elif image_category == "symbol":
            folder = "/symbols"
            fallback = None
        else:
            raise Exception("Unknown Image Category!")
        
        try:
            filename = f"{image_name}.rgb666"
            files = os.listdir(folder)
            file_path = f"{folder}/{filename}" if filename in files else fallback
        except Exception:
            file_path = fallback

        with open(file_path, "rb") as f:
            return f.read()
        
    def close(self):
        """
        Unmounts the SD card.
        """
        try:
            os.umount("/sd")
        except Exception:
            pass

