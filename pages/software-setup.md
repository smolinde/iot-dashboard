# Software Setup
← [Homepage](../)

## 1 Required Software Tools
To be able to flash the software to the dashboard, you have to install [Python](https://www.python.org/downloads/) and [Git](https://git-scm.com/) on your machine. For this instruction, I will use [Mircosoft PowerShell](https://learn.microsoft.com/en-us/powershell/). This is an amazing command line interface (CLI) that I use a lot. On Mac/Linux, you can use the built-in terminal.

## 2 Software Preparation
Open a new PowerShell or terminal window. Navigate to the folder where you want to have this repository stored. Copy the corresponding path from your file explorer and run this command:

        cd "path/to/your/folder"

To clone the repository, run the following command:

        git clone https://github.com/smolinde/iot-dashboard.git

Navigate inside the downloaded repository:

        cd iot-dashboard

You need to install a few Python packages that are required to flash the ESP32-S3 Nano with MicroPython, upload the dashboard source code to it, and to be able to run the helper scripts from [this folder](../scripts). To install the required packages, run the following command:

        pip install -r requirements.txt

Next step is to download the latest [MicroPython](https://micropython.org/) firmware for the ESP32-S3 Nano. <b>Please note that you need to download the version that supports external PSRAM!</b> Download the corresponding `.bin` file from [here](https://micropython.org/download/ESP32_GENERIC_S3/). Now you have acquired all necessary software components.

### 3 Flashing MicroPython to the ESP32-S3 Nano
Connect your dashboard to your computer with either the USB-C cable that was listed in the [shopping list](#1-shopping-list) or any other that you prefer. You will notice that (if you are using a Windows 11 machine) the dashboard appears and disappears in an endless loop. This is because the microcontroller is new and needs to be set to bootloader mode. Keep the microcontroller connected to your computer. To be able to push the buttons, use two paperclips. To activate the ROM bootloader, press and hold the <kbd>BOOT</kbd> button. While holding it, push the <kbd>RST</kbd> button and release immediately. Now you can release the <kbd>BOOT</kbd> button. If the ESP32-S3 Nano is still caught in the connect/disconnect loop, repeat the process again. After successfully entering the bootloader mode, you can proceed with erasing the flash memory. Run the following command in a terminal window:

        esptool erase-flash

This command wipes everything from the microcontroller storage. Next, navigate with `cd` to the MicroPython firmware file that you have downloaded previously. To flash MicroPython to the ESP32-S3 Nano, run the following command:

        esptool --baud 460800 write-flash 0 ESP32_BOARD_NAME-DATE-VERSION.bin

Please make sure to adjust the firmware file name before running the command. The process will take some time. Now your dashboard has MicroPython installed on it. After the installation, you need to unplug the dashboard from the computer, wait a few seconds, and then reconnect it. Run the following command in your terminal:

        mpremote

You should see something like this:

        Connected to MicroPython at COM8
        Use Ctrl-] or Ctrl-x to exit this shell
        Performing initial setup
        MicroPython v1.26.1 on 2025-09-11; Generic ESP32S3 module with Octal-SPIRAM with ESP32S3
        Type "help()" for more information.
        >>>

Remember the port that your computer uses to communicate with the dashboard. In my case, it is `COM8`. Press <kbd>CTRL</kbd> + <kbd>X</kbd> to quit the MicroPython shell of the ESP32-S3 Nano.

## 4 Installation of Dashboard Software
The last component that is still missing is the dashboard software, or more precise, firmware. This requires a few commands only, and is usually a very brief procedure. After a fresh MicroPython installation, there is a file called `boot.py` in the root directory of the microcontroller. This file is obsolete and can be removed with the following command:

        mpremote connect COM8 fs rm boot.py

Now we also have to install three additional MicroPython libraries that will be used by the software. The following command requires your computer to have a working internet connection:

        mpremote connect COM8 mip install tarfile gzip shutil

These libraries will be used for automatic firmware updates in the [updater.py](../src/updater.py) script. Now everythin that is left is to copy all contents from the `src` directory of the repository. Navigate with the following command to the folder:

        cd "path/to/your/folder/iot-dashboard/src"

Then run the following command to copy everything to the dashboard:

        mpremote connect COM8 fs cp -r . :

This command copies everything in the current directory recursively to the root directory of the ESP32-S3 Nano. This can take some time to complete. After that, your dashboard is ready for exploitation. Disconnect the dashboard from yor computer and connect it to any 5V power supply. You will most likely see the [Error 1101](../errors/1101.md) as there is no SD card inserted yet. Please get familiar with the possibilities and customization options from the [User Manual](./user-manual.md).

<p align="center"><a href="#">Unscroll this page</a></p>