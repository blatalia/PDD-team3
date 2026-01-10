# Lasers Image Analyzer

### HOW TO USE APP SEE APP-INSTRUCTION


## Overview

**Lasers Image Analyzer** is a desktop application for **laser beam image analysis**.  
It provides a graphical user interface (GUI) for loading laser beam images and performing
quantitative analysis without requiring command-line interaction during normal use.

The application supports:
- intensity and contrast analysis,
- region of interest (ROI) selection,
- intensity profile extraction,
- batch processing of multiple images,
- exporting results to CSV, TXT, and PDF formats.

The tool is intended for **laboratory, research, and educational use**.

---

## Requirements

- Python 3.9 or newer
- Git
- Linux (Debian/Ubuntu) or Windows

---

## Installation

You can install and run the application in two ways:
- using the provided installer scripts (recommended),
- running it manually from the repository.

---

### Linux (Debian / Ubuntu)

#### 1. Clone the repository
```bash
git clone <REPOSITORY_URL>
cd PDD-team3
```

#### 2. Run the installer
```bash
chmod +x scripts/*.sh
./scripts/install_linux.sh
```

The installer:
- uses the existing `venv/` directory,
- installs all required Python dependencies,
- creates a desktop launcher (`.desktop` file),
- allows the application to be started from the system menu or desktop.

After installation, the application can be launched by clicking the desktop icon.

---

### Windows

#### 1. Clone the repository
```powershell
git clone <REPOSITORY_URL>
cd PDD-team3
```

#### 2. Run the installer
```powershell
.\scripts\install_windows.ps1
```

If PowerShell blocks script execution, run once:
```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

The installer:
- uses the existing `venv\` directory,
- installs all required Python dependencies,
- creates a desktop shortcut,
- allows the application to be started by double-clicking the shortcut.

---

## Manual Run (Without Installer)

The application can also be run directly from the repository.

### Linux / macOS
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m app.main
```

### Windows
```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python -m app.main
```

This mode is recommended for development and debugging.

---

## Project Structure

```
PDD-team3/
├── app/            # GUI application
├── core/           # image processing and analysis logic
├── scripts/        # installer and launcher scripts
├── results/        # exported analysis results
├── test_photos/    # example input images
├── venv/           # Python virtual environment
├── requirements.txt
└── README.md
```

---

## Notes

- The virtual environment is local to the repository.
- No system-wide Python packages are installed.
- The application is started using:
  ```bash
  python -m app.main
  ```
- Internet access is not required after installation.

---

## License

This project is intended for academic and educational use.
