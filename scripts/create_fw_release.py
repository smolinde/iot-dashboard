import os
import shutil
import subprocess
import sys

def create_fw_release(version: str):
    src_dir = "../src"
    temp_dir = "temp"
    tar_name = f"firmware_{version}.tar.gz"
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)

    shutil.copytree(src_dir, temp_dir)
    main_py = os.path.join(temp_dir, "main.py")
    main_new_py = os.path.join(temp_dir, "main_NEW.py")
    if os.path.exists(main_py):
        os.rename(main_py, main_new_py)

    with open(os.path.join(temp_dir, "version"), "w") as f:
        f.write(version)

    subprocess.run(["tar", "-czvf", tar_name, "-C", temp_dir, "."], check = True)
    shutil.rmtree(temp_dir)
    print(f"Firmware archive created: {tar_name}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python build_firmware.py <version>")
        sys.exit(1)

    version = sys.argv[1]
    create_fw_release(version)
