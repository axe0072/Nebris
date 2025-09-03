# Nebris
A modern, lightweight screen saver application for Windows that transforms your idle time into an elegant clock display.

![Nebris Screensaver](screenshot.png)

## ✨ Features

- **Multiple Clock Styles**: Digital, Flip, Date, and Calendar views
- **Multi-language Support**: 12 languages including English, Spanish, French, German, and more
- **Smart Activation**: Only activates when system is truly idle
- **Audio Detection**: Pauses when audio is playing
- **System Tray Integration**: Runs quietly in background
- **Auto-start Option**: Launch with Windows startup
- **Customizable**: Choose fonts, timeout duration, and display style

## 🚀 Installation

### Option 1: Download Executable
1. Download the latest `Nebris.exe` from [Releases](#)
2. Run the executable
3. The app will start minimized in system tray

### Option 2: Build from Source
```bash
# Clone repository
git clone https://github.com/axe0072/nebris.git

# Install dependencies
pip install -r requirements.txt

# Build executable
pyinstaller --onefile --windowed --icon=ikonica.ico --name "Nebris" main7.py
