import os, time, machine, socket
from machine import SPI, Pin
from managers.DisplayManager import DisplayManager
from managers.FileManager import FileManager
from managers.StationManager import StationManager
from managers.TimeManager import TimeManager
from managers.WlanManager import WlanManager
from managers.WeatherManager import WeatherManager
from drivers.xglcd_font import XglcdFont
from drivers.XPT2046 import Touch
from updater import UpdateManager

WLAN_TIMEOUT = 30
REQUEST_TIMEOUT = 5
UPDATE_HOUR = 3
LOOP_DELAY = 0.2

T_DAY = 2
T_HOUR = 3
T_MINUTE = 4
T_SECOND = 5

socket.socket().settimeout(REQUEST_TIMEOUT)
fmgr = FileManager()
dspm = DisplayManager(XglcdFont("fonts/ILIFont10x19.c", 10, 19), XglcdFont("fonts/PriceFont15x33.c", 15, 33))
upmr = UpdateManager()

def exit_if_process_fails(error_code, error_text, display_manager, file_manager, wlan_manager=None):
    if error_code is not "OK":
        qr_code = file_manager.get_image_file("error", error_code)
        display_manager.draw_error(error_code, error_text, qr_code)
        file_manager.close()
        if wlan_manager != None:
            wlan_manager.close()

        if error_code[0] == "1":
            touch_spi = SPI(1, baudrate=2000000, polarity=0, phase=0, sck=Pin(7), mosi=Pin(5), miso=Pin(4))
            touch_manager = Touch(touch_spi, Pin(6), Pin(3), 2)
            while not touch_manager.is_touched():
                pass
        
        machine.reset()

def update_firmware(display_manager, update_manager, file_manager, wlan_manager):
    current_version, update_version = update_manager.update_available()
    if current_version != update_version:
        display_manager.draw_update_screen(file_manager.get_image_file("symbol", "update"), current_version, update_version)
        display_manager.draw_update_action("Downloading update...")
        exit_if_process_fails(*update_manager.download_update(), display_manager, file_manager, wlan_manager)
        display_manager.draw_update_action("Verifying update...")
        exit_if_process_fails(*update_manager.verify_update(), display_manager, file_manager, wlan_manager)
        display_manager.draw_update_action("Installing update...")
        os.rename("main.py", "main_OLD.py")
        os.rename("updater.py", "main.py")
        machine.reset()

def main():
    dspm.draw_waiting_screen()
    exit_if_process_fails(*fmgr.open_sd_card(), dspm, fmgr)
    exit_if_process_fails(*fmgr.validate_sd_card_contents(), dspm, fmgr)
    wlnm = WlanManager()
    wlnm.connect(fmgr.get_configuration_value("wlan_ssid"), fmgr.get_configuration_value("wlan_psk"))
    dspm.draw_waiting_for_wlan(fmgr.get_image_file("symbol", "wlan"), fmgr.get_configuration_value("wlan_ssid"))
    for i in range(WLAN_TIMEOUT + 1):
        dspm.draw_wlan_waiting_time(WLAN_TIMEOUT - i)
        if wlnm.is_connected_boolean():
            break

        time.sleep(1)
    
    exit_if_process_fails(*wlnm.is_connected(), dspm, fmgr, wlnm)
    exit_if_process_fails(*wlnm.device_online(), dspm, fmgr, wlnm)
    tmgr = TimeManager()
    exit_if_process_fails(*tmgr.sync_time(), dspm, fmgr, wlnm)
    tmgr.set_timezone()
    wmgr = WeatherManager(fmgr.get_configuration_value("weather_lat"), fmgr.get_configuration_value("weather_long"))
    stmr = StationManager(fmgr.get_configuration_value("station_ids"),
                          fmgr.get_configuration_value("fuel_type"),
                          fmgr.get_configuration_value("tankerkoenig_api_key"))
    dspm.draw_main_layout(
        [fmgr.get_image_file("station", label[0]) for label in fmgr.get_configuration_value("station_labels")],
        [fmgr.get_image_file("symbol", "thermometer"), 
        fmgr.get_image_file("symbol", "raindrop"),
        fmgr.get_image_file("symbol", "lowest-temperature"),
        fmgr.get_image_file("symbol", "highest-temperature")],
        fmgr.get_configuration_value("station_labels"),
        fmgr.get_configuration_value("fuel_type")
    )
    
    dspm.draw_weekday_date_time(tmgr.get_timedate())
    weather_data, weather_icon_name = wmgr.get_weather_data(tmgr.get_timestamp(), tmgr.get_tz_identifier())
    dspm.draw_weather_data(weather_data, weather_icon_name, fmgr.get_image_file("weather", weather_icon_name))
    dspm.draw_station_data(*stmr.get_station_data())

    previous_day = -1
    previous_hour = -1
    previous_minute = -1
    data_can_be_updated = False
    perform_update_check = False
   
    while True:
        t = tmgr.get_timestamp()
        if previous_day != t[T_DAY]:
            previous_day = t[T_DAY]
            perform_update_check = True

        if previous_hour != t[T_HOUR]:
            previous_hour = t[T_HOUR]
            exit_if_process_fails(*wlnm.device_online(), dspm, fmgr, wlnm)
            exit_if_process_fails(*tmgr.sync_time(), dspm, fmgr, wlnm)

        if previous_minute != t[T_MINUTE]:
            previous_minute = t[T_MINUTE]
            dspm.draw_weekday_date_time(tmgr.get_timedate())

        if (t[T_MINUTE] - 1) % 5 != 0 and not data_can_be_updated:
            data_can_be_updated = True

        if (data_can_be_updated and t[T_SECOND] >= 1 and (t[T_MINUTE] - 1) % 5 == 0):
            data_can_be_updated = False
            exit_if_process_fails(*wlnm.device_online(), dspm, fmgr, wlnm)
            if not tmgr.get_timezone_set():
                tmgr.set_timezone()

            if (fmgr.get_configuration_value("automatic_updates") and perform_update_check and t[T_HOUR] == UPDATE_HOUR):
                perform_update_check = False
                update_firmware(dspm, upmr, fmgr, wlnm)
            
            weather_data, weather_icon_name = wmgr.get_weather_data(t, tmgr.get_tz_identifier())
            if(dspm.currently_displayed.get("weather_icon_name") != weather_icon_name):
                dspm.draw_weather_data(weather_data, weather_icon_name, fmgr.get_image_file("weather", weather_icon_name))
            else:
                dspm.draw_weather_data(weather_data, weather_icon_name)
            
            dspm.draw_station_data(*stmr.get_station_data())
            
        time.sleep(LOOP_DELAY)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        dspm.draw_waiting_screen()
        exit_if_process_fails(*fmgr.open_sd_card(), dspm, fmgr)
        exit_if_process_fails("1000", ["An unexpected error occured:",
                                       str(e)[:42],
                                       "Please try to reproduce it and open",
                                       "a new issue on the GitHub page!"], 
                                       dspm, fmgr)