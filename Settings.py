from yaml import load, dump, YAMLError

import logging


settings = {}

__defaultSettings = {
    'LoggingLevel': 'INFO',
    'MKVToolNixPath': '', # Folder path where MKVToolNix is installed
    'MKVFolderPath': '' # Path of the folder which contains the MKV files that should be updated
    }


#Read the settings.yml file
try:
    with open('settings.yml', 'r') as file:
        settings = load(file)
        if settings is None:
            settings = {}
except YAMLError as e:
    logging.error('Your settings.yml file could not be parsed. Using default config. Try fixing or deleting your settings.yml file to get rid of this error.')
    settings = __defaultSettings
except FileNotFoundError as e:
    with open('settings.yml', 'w') as file:
        file.write(dump(__defaultSettings))
    settings = __defaultSettings
else:
    
    #If some options were not present in the settings.yml file, use the default instead
    for key in __defaultSettings:
        if key not in settings:
            settings[key] = __defaultSettings[key]


#print (settings)
#print (__defaultSettings)


