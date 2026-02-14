
import os
import subprocess
import sys

# The name of the directory to store the packages
OFFLINE_DIR = "offline_packages"

# The name of the requirements file
REQUIREMENTS_FILE = "requirements.txt"

def create_offline_installer():
    """
    Creates an offline installer for the project dependencies.
    """
    print("Creating offline installer...")

    # Create the offline directory if it doesn't exist
    if not os.path.exists(OFFLINE_DIR):
        os.makedirs(OFFLINE_DIR)
        print(f"Created directory: {OFFLINE_DIR}")

    # Download the packages
    print(f"Downloading packages from {REQUIREMENTS_FILE} to {OFFLINE_DIR}...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "download", "-r", REQUIREMENTS_FILE, "-d", OFFLINE_DIR])
        print("Packages downloaded successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error downloading packages: {e}")
        return

    # Create the installation script
    install_script_path = "install_offline.bat"
    with open(install_script_path, "w") as f:
        f.write(f"@echo off\n")
        f.write(f"echo Installing packages from {OFFLINE_DIR}...\n")
        f.write(f"pip install --no-index --find-links={OFFLINE_DIR} -r {REQUIREMENTS_FILE}\n")
        f.write(f"echo Installation complete.\n")
        f.write(f"pause\n")

    print(f"Created installation script: {install_script_path}")
    print("\nOffline installer created successfully!")
    print(f"To use it, first run 'python create_offline_installer.py' to download the packages.")
    print(f"Then, move the '{OFFLINE_DIR}' directory and the '{install_script_path}' script to the target machine.")
    print(f"Finally, run '{install_script_path}' on the target machine to install the packages.")


if __name__ == "__main__":
    create_offline_installer()
