#!/config/Scripts/bin/python/install/bin/python3
import sys
from os import getenv, chdir, path
import subprocess
import logging
import pathlib

#Set Default Path Here
root = pathlib.Path(r'/config/Scripts')

#Important File Paths
log = root / 'Rip.log'
pypath = root / 'bin' / 'python' / 'install' / 'bin'
ffpath = root / 'bin' / 'ffmpeg'
# Installed Location for binaries
ffprobe = "./ffprobe"
ffmpeg = "./ffmpeg"

# Change dir to ffmpeg so commands can be run
chdir(ffpath)
#Setup Logging
logging.basicConfig(filename=log, format='%(asctime)s:%(levelname)s:%(message)s', level=logging.DEBUG)


# Variables
# Formats that are acceptable
extractable = ['ass']
# Languages codes that are acceptable
desirables = ['eng', 'en']
# ISO2 Language Code for desired language
desired_lang = 'en'
sub_ext = ".{}.default.srt".format(desired_lang)
# Get Event Type
evtype = getenv('sonarr_eventtype', None)
# Output Event Type
logging.info("Event Type: {}".format(evtype))
# Optionally, load overrides from Variables.py
# This allows users to have defaults that won't change, as this is .gitignore-ed
from Variables import *
# Run a subprocess and return the logs


def logProc(cmd):
    logging.info("Running {}...".format(cmd[0]))
    parse = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, error = parse.communicate()
    error = error.decode("utf-8")
    out = out.decode("utf-8")
    if error != '':
        logging.error(error)
    if out != '':
        logging.info(out)
    return (out, error)


# Extract Subtitles
def extract(f, track):
    f = str(f)
    name = f.split(".")[0]
    dest = name + sub_ext
    cmd = [ffmpeg,
           '-v', 'error',
           '-n', '-i', f,
           '-map', '0:{}'.format(track),
           dest]
    out, error = logProc(cmd)
    if path.exists(dest):
        logging.info("File Exists: {}".format(dest))
    else:
        logging.warning("File Doesn't Exist: {}".format(dest))
    return (out, error)

# Function that Analyzes and Rips Subs from Files, taking in file as f
def analyze(f):
    entry_format = 'stream=index:stream=codec_name:stream_disposition=default,forced:stream_tags=language'
    # Formatting Info
    info = {
        'track': 0,
        'codec': 1,
        'default': 2,
        'forced': 3,
        'lang': 4
    }
    cmd = [ffprobe,
            '-v', 'error',
            '-select_streams', 's',
            '-show_entries', entry_format,
            '-of', 'csv=p=0',
            f]
    # Run and return logs
    logging.info("Starting rip process for {}...".format(f))
    out, error = logProc(cmd)
    # Split lines
    rawsubs = list(out.splitlines())
    # Split into 2D array
    for i, x in enumerate(rawsubs):
        rawsubs[i] = x.split(",")
    # Remove Non-English
    subs = []
    for i, x in enumerate(rawsubs):
        # If the subtitle has a good language code
        if rawsubs[i][info['lang']] in desirables:
            # And if the subtitle is in a good format
            if rawsubs[i][info['codec']] in extractable:
                # Put that track in the list of good subtitles
                subs.append(rawsubs[i])
            else:
                logging.info(
                    "Track {} not extractable".format(rawsubs[i][info['track']]))
        else:
            logging.info(
                "Track {} not a desired language".format(rawsubs[i][info['track']]))

    # If there's only one track that is good, extract it
    if len(subs) == 0:
        logging.error("Found no valid subtitle tracks!")
    elif len(subs) == 1:
        logging.info(
            "Only one {} subtitle track, extracting...".format(subs[0][info['lang']]))
        out, error = extract(f, subs[0][info['track']])
        logging.info("Extracted? (See Above)")
    elif len(subs) == 2:
        logging.info("Found two subtitle tracks, attempting to deduce...")
        cmd = [ffprobe,
                '-v', 'error',
                '-select_streams', 'a',
                '-show_entries', entry_format,
                '-of', 'csv=p=0',
                f]
        out, error = logProc(cmd)
        # Split lines
        rawaudio = list(out.splitlines())
        # Split into 2D array
        for i, x in enumerate(rawaudio):
            rawaudio[i] = x.split(",")
        # Process Audio to determine Default Language
        sub_track = {}
        determiner = None
        for check in ['default', 'forced']:
            logging.debug(
                "Trying to differentiate based on flag: {}".format(check))
            for track in subs:
                if track[info[check]] == '1':
                    sub_track['default'] = track
                else:
                    sub_track['regular'] = track
            if len(list(sub_track)) == 2:
                determiner = check
                break
        if determiner is None:
            logging.error("No difference in flags, giving up!")
        else:
            logging.debug(
                "Found difference in flag: {}".format(determiner))
        logging.debug("Checking for two audio tracks...")
        answer = None
        if len(rawaudio) == 2:
            # If one is forced, and one is not, use the non-forced track
            if determiner == 'forced':
                answer = sub_track['regular']
            # If one is default, and one is not, figure out the correct track based on which audio is default
            if determiner == 'default':
                for i, x in enumerate(rawaudio):
                    if rawaudio[i][info['default']] == '1':
                        if rawaudio[i][info['lang']] in desirables:
                            logging.info(
                                "Determined that desired language is default, using non-default subtitle track!")
                            answer = sub_track['regular']
                        else:
                            logging.info(
                                "Determined that desired language is not default, using default subtitle track!")
                            answer = sub_track['default']

        else:
            logging.error(
                "Insufficient information to determine correct track, giving up!")
        if answer is not None:
            out, error = extract(f, answer[info['track']])
            logging.info("Extracted? (See Above)")
        else:
            logging.error(
                "Insufficient information to determine correct track, giving up!")

    else:
        logging.debug("Found {} subtitle tracks".format(len(subs)))
        logging.warning("More than two subtitle tracks, I give up!")


def main():
    # If no event type, error out
    if evtype is None:
        logging.warning("No event type specified!")
    # If testing, verify ffmpeg and ffprobe are installed and work
    elif evtype == 'Test':
        logging.info("Testing")
        logProc([ffmpeg])
        logProc([ffprobe])
        logging.info("Testing complete")
    # Where the magic happens - Triggers on imports from download clients
    elif evtype == 'Download':
        # Ignore upgrades, since we probably already have subtitles
        if getenv('sonarr_isupgrade') == True:
            pass
        # Get file name and path
        f = getenv('sonarr_episodefile_path')
        analyze(f)
    else:
        logging.warning("Unknown Event Type!")


# Put code in a try/except in order to facilitate better exception logging
try:
    main()
except Exception as err:
    logging.exception("Fatal error in main: {}".format(err))
