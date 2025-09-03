# Nebris
A modern, lightweight screen saver application for Windows that transforms your idle time into an elegant clock display.

![Nebris](<img width="512" height="512" alt="n" src="https://github.com/user-attachments/assets/5e8ceb4b-db4a-463d-8082-393f4196e1a0" />
)

## ✨ Features

<img width="256" height="256" alt="n" src="https://github.com/user-attachments/assets/662b8ba0-100c-482a-976a-507916102c9f" />

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

# Build executable
pyinstaller --onefile --windowed --icon=ikonica.ico --name "Nebris" nebris.py



