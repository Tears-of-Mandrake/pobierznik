# Pobierznik

A powerful and user-friendly video downloader and streaming application built with GTK4, python and libadwaita. Use yt-dlp and streamlink as backend.

Pobierznik – a name inspired by Old Polish and Slavic word formation, referencing historical noun forms that denoted a person performing a specific action (e.g., miecznik – swordsmith, garncarz – potter). The word pobierać is deeply rooted in the Polish language, meaning both "to download" and "to acquire." Pobierznik is a unique and familiar-sounding application for downloading and playing video streams, serving as a frontend for Streamlink. The name evokes the spirit of old craftsmen and simplicity, blending tradition with modern technology.

The application was developed for the Linux OpenMandriva system, but due to the hostility towards gtk and python software, it may never see the light of day there, so a new home for the application is being sought. The downloader works on others like Fedora, OpenSuse, Arch or Ubuntu - provided that the appropriate dependencies are installed.


## Features

- Download videos from various platforms (YouTube, Vimeo, and more)
- Stream videos directly using your preferred video player
- Batch download multiple videos at once
- Download history management
- Configurable video and audio quality
- Speed limit control
- Custom download directory
- Multiple video player support (MPV, VLC, MPlayer, Clapper, QMPlay2, or custom)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/Tears-of-Mandrake/pobierznik.git
cd pobierznik
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Install system dependencies:
```bash
# For Debian/Ubuntu
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-4.0 gir1.2-adw-1

# For OpenMandriva/Fedora
sudo dnf install python-pip python-setuptools lib64glib2.0-devel desktop-file-utils

# Runtime dependencies if not installed with pip
yt-dlp. streamlink, python,libadwaita-common, lib64adwaita-gir1 or typelib(Adw), python-gi, python-gobject3

# For video playback, install at least one of:
sudo apt install mpv vlc mplayer clapper qmplay2
```

4. Run the application:
```bash
python3 main.py
```

## Usage

1. **Single Video Download/Stream**
   - Enter a video URL in the main tab
   - Click "Download" to save the video
   - Click "Watch" to stream directly

2. **Batch Download**
   - Switch to the Batch Download tab
   - Enter multiple URLs (one per line)
   - Click "Download All"

3. **Configure Settings**
   - Click the menu button (⋮) and select "Preferences"
   - Set your preferred:
     - Download directory
     - Download speed limit
     - Video/audio quality
     - Video player

## License

GPL-3.0

## Author

Damian Marcin Szymański aka Angry Penguin

Tears of Mandrake 2025
