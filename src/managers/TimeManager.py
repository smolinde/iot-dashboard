# Import required libraries
import ntptime, time
import urequests as requests

class TimeManager:
    """Manages time synchronization and timezone settings for the device."""

    __WEEKDAYS = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"]
    __HEADERS = {"User-Agent": "ESP32-OTA-Updater"}

    def __init__(self):
        """
        Initializes the TimeManager, setting default timezone offset and sync status.
        """
        self.tz_offset = 0
        self.timezone = "Etc/UTC"
        self.synced = False
        self.timezone_set = False
        self._time = time.time
        self._localtime = time.localtime

    def sync_time(self):
        """
        Synchronizes the device time with an NTP server.

        Returns:
            tuple: A tuple containing an error code (or "OK") and a list of error messages (or None).
        """
        try:
            ntptime.settime()
            return "OK", None
        except Exception:
            return "2501", ["Time synchronization failed!",
                            "This error is caused by the NTP server,",
                            "probably due to a server outage.",
                            "System will attempt to sync again."]

    def set_timezone(self):
        """
        Determines the local timezone offset using an external API and sets it.
        Updates `self.tz_offset` and `self.timezone`.
        """
        try:
            response = requests.get("https://ipapi.co/json", headers = self.__HEADERS)
            data = response.json()
            response.close()
            offset = data["utc_offset"]
            sign = 1 if offset[0] == "+" else -1
            hours = int(offset[1:3])
            minutes = int(offset[3:]) if len(offset) > 3 else 0
            self.tz_offset = sign * (hours * 3600 + minutes * 60)
            self.timezone = data["timezone"]
            self.timezone_set = True
        except Exception:
            self.tz_offset = 0
            self.timezone = "Etc/UTC"
            self.timezone_set = False
    
    def get_tz_identifier(self):
        """
        Returns the current timezone identifier.

        Returns:
            str: The timezone identifier (e.g., "Europe/Berlin").
        """
        return self.timezone

    def get_timezone_set(self):
        """
        Checks if the timezone has been successfully set.

        Returns:
            bool: True if timezone is set, False otherwise.
        """
        return self.timezone_set

    def get_timestamp(self):
        """
        Returns the current local time as a timestamp tuple, adjusted for timezone offset.

        Returns:
            tuple: A tuple representing the local time (year, month, mday, hour, minute, second, weekday, yearday).
        """
        return self._localtime(self._time() + self.tz_offset)
    
    def get_timedate(self):
        """
        Returns formatted weekday, date, and time strings.

        Returns:
            list: A list containing [weekday (str), date (str), time (str)].
        """
        t = self.get_timestamp()
        return [
            self.__WEEKDAYS[t[6]],
            "{:02d}.{:02d}.{:04d}".format(t[2], t[1], t[0]),
            "{:02d}:{:02d}".format(t[3], t[4])
        ]

