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
ffprobe = "./ffprobe"
ffmpeg = "./ffmpeg"

#Add Python to Path
sys.path.append(pypath)
#Change dir to ffmpeg
chdir(ffpath)
#Setup Logging
logging.basicConfig(filename=log, format='%(asctime)s:%(levelname)s:%(message)s', level=logging.DEBUG)

# Variables
extractable = ['ass']
desirables = ['eng']
glang = 'en'
sub_ext = ".{}.default.srt".format(glang)
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


if evtype == None:
    logging.warning("No event type specified!")
elif evtype == 'Test':
    logging.info("Testing")
    logProc([ffmpeg])
    logging.info("Testing complete")
elif evtype == 'Download':
    if getenv('sonarr_isupgrade') == True:
        pass
    f = getenv('sonarr_episodefile_path')
    cmd = [ffprobe,
           '-v', 'error',
           '-select_streams', 's',
           '-show_entries', 'stream=index:stream=codec_name:stream_tags=language',
           '-of', 'csv=p=0',
           f]
    #Formatting Info
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
        if rawsubs[i][lang] in desirables:
            if rawsubs[i][codec] in extractable:
                subs.append(rawsubs[i])
            else:
                logging.info(
                    "Track {} not extractable".format(rawsubs[i][track]))
        else:
            logging.info(
                "Track {} not a desired language".format(rawsubs[i][track]))

    # If there's only one track that can be extracted, extract it
    if len(subs) == 1:
        logging.info(
            "Only one {} subtitle track, extracting...".format(subs[0][lang]))
        out, error = extract(f, subs[0][track])
        logging.info("Extracted? (See Above)")
    else:
        logging.warning("More than one subtitle track, I give up!")
else:
    logging.warning("Unknown Event Type!")