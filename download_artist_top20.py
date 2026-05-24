#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
================================================================================
                    ARTIST TOP 20 MP3 DOWNLOADER & CONVERTER
================================================================================
A highly robust, professional-grade automation tool to search, filter,
download, and convert the 20 most popular songs of any given artist to
high-quality MP3 format.

Key Features:
1. Native Windows & Cross-Platform compatibility (Python-based).
2. Clean, interactive user prompts and command-line argument support.
3. Strict popularity ranking based on exact YouTube view counts.
4. Smart duration filtering (60s - 10mins) to exclude Shorts and compilations.
5. Smart deduplication (keeps only the highest-viewed upload of a song).
6. Smart title cleanup (removes "(Official Music Video)", "[Lyrics]", etc.).
7. Individual download error isolation (one bad track won't crash the script).
8. Dedicated sanitized folder creation per artist.
9. Beautiful, colorized, user-friendly CLI output.
================================================================================
"""

import os
import sys
import re
import json
import shutil
import subprocess

# Define colors for beautiful, modern CLI output (supported on Windows 10+ and UNIX)
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# Enable Virtual Terminal Processing on Windows to display ANSI colors correctly
if sys.platform == 'win32':
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        # SetConsoleMode on STD_OUTPUT_HANDLE (-11) to enable ENABLE_VIRTUAL_TERMINAL_PROCESSING (0x0004)
        # Combined with other modes, typically 7 handles it beautifully
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except Exception:
        # If Windows version doesn't support it or ctypes fails, disable colors to avoid junk text
        Colors.HEADER = ''
        Colors.OKBLUE = ''
        Colors.OKCYAN = ''
        Colors.OKGREEN = ''
        Colors.WARNING = ''
        Colors.FAIL = ''
        Colors.ENDC = ''
        Colors.BOLD = ''
        Colors.UNDERLINE = ''


def check_dependencies():
    """
    Checks if yt-dlp and ffmpeg are installed and in the system's PATH.
    """
    yt_dlp_path = shutil.which("yt-dlp")
    ffmpeg_path = shutil.which("ffmpeg")
    return yt_dlp_path is not None, ffmpeg_path is not None


def sanitize_filename(name):
    """
    Remove illegal characters from the string to make it safe for folder and filenames,
    specifically targeting Windows (\ / : * ? " < > |) and UNIX platforms.
    """
    name = re.sub(r'[\\/*?:"<>|]', '', name)
    name = re.sub(r'\s+', ' ', name).strip()
    return name


def clean_song_title(title, artist_name):
    """
    Cleans song titles by removing redundant artist branding and common promotional trash tags.
    Example: "Queen - Bohemian Rhapsody (Official Video) [HD]" -> "Bohemian Rhapsody"
    """
    # 1. Case-insensitive removal of artist name from the beginning or end of the title if separated
    artist_esc = re.escape(artist_name)
    title = re.sub(rf'^\s*{artist_esc}\s*[-–—:]\s*', '', title, flags=re.IGNORECASE)
    title = re.sub(rf'\s*[-–—:]\s*{artist_esc}\s*$', '', title, flags=re.IGNORECASE)
    
    # 2. Case-insensitive removal of common promotional tags, video details, and channel suffixes
    trash_patterns = [
        r'\s*[\(\[]\s*Official\s+Video\s*[\)\]]',
        r'\s*[\(\[]\s*Official\s+Music\s+Video\s*[\)\]]',
        r'\s*[\(\[]\s*Official\s+Audio\s*[\)\]]',
        r'\s*[\(\[]\s*Official\s+Lyric\s+Video\s*[\)\]]',
        r'\s*[\(\[]\s*Lyric\s+Video\s*[\)\]]',
        r'\s*[\(\[]\s*Music\s+Video\s*[\)\]]',
        r'\s*[\(\[]\s*Lyrics\s*[\)\]]',
        r'\s*[\(\[]\s*Audio\s*[\)\]]',
        r'\s*[\(\[]\s*HD\s*[\)\]]',
        r'\s*[\(\[]\s*HQ\s*[\)\]]',
        r'\s*[\(\[]\s*4K\s*[\)\]]',
        r'\s*[\(\[]\s*Remastered\s*[\)\]]',
        r'\s*[\(\[]\s*Remastered\s+\d{4}\s*[\)\]]',
        r'\s*\|\s*Official\s*Video',
        r'\s*\|\s*Official\s*Music\s*Video',
        r'\s*-\s*Topic$', # Suffix for YouTube Music auto-generated channel tracks
    ]
    
    for pattern in trash_patterns:
        title = re.sub(pattern, '', title, flags=re.IGNORECASE)
        
    # 3. Trim spacing
    title = re.sub(r'\s+', ' ', title).strip()
    
    # 4. Strip outer quotes if any
    title = re.sub(r'^["\'“‘](.*)["\'”’]$', r'\1', title).strip()
    
    return title


def fetch_top_tracks(artist_name):
    """
    Search YouTube for 50 candidates using the yt-dlp flat-playlist feature.
    Grabbing 50 candidates gives us a solid pool to apply deduplication and duration filters.
    """
    query = f"ytsearch50:{artist_name} songs"
    print(f"{Colors.OKCYAN}🔍 Searching YouTube for popular tracks of '{artist_name}'...{Colors.ENDC}")
    
    cmd = [
        "yt-dlp",
        "--flat-playlist",
        "--dump-single-json",
        "--no-warnings",
        "--quiet",
        query
    ]
    
    try:
        # Run command synchronously, capture output
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        data = json.loads(result.stdout)
        return data.get("entries", [])
    except subprocess.CalledProcessError as e:
        print(f"{Colors.FAIL}❌ Error running yt-dlp: {e.stderr.strip()}{Colors.ENDC}")
        return []
    except json.JSONDecodeError:
        print(f"{Colors.FAIL}❌ Error parsing YouTube search data. Make sure yt-dlp is updated.{Colors.ENDC}")
        return []
    except Exception as e:
        print(f"{Colors.FAIL}❌ Unexpected search error: {str(e)}{Colors.ENDC}")
        return []


def process_entries(entries, artist_name):
    """
    Filters, deduplicates, and sorts the entries strictly by views to find the top 20 unique songs.
    """
    processed = {}
    
    for index, entry in enumerate(entries):
        if not entry:
            continue
            
        title = entry.get("title", "")
        video_id = entry.get("id")
        url = entry.get("url") or f"https://www.youtube.com/watch?v={video_id}"
        
        if not title or not video_id:
            continue
            
        # 1. Clean the song title (strips metadata trash and artist tags)
        cleaned = clean_song_title(title, artist_name)
        if not cleaned:
            cleaned = title
            
        # 2. Duration filter (skip YouTube Shorts <60s or compilations/albums >10mins)
        try:
            duration = int(float(entry.get("duration") or 0))
        except (ValueError, TypeError):
            duration = 0
            
        if duration != 0 and (duration < 60 or duration > 600):
            continue
            
        # 3. View count extraction (default to 0 if missing)
        try:
            views = int(float(entry.get("view_count") or 0))
        except (ValueError, TypeError):
            views = 0
        
        track_info = {
            "id": video_id,
            "url": url,
            "original_title": title,
            "cleaned_title": cleaned,
            "view_count": views,
            "duration": duration,
            "search_rank": index  # Save rank as a fallback for popularity
        }
        
        # 4. Smart Deduplication: Keep only the upload with the HIGHEST view count
        cleaned_lower = cleaned.lower()
        if cleaned_lower not in processed:
            processed[cleaned_lower] = track_info
        else:
            if views > processed[cleaned_lower]["view_count"]:
                processed[cleaned_lower] = track_info
                
    candidates = list(processed.values())
    
    # 5. Sort strictly by view count descending
    # Fallback to YouTube relevance rank (search_rank) if views are absent/equal
    # Lower search_rank is more relevant, so we sort it ascending (using negative weight with reverse=True)
    candidates.sort(
        key=lambda x: (x["view_count"] or 0, -x["search_rank"]),
        reverse=True
    )
    
    # Return the top 20 candidates
    return candidates[:20]


def download_tracks(top_tracks, artist_name):
    """
    Downloads each filtered track individually, showing clean progress and isolating errors.
    """
    # Create the artist's directory
    folder_name = sanitize_filename(artist_name)
    os.makedirs(folder_name, exist_ok=True)
    
    total = len(top_tracks)
    print(f"\n{Colors.HEADER}{Colors.BOLD}📂 Organizing files in: '{folder_name}'{Colors.ENDC}")
    print(f"{Colors.HEADER}📥 Total tracks queued for download: {total}{Colors.ENDC}\n")
    
    success_count = 0
    failed_tracks = []
    
    for idx, track in enumerate(top_tracks, 1):
        title = track["cleaned_title"]
        sanitized_title = sanitize_filename(title)
        url = track["url"]
        
        # Output template directs yt-dlp to write directly into our directory with the clean title
        out_template = os.path.join(folder_name, f"{sanitized_title}.%(ext)s")
        
        # Safely convert duration to integer minutes/seconds
        duration_sec = int(float(track.get("duration") or 0))
        minutes = duration_sec // 60
        seconds = duration_sec % 60
        
        # Safely format view count
        views_val = int(float(track.get("view_count") or 0))
        
        print(f"{Colors.OKBLUE}[{idx}/{total}]{Colors.ENDC} Downloading: {Colors.BOLD}{title}{Colors.ENDC}")
        if views_val > 0:
            print(f"      Views: {views_val:,} | Duration: {minutes}:{seconds:02d}")
        else:
            print(f"      Duration: {minutes}:{seconds:02d}")
            
        cmd = [
            "yt-dlp",
            "-x",                           # Extract audio
            "--audio-format", "mp3",         # Convert to mp3 format
            "--audio-quality", "320k",       # Highest standard constant bitrate
            "--output", out_template,        # Output target path template
            "--no-playlist",                 # Focus strictly on this single track
            "--no-warnings",
            "--quiet",
            url
        ]
        
        try:
            # Execute download process synchronously
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
            print(f"      {Colors.OKGREEN}✓ Download and high-quality MP3 conversion successful!{Colors.ENDC}\n")
            success_count += 1
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.strip() if e.stderr else "Transcoding or download error"
            print(f"      {Colors.FAIL}✗ Download failed! Error Details: {error_msg}{Colors.ENDC}\n")
            failed_tracks.append((title, url, error_msg))
        except Exception as e:
            print(f"      {Colors.FAIL}✗ Unexpected error: {str(e)}{Colors.ENDC}\n")
            failed_tracks.append((title, url, str(e)))
            
    # Process Completion Summary
    print(f"\n{Colors.BOLD}{Colors.OKGREEN}==================================================")
    print(f"🎉 DOWNLOAD TASK COMPLETE!")
    print(f"=================================================={Colors.ENDC}")
    print(f"   Successfully Downloaded: {success_count} / {total}")
    
    if failed_tracks:
        print(f"\n{Colors.WARNING}⚠️ The following tracks encountered errors:{Colors.ENDC}")
        for name, url, err in failed_tracks:
            print(f"   - {Colors.BOLD}{name}{Colors.ENDC} ({url})")
            print(f"     Reason: {err}")
    print()


def main():
    print(f"{Colors.HEADER}{Colors.BOLD}==================================================")
    print("        ARTIST TOP 20 MP3 DOWNLOADER & CONVERTER")
    print(f"=================================================={Colors.ENDC}\n")
    
    # 1. Run environment dependency checks
    yt_dlp_ok, ffmpeg_ok = check_dependencies()
    
    if not yt_dlp_ok or not ffmpeg_ok:
        print(f"{Colors.FAIL}{Colors.BOLD}❌ Missing Critical Dependencies!{Colors.ENDC}")
        if not yt_dlp_ok:
            print(f"   - {Colors.BOLD}yt-dlp{Colors.ENDC} is not found in your system PATH.")
        if not ffmpeg_ok:
            print(f"   - {Colors.BOLD}ffmpeg{Colors.ENDC} is not found in your system PATH.")
        
        print(f"\n{Colors.OKCYAN}{Colors.BOLD}💡 Dependency Installation Instructions:{Colors.ENDC}")
        print(f"{Colors.BOLD}Windows (PowerShell):{Colors.ENDC}")
        print("   winget install yt-dlp")
        print("   winget install ffmpeg")
        print(f"\n{Colors.BOLD}macOS (Terminal):{Colors.ENDC}")
        print("   brew install yt-dlp ffmpeg")
        print(f"\n{Colors.BOLD}Linux (Debian/Ubuntu):{Colors.ENDC}")
        print("   sudo apt update && sudo apt install yt-dlp ffmpeg")
        print()
        sys.exit(1)
        
    # 2. Parse artist name from CLI arguments or prompt interactively
    artist_name = ""
    if len(sys.argv) > 1:
        artist_name = " ".join(sys.argv[1:]).strip()
    else:
        try:
            artist_name = input(f"{Colors.BOLD}Enter the name of the artist: {Colors.ENDC}").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nOperation cancelled by user.")
            sys.exit(0)
            
    if not artist_name:
        print(f"{Colors.FAIL}❌ Error: Artist name cannot be empty.{Colors.ENDC}")
        sys.exit(1)
        
    # 3. Retrieve metadata search entries
    entries = fetch_top_tracks(artist_name)
    if not entries:
        print(f"{Colors.FAIL}❌ No entries retrieved. Please check spelling, artist fame, or internet connection.{Colors.ENDC}")
        sys.exit(1)
        
    # 4. Clean titles, filter duration, deduplicate, and sort
    top_tracks = process_entries(entries, artist_name)
    if not top_tracks:
        print(f"{Colors.FAIL}❌ No items matched filtering criteria (valid music tracks).{Colors.ENDC}")
        sys.exit(1)
        
    # 5. Display identified top tracks
    print(f"\n{Colors.OKGREEN}✓ Top tracks identified (sorted strictly by views):{Colors.ENDC}")
    for idx, track in enumerate(top_tracks, 1):
        views_str = f"{track['view_count']:,} views" if track['view_count'] > 0 else "View count unavailable"
        print(f"   {idx:2d}. {Colors.BOLD}{track['cleaned_title']}{Colors.ENDC} ({views_str})")
        
    # 6. Execute downloads and audio extractions
    download_tracks(top_tracks, artist_name)


if __name__ == "__main__":
    main()
