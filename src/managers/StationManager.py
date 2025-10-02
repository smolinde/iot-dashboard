# Import requests library
import urequests as requests

class StationManager:
    """Manages fetching and processing gas station data from the Tankerkoenig API."""
    __STATION_STATUSES = {
        "open": "OPEN",
        "closed": "CLOSED",
        "no prices": "NO PRICES",
        None: "STATUS UNKNOWN"
    }
    
    def __init__(self, station_ids, fuel_type, api_key):
        """
        Initializes the StationManager with station IDs, fuel type, and API key.

        Args:
            station_ids (list): A list of station UUIDs.
            fuel_type (str): The type of fuel to query (e.g., "e5", "e10", "diesel").
            api_key (str): The API key for the Tankerkoenig service.
        """
        self.station_ids = station_ids
        self.fuel_type = fuel_type
        self.base_url_station_info = f"https://creativecommons.tankerkoenig.de/json/prices.php?apikey={api_key}"
    
    def __get_station_status(self, data, station_id):
        """
        Extracts the status of a specific station from the API response data.

        Args:
            data (dict): The JSON response data from the Tankerkoenig API.
            station_id (str): The UUID of the station.

        Returns:
            str: The status of the station (e.g., "OPEN", "CLOSED", "NO PRICES", "STATUS UNKNOWN").
        """
        try:
            data = data["prices"][station_id]["status"]
            return self.__STATION_STATUSES.get(data)

        except Exception:
            return self.__STATION_STATUSES.get(None)

    def __get_station_fuel_price(self, data, station_id):
        """
        Extracts the fuel price for a specific station and fuel type from the API response data.

        Args:
            data (dict): The JSON response data from the Tankerkoenig API.
            station_id (str): The UUID of the station.

        Returns:
            str: The formatted fuel price (e.g., "1,59") or "-,--" if not available.
        """
        try:
            data = data["prices"][station_id][self.fuel_type]
            return f"{data:.2f}".replace(".", ",") if data is not None else "-,--"

        except Exception:
            return "-,--"
        
    def get_station_data(self):
        """
        Fetches gas station statuses and fuel prices for all configured stations.

        Returns:
            tuple: A tuple containing two lists: station statuses and fuel prices.
        """
        try:
            response = requests.get(f"{self.base_url_station_info}&ids={",".join(self.station_ids)}")
            data = response.json()
            response.close()
            statuses = [self.__get_station_status(data, sid) for sid in self.station_ids]
            prices = [self.__get_station_fuel_price(data, sid) for sid in self.station_ids]

        except Exception:
            statuses = [self.__STATION_STATUSES.get(None)] * len(self.station_ids)
            prices = ["-,--"] * len(self.station_ids)

        return statuses, prices

