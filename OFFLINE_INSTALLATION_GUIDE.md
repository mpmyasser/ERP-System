# Offline Installation Guide

This project can run on a new Windows machine without internet, but the offline package must include:

- the full project folder, not only `offline_packages`;
- `install_offline.bat`;
- `start_hr.bat`;
- `offline_packages\requirements.txt`;
- all wheel files in `offline_packages`;
- `offline_packages\python-3.11.9-amd64.exe`.

Why Python 3.11.9? The included wheels are built for CPython 3.11 on 64-bit Windows (`cp311-win_amd64`). Python 3.11.9 is the last Python 3.11 release that provides the normal Windows installer.

## Build the offline package on an online machine

Run:

```bat
python create_offline_installer.py
```

The script downloads the required wheels and the Python 3.11.9 Windows x64 installer into `offline_packages`.

## Install on the offline machine

1. Copy the whole project folder to the offline machine.
2. Run `install_offline.bat`.
3. After it finishes successfully, run `start_hr.bat`.

The installer creates a local `.venv` folder and installs packages from `offline_packages` only. It writes detailed errors to `offline_install.log`.
