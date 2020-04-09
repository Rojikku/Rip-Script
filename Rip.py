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
        cmd = [ffprobe,
               '-v', 'error',
               '-select_streams', 's',
               '-show_entries', 'stream=index:stream=codec_name:stream_tags=language',
               '-of', 'csv=p=0',
               f]
        # Formatting Info
        track = 0
        codec = 1
        lang = 2
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
            if rawsubs[i][lang] in desirables:
                # And if the subtitle is in a good format
                if rawsubs[i][codec] in extractable:
                    # Put that track in the list of good subtitles
                    subs.append(rawsubs[i])
                else:
                    logging.info(
                        "Track {} not extractable".format(rawsubs[i][track]))
            else:
                logging.info(
                    "Track {} not a desired language".format(rawsubs[i][track]))

        # If there's only one track that is good, extract it
        if len(subs) == 1:
            logging.info(
                "Only one {} subtitle track, extracting...".format(subs[0][lang]))
            out, error = extract(f, subs[0][track])
            logging.info("Extracted? (See Above)")
        else:
            logging.warning("More than one subtitle track, I give up!")
    else:
        logging.warning("Unknown Event Type!")

# Put code in a try/except in order to facilitate better exception logging
try:
    main()
except Exception as err:
    logging.exception("Fatal error in main: {}".format(err))
