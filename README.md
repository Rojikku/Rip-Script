# Rip-Script
A Subtitle Rip Script For Sonarr

Rip Script is designed to work in the linuxserver/sonarr:preview container, but can likely be used outside with some customization.

In that case, first line should be replaced with:  
`#!/usr/bin/env python3`  
Likewise, if your python3 binary is located elsewhere, update the first line

## Inspiration

When using Emby, on the TV version, if On The Fly subtitle ripping is turned on, there are situations where no subtitles will appear.

With On The Fly turned off, transcoding happens on many clients automatically, including the web client. This nearly doubles the required buffer time as compared to no subtitles.

However, if an external subtitle file is provided, this issue is minimized.
Therefore, it is more optimal to extract subtitles to an external file. This script is designed to automate as much of that as possible.

## Setup
Rip Script requires Python3, ffmpeg, and ffprobe.  
None of these are available in the docker container this is designed for.  
Fortunately, I'm mounting /config, so I made a directory of `/config/Scripts` for my script, and `/config/Scripts/bin` for my portable binaries.  
1. Download [ffmpeg](https://johnvansickle.com/ffmpeg/) and [python3](https://github.com/indygreg/python-build-standalone).

2. Extract the files, and rename the folders to `ffmpeg` and `python` respectively, then move them to the `/config/Scripts/bin` folder.  

3. (Optionally) Make a sync.sh script in the git directory, which is in .gitignore, to rsync the Rip.py script into `/config/Scripts`.

4. Run your sync.sh script from above, or copy the Rip.py script over to `/config/Scripts/Rip.py`.

5. In Sonarr, Settings > Connect > Custom Scripts and add the script (Likely `/config/Scripts/Rip.py`).

6. Set On Import and On Rename, the rest can be off.

If you do anything different, modify the script accordingly. It's mostly setup to be easy enough to modify.

## Customization
Since it would be annoying to change the larger variables every time you update the script, I added an import for Variables.py (I attached an example).

You can simply set your variables in Variables.py, and it should override the ones in the script.

## Limitations
* As far as the documentation shows, this will only trigger when a file is imported from a download client.
Manual imports will not trigger the script.
* Can't figure out the correct track if there's more than two subtitle tracks

## Manual Fixes
If you get a wrong track, just go into the directory where the wrong subtitles exist, and do something like:
```
rm *.srt
for f in *.mkv; do ffmpeg -n -i "$f" -map 0:s:X "$(echo $f | sed s/.mkv/.en.default.srt/)"; done
```
With X in 0:s:X being the correct subtitle track, or 0:X if you use the absolute number, instead of just the first or second subtitle track.

### Manual Mode

Alternatively, if you have existing content, or manually imported content, and want to run the script on it, you now can with manual mode.
```
sonarr_eventtype="Manual" ./Rip.py
```
Using a format like so, from the directory of the series, it should work fine.
Personally, I copy Rip.py to Test.py, and change the variables since I'm running it from a different context.
I call it by full path.

Manual mode will check every folder inside your working directory, and then rip subtitles from all .mkv files in those subdirectories.

### Logs
If you have access to the Rip.log, it's nice to watch the progress with `tail -f Rip.log` or a similar command.  
All output goes to this log file instead of the console due it being designed for an environment where a console is not convenient (A docker container).