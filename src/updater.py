import machine, os, gzip, tarfile, hashlib, shutil, ubinascii
import urequests as requests

class UpdateManager:

    __HEADERS = {"User-Agent": "ESP32-OTA-Updater"}
    __OTA_API_URL = "https://api.github.com/repos/smolinde/iot-dashboard/releases/latest"

    def __init__(self):
        self.tag_name = None
        self.name = None
        self.browser_download_url = None
        self.digest = None

    def update_available(self):
        current_version = "v0.0.0"
        try:
            with open("version", "r") as f:
                current_version = f.read().strip()
        except Exception:
            with open("version", "w") as f:
                f.write("v0.0.0")

        try:
            response = requests.get(self.__OTA_API_URL, headers = self.__HEADERS)
            data = response.json()
            response.close()
            self.tag_name = data["tag_name"]
            self.name = data["assets"][0]["name"]
            self.browser_download_url = data["assets"][0]["browser_download_url"]
            self.digest = data["assets"][0]["digest"][7:]
            return current_version, self.tag_name
        except Exception:
            return None, None

    def download_update(self):
        try:
            response = requests.get(self.browser_download_url, headers = self.__HEADERS)
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
        sha256 = hashlib.sha256()
        with open("/" + self.name, 'rb') as f:
            while True:
                chunk = f.read(8192)
                if not chunk:
                    break
                sha256.update(chunk)

        update_sha = ubinascii.hexlify(sha256.digest()).decode()
        if update_sha == self.digest:
            return "OK", None
        else:
            return "2602", ["Update Verification Failed!",
                            "The system will discard this update.",
                            f"File SHA256 (tail): [...]{update_sha[-10:]}",
                            f"True SHA256 (tail): [...]{self.digest[-10:]}"]
        
def __path_exists(path):
    try:
        os.stat(path)
        return True
    except OSError:
        return False

def main():
    update_file = next((f for f in os.listdir("/") if f.startswith("firmware_v") and f.endswith(".tar.gz")), None)
    if not update_file:
        raise Exception("No update file found!")

    for entry in os.listdir("/"):
        if entry in ["lib", update_file, "main.py"]:
            continue

        try:
            if os.stat("/" + entry)[0] & 0x4000:
                shutil.rmtree("/" + entry)
            else:
                os.remove("/" + entry)
        except Exception:
            raise Exception("Failed to wipe the root storage!")

    with gzip.open("/" + update_file, "rb") as gz:
        tar = tarfile.TarFile(fileobj = gz)
        for member in tar:
            print(member.name)
            if member.name not in [".", "./"]:
                if member.type == tarfile.DIRTYPE:
                    os.mkdir(member.name)
                else:
                    source = tar.extractfile(member)
                    with open(member.name, "wb") as target:
                        target.write(source.read())

    os.remove("main.py")
    os.rename("main_NEW.py", "main.py")
    os.remove(update_file)
    machine.reset()

if __name__ == "__main__":
    try:
        main()
    except Exception:
        machine.deepsleep()