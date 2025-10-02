# Import required libraries
import machine, os, gzip, tarfile, hashlib, shutil, ubinascii
import urequests as requests

class UpdateManager:
    """Manages the over-the-air (OTA) firmware update process by interacting with a GitHub repository."""

    __HEADERS = {"User-Agent": "ESP32-OTA-Updater"} # Custom User-Agent for API requests
    __OTA_API_URL = "https://api.github.com/repos/smolinde/iot-dashboard/releases/latest" # GitHub API endpoint for latest release

    def __init__(self):
        """
        Initializes the UpdateManager, preparing attributes to store release information.
        """
        self.tag_name = None # Stores the tag name (version) of the latest release
        self.name = None # Stores the name of the release asset file
        self.browser_download_url = None # Stores the download URL for the release asset
        self.digest = None # Stores the SHA256 digest of the release asset for verification

    def update_available(self):
        """
        Checks if a new firmware update is available by comparing the current version with the latest GitHub release.

        Returns:
            tuple: A tuple containing the current version and the latest available version (or None if an error occurs).
        """
        current_version = "v0.0.0"
        try:
            # Read current version from file
            with open("version", "r") as f:
                current_version = f.read().strip()
        except Exception:
            # If version file doesn't exist, create it with default version
            with open("version", "w") as f:
                f.write("v0.0.0")

        try:
            # Fetch latest release information from GitHub API
            response = requests.get(self.__OTA_API_URL, headers = self.__HEADERS)
            data = response.json()
            response.close()
            
            # Parse release data
            self.tag_name = data["tag_name"]
            self.name = data["assets"][0]["name"]
            self.browser_download_url = data["assets"][0]["browser_download_url"]
            # Extract SHA256 digest from the asset information
            self.digest = data["assets"][0]["digest"][7:] 
            return current_version, self.tag_name
        except Exception:
            return None, None

    def download_update(self):
        """
        Downloads the firmware update file from the specified URL.

        Returns:
            tuple: "OK" and None on success, or an error code and message on failure.
        """
        try:
            response = requests.get(self.browser_download_url, headers = self.__HEADERS)
            # Write the downloaded content to a file in the root directory
            with open("/" + self.name, "wb") as f:
                f.write(response.content)
            response.close()
            return "OK", None
        except Exception:
            return "2601", ["Update Download Failed!",
                            "Something went wrong while downloading",
                            "the update. The system will attempt to",
                            "download the update in 24 hours again!"]

    def verify_update(self):
        """
        Verifies the integrity of the downloaded update file using its SHA256 hash.

        Returns:
            tuple: "OK" and None on success, or an error code and message on failure.
        """
        sha256 = hashlib.sha256()
        # Calculate SHA256 hash of the downloaded file
        with open("/" + self.name, 'rb') as f:
            while True:
                chunk = f.read(8192) # Read in chunks to handle large files
                if not chunk:
                    break
                sha256.update(chunk)

        update_sha = ubinascii.hexlify(sha256.digest()).decode()
        # Compare calculated hash with the expected digest
        if update_sha == self.digest:
            return "OK", None
        else:
            return "2602", ["Update Verification Failed!",
                            "The system will discard this update.",
                            f"File SHA256 (tail): [...]{update_sha[-10:]}",
                            f"True SHA256 (tail): [...]{self.digest[-10:]}"]
        
def __path_exists(path):
    """
    Checks if a given file or directory path exists.

    Args:
        path (str): The path to check.

    Returns:
        bool: True if the path exists, False otherwise.
    """
    try:
        os.stat(path)
        return True
    except OSError:
        return False

def main():
    """
    This main function is executed when the device reboots into the updater script.
    It extracts the new firmware, replaces old files, and reboots the device.
    """
    # Find the downloaded update file (e.g., firmware_vX.Y.Z.tar.gz)
    update_file = next((f for f in os.listdir("/") if f.startswith("firmware_v") and f.endswith(".tar.gz")), None)
    if not update_file:
        raise Exception("No update file found!")

    # Clean up old files and directories, excluding essential update files
    for entry in os.listdir("/"):
        if entry in ["lib", update_file, "main.py"]:
            continue # Skip essential directories/files

        try:
            # Remove directories recursively or delete files
            if os.stat("/" + entry)[0] & 0x4000: # Check if it's a directory
                shutil.rmtree("/" + entry)
            else:
                os.remove("/" + entry)
        except Exception:
            raise Exception("Failed to wipe the root storage!")

    # Extract the new firmware from the gzipped tar archive
    with gzip.open("/" + update_file, "rb") as gz:
        tar = tarfile.TarFile(fileobj = gz)
        for member in tar:
            print(member.name) # Print file names being extracted for debugging/progress
            if member.name not in [".", "./"]:
                if member.type == tarfile.DIRTYPE:
                    os.mkdir(member.name) # Create directory
                else:
                    source = tar.extractfile(member)
                    with open(member.name, "wb") as target:
                        target.write(source.read()) # Extract file content

    # Finalize the update process
    os.remove("main.py") # Remove the updater script itself
    os.rename("main_NEW.py", "main.py") # Rename the new main application file
    os.remove(update_file) # Delete the downloaded update archive
    machine.reset() # Reboot into the new firmware

if __name__ == "__main__":
    try:
        main()
    except Exception:
        # If something goes wrong, enter deep sleep to conserve power
        machine.deepsleep()

