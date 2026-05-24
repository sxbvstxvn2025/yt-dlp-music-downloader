# 🎵 Automated Artist Top 20 Music Downloader & Converter

[![Python Version](https://img.shields.io/badge/Python-3.7+-blue.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![yt-dlp](https://img.shields.io/badge/Dependency-yt--dlp-red.svg?style=for-the-badge&logo=youtube&logoColor=white)](https://github.com/yt-dlp/yt-dlp)
[![ffmpeg](https://img.shields.io/badge/Dependency-ffmpeg-green.svg?style=for-the-badge&logo=ffmpeg&logoColor=white)](https://ffmpeg.org/)

An automated, robust, and highly optimized command-line utility to search, filter, download, and convert the **20 most popular songs** of any given artist. It organizes everything into dedicated directories with clean, elegant file names.

---

## ✨ Features

- **🚀 Multithreaded Downloads:** Downloads up to 4 tracks simultaneously in parallel, dramatically cutting down download time.
- **⚡ Size & Quality Optimization (192 kbps MP3):** Transcodes files to high-fidelity 192 kbps MP3. Since YouTube's original audio stream maxes out at ~128-160 kbps, this maintains 100% source audio quality while shrinking final file sizes and download times by ~40%.
- **📊 View-Based Popularity Sorting:** Fetches the top 50 search candidates from YouTube, parses their exact view counts, and ranks them strictly to identify the actual top 20 hits.
- **🛡️ Smart Filters & Deduplication:** 
  - Filters out YouTube Shorts (< 60 seconds) and full-album compilation loops (> 10 minutes).
  - Automatically identifies duplicate uploads of the same song (e.g. music video vs. album track) and keeps only the highest-viewed official upload.
- **🏷️ Aesthetic Filenames:** Automatically cleans up clutter tags such as `(Official Video)`, `[Lyrics]`, `(HQ Audio)`, and `- Topic` from the final file names.
- **🎨 Modern Colorized UI:** Interactive console outputs with clean, thread-safe progress logging.
- **🛠️ Dependency Checking:** Built-in verification for `yt-dlp` and `ffmpeg` with simple diagnostic messages and platform-specific install commands.
- **🧩 Individual Error Isolation:** Sequence errors on individual tracks (e.g., regional blocks) are isolated; one failing song will not disrupt the rest of the queue.

---

## 📦 Requirements & Installation

This utility requires **Python 3.7+**, **`yt-dlp`**, and **`ffmpeg`** installed and available in your system path.

### 1. Install System Dependencies

#### **Windows (via Package Manager)**
We recommend using the official Windows Package Manager (`winget`):
```powershell
# Install yt-dlp
winget install yt-dlp.yt-dlp

# Install ffmpeg (required for MP3 transcoding)
winget install gyan.ffmpeg
```
*Note: Please restart your terminal/PowerShell session after running these commands to refresh your environment variables.*

#### **macOS (via Homebrew)**
```bash
brew install yt-dlp ffmpeg
```

#### **Linux (Debian/Ubuntu)**
```bash
sudo apt update
sudo apt install yt-dlp ffmpeg
```

---

## 🚀 How to Run

### Option A: Direct Command Line Argument
Pass the artist's name directly as arguments:
```bash
python download_artist_top20.py Queen
```
or for multi-word artist names:
```bash
python download_artist_top20.py "Red Hot Chili Peppers"
```

### Option B: Interactive Prompt
Run the script without arguments and it will prompt you for the artist:
```bash
python download_artist_top20.py
```

---

## 📂 Project Organization

When you search for an artist, the tool creates a dedicated folder and saves all MP3 tracks with beautiful, clean file names:

```text
yt-dlp-music-downloader/
│
├── download_artist_top20.py
├── README.md
└── [Artist Name]/
    ├── Song Title A.mp3
    ├── Song Title B.mp3
    └── ...
```

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the issues page or submit pull requests.
