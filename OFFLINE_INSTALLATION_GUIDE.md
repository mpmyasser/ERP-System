
# Offline Installation Guide

This guide explains how to install the project dependencies without an internet connection.

## Steps

1. **Generate the offline installer:**
   - Run the `create_offline_installer.py` script:
     ```bash
     python create_offline_installer.py
     ```
   - This will create a directory named `offline_packages` containing all the required packages.
   - It will also create an installation script named `install_offline.bat`.

2. **Transfer the offline installer:**
   - Copy the `offline_packages` directory and the `install_offline.bat` script to the target machine where you want to install the dependencies.

3. **Install the dependencies offline:**
   - On the target machine, run the `install_offline.bat` script. This will install all the dependencies from the `offline_packages` directory.

Now you have a complete offline installer for your project.
