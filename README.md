# Rip-Script
A Subtitle Rip Script For Sonarr

Rip Script is designed to work in the linuxserver/sonarr:latest container, but can likely be used outside with some customization.

In that case, first line should be replaced with:  
`#!/usr/bin/env python3`  
Likewise, if your python3 binary is located elsewhere, update the first line

## Setup
Rip Script requires Python3, ffmpeg, and ffprobe.  
None of these are available in the docker container this is designed for.  
Fortunately, I'm mounting /config, so I made a directory of `/config/Scripts` for my script, and `/config/Scripts/bin` for my portable binaries.  
1. Download [ffmpeg](https://johnvansickle.com/ffmpeg/) and [python3](https://github.com/indygreg/python-build-standalone).

2. Extract the files, and rename the folders to `ffmpeg` and `python` respectively, then move them to the `/config/Scripts/bin` folder.  

3. In Sonarr, Settings > Connect > Custom Scripts and add the script (Likely `/config/Scripts/Rip.py`).

4. Set On Import and On Rename, the rest can be off.

If you do anything different, modify the script accordingly. It's mostly setup to be easy enough to modify.

## Limitations
As far as the documentation shows, this will only trigger when a file is imported from a download client.
Manual imports will not trigger the script.