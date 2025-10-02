# Import requests library
import urequests as requests

class WeatherManager:
    """Manages fetching and processing weather data from the Brightsky API."""
    def __init__(self, lat, long):
        """
        Initializes the WeatherManager with geographical coordinates.

        Args:
            lat (float): The latitude for weather data.
            long (float): The longitude for weather data.
        """
        self.base_url_current_weather = f"https://api.brightsky.dev/current_weather?lat={lat}&lon={long}"
        self.base_url_weather = f"https://api.brightsky.dev/weather?lat={lat}&lon={long}"

    def __round_half_up(self, x):
            """
            Rounds a number to the nearest integer, with halves rounded up.

            Args:
                x (float): The number to round.

            Returns:
                int: The rounded integer.
            """
            if abs(x)%1<.5:
                return int(x)
            return int(x) + 1 if x > 0 else int(x) - 1

    def __get_current_temperature(self, data):
        """
        Extracts the current temperature from the API response data.

        Args:
            data (dict): The JSON response data from the Brightsky API.

        Returns:
            str: The current temperature formatted with `C or "----" if not available.
        """
        try:
            data = data["weather"]["temperature"]
            return f"{self.__round_half_up(data)}`C" if data is not None else "N/A"

        except Exception:
            return "----"
        
    def __get_rain_probability(self, data, hour):
        """
        Extracts the probability of rain for a specific hour from the API response data.

        Args:
            data (dict): The JSON response data from the Brightsky API.
            hour (int): The hour to get rain probability for.

        Returns:
            str: The rain probability formatted with % or "----" if not available.
        """
        try:
            hour_str = f"{hour:02d}"
            entry = next(
                (w for w in data.get("weather", []) 
                if w.get("timestamp", "")[11:13] == hour_str),
                None
            )
            if entry and entry.get("precipitation_probability") is not None:
                return f"{entry["precipitation_probability"]}%"
            return "0%"
        except Exception:
            return "----"
    
    def __get_min_max_temperature(self, data, current_temperature, date):
        """
        Extracts the minimum and maximum temperatures for a given date from the API response data.

        Args:
            data (dict): The JSON response data from the Brightsky API.
            current_temperature (str): The current temperature string (e.g., "20`C").
            date (str): The date in "YYYY-MM-DD" format.

        Returns:
            tuple: A tuple containing the minimum and maximum temperatures formatted with `C or "----" if not available.
        """
        try:
            temps = [
                entry["temperature"]
                for entry in data.get("weather", [])
                if entry.get("temperature") is not None
                and entry.get("timestamp", "").startswith(date)
            ]

            if not temps:
                return "----", "----"

            if current_temperature != "----":
                try:
                    temps.append(int(current_temperature.replace("`C","")))
                except Exception:
                    pass

            min_temp = self.__round_half_up(min(temps))
            max_temp = self.__round_half_up(max(temps))

            return f"{min_temp}`C", f"{max_temp}`C"

        except Exception:
            return "----", "----"
    
    def __get_weather_icon(self, data):
        """
        Extracts the weather icon name from the API response data.

        Args:
            data (dict): The JSON response data from the Brightsky API.

        Returns:
            str: The weather icon name or "unknown" if not available.
        """
        try:
            data = data["weather"]["icon"]
            return str(data) if data is not None else "unknown"

        except Exception:
            return "unknown"

    def get_weather_data(self, timestamp, timezone):
        """
        Fetches and processes current and forecasted weather data.

        Args:
            timestamp (tuple): A time tuple (year, month, mday, hour, ...).
            timezone (str): The timezone identifier (e.g., "Europe/Berlin").

        Returns:
            tuple: A tuple containing a list of weather data [current_temp, rain_prob, min_temp, max_temp] and the weather icon name.
        """
        date = "{:04d}-{:02d}-{:02d}".format(
            timestamp[0], timestamp[1], timestamp[2]
        )
        try:
            response = requests.get(self.base_url_current_weather)
            data = response.json()
            response.close()
            current_temperature = self.__get_current_temperature(data)
            weather_icon_name = self.__get_weather_icon(data)
        except Exception:
            current_temperature = "----"
            weather_icon_name = "unknown"

        try:
            response = requests.get(f"{self.base_url_weather}&date={date}&tz={timezone}")
            data = response.json()
            response.close()
            rain_probability = self.__get_rain_probability(data, timestamp[3])
            min_temp, max_temp = self.__get_min_max_temperature(data, current_temperature, date)
        except Exception:
            rain_probability, min_temp, max_temp = "----", "----", "----"

        return [current_temperature, rain_probability, min_temp, max_temp], weather_icon_name

