from Settings import settings

import os
from os.path import isfile, join

import logging
import re



def updateMKVFiles():
    mkvPath = settings['MKVFolderPath']

    for file in os.listdir(mkvPath):
        filepath = join(mkvPath, file)

        #Check if it is indeed a file, not a folder
        if not isfile(filepath):
            continue

        #Check that file is indeed an mkv file
        if not (len(file)>=4 and file[-4:] == ".mkv"):
            continue

        logging.info(f"Processing file: {file}")

        #Get the meta data from the file
        metadata = ""
        mkvInfoPath = join(settings['MKVToolNixPath'], 'mkvinfo.exe')
        stream = os.popen(f"\"{mkvInfoPath}\" \"{filepath}\"")
        metadata = stream.read()
        stream.close()
        logging.debug(metadata)

        #Search for correct subtitle track within meta data
        (japaneseAudioTracks, englishSubtitleTracks) = parseTracks(metadata)

        #Check that the above results are unique:
        if len(japaneseAudioTracks) == 0:
            logging.error(f"Japanese audio track not found. Skipping file.")
            continue
        if len(englishSubtitleTracks) == 0:
            logging.error(f"English subtitle track not found. Skipping file.")
            continue
        if len(japaneseAudioTracks) > 1:
            logging.warning(f"Japanese audio track not unique. Found {len(japaneseAudioTracks)}. Using first track.")
        if len(englishSubtitleTracks) > 1:
            logging.warning(f"English subtitle track not unique. Found {len(englishSubtitleTracks)}. Using first track.")
        
        #Delete default tracks in file
        mkvPropeditPath = join(settings['MKVToolNixPath'], 'mkvpropedit.exe')
        for i in range(1,21):
            stream = os.popen(f"\"{mkvPropeditPath}\" \"{filepath}\" --edit track:a{i} --set flag-default=0")
            stream.close()
            stream = os.popen(f"\"{mkvPropeditPath}\" \"{filepath}\" --edit track:s{i} --set flag-default=0")
            stream.close()
        
        #Set new default tracks
        audioNumber = japaneseAudioTracks[0][1]
        subNumber = englishSubtitleTracks[0][1]
        stream = os.popen(f"\"{mkvPropeditPath}\" \"{filepath}\" --edit track:{audioNumber} --set flag-default=1")
        stream.close()
        stream = os.popen(f"\"{mkvPropeditPath}\" \"{filepath}\" --edit track:{subNumber} --set flag-default=1")
        stream.close()

        #Output final meta data for debug
        stream = os.popen(f"\"{mkvInfoPath}\" \"{filepath}\"")
        metadata = stream.read()
        stream.close()
        logging.debug(metadata)

        logging.info("Updated file.")




def parseTracks(metadata):
    lines = str.split(metadata, "\n")

    #Find the starting and endpoints of individual tracks
    trackStartLines = []
    tracksStarted = False
    for i in range(0, len(lines)):
        line = lines[i]

        if line[:9] == "|+ Tracks":
            tracksStarted = True
            continue

        if tracksStarted:
            if line[:2] != "| ": # Check that we are still within the tracks environment
                trackStartLines.append(i)
                break

            if line[:] == "| + Track":
                trackStartLines.append(i)

    #Parse individual tracks
    japaneseAudioTracks = []
    englishSubtitleTracks = []
    for i in range(0, len(trackStartLines)-1):
        track = parseIndividualTrack(lines[trackStartLines[i]:trackStartLines[i+1]])
        if track[0] == "audio" and track[2] == "jpn":
            japaneseAudioTracks.append(track)
        if track[0] == "sub" and track[2] == "eng":
            englishSubtitleTracks.append(track)

    logging.debug(f"Japanese audio tracks: {japaneseAudioTracks}")
    logging.debug(f"English sub tracks: {englishSubtitleTracks}")
    return (japaneseAudioTracks, englishSubtitleTracks)





#Returns a tuple of the form (tracktype, number, language). tracktype is either "audio", "sub", or "" (if track was not parsed successfully). Video track will not be parsed.
def parseIndividualTrack(lines):
    tracktype = ""
    number = -1
    language = ""

    for line in lines:
        numberRegex = r".*Track number: ([0-9]*).*"
        match = re.match(numberRegex, line)
        if match:
            number = int(match.group(1))

        typeAudioRegex = r".*Track type: audio.*"
        match = re.match(typeAudioRegex, line)
        if match:
            tracktype = "audio"

        typeSubtitleRegex = r".*Track type: subtitles.*"
        match = re.match(typeSubtitleRegex, line)
        if match:
            tracktype = "sub"

        languageJpnRegex = r".*Language: jpn.*"
        match = re.match(languageJpnRegex, line)
        if match:
            language = "jpn"

        languageEngRegex = r".*Language: eng.*"
        match = re.match(languageEngRegex, line)
        if match:
            language = "eng"

    #Language field might not be properly set. Check whether the name field contains the string "english" as a backup
    if language == "":
        for line in lines:
            nameEngRegex = r".*Name:.*english.*"
            match = re.match(nameEngRegex, line, re.IGNORECASE)
            if match:
                language = "eng"


    #Check that both language and number have been found successfully. Otherwise clear the tracktype.
    if language == "" or number == -1:
        tracktype = ""

    return (tracktype, number, language)
        






if __name__ == "__main__":

    #Prepare Logging
    logginglevels = {
        "DEBUG" : logging.DEBUG,
        "INFO" : logging.INFO,
        "WARNING" : logging.WARNING,
        "ERROR" : logging.ERROR,
        "CRITICAL" : logging.CRITICAL,
    }
    logging.basicConfig(level=logginglevels.get(settings["LoggingLevel"], logging.ERROR), format = "LOGGING:%(levelname)s   %(message)s")

    updateMKVFiles()
    
