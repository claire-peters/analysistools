# Claire Peters, October 2019
# Script feeds multiple directories of recorded audio files through Google
# Cloud's Speech-to-Text API to produce searchable .txt transcripts.

import argparse
import datetime
import io
import os
import sys
from google.cloud import speech_v1p1beta1 as speech
from google.cloud.speech_v1p1beta1 import enums
from google.cloud.speech_v1p1beta1 import types
from mutagen.mp3 import MP3

# Record .mp3 metadata.
def collect_metadata(speech_file):
    file_path = speech_file
    mod_time = datetime.datetime.fromtimestamp(os.path.getmtime(speech_file))
    audio = MP3(speech_file)
    print('filepath:', file_path, file=f)
    print('modtime:', mod_time, file=f)
    print('length in seconds:', audio.info.length, end='\n\n', file=f)

# Use Google Cloud API for transcription of locally hosted files.
def transcribe_file(speech_file):
    """Transcribe the given audio file asynchronously."""
    client = speech.SpeechClient()

    with io.open(speech_file, 'rb') as audio_file:
        content = audio_file.read()

    audio = types.RecognitionAudio(content=content)
    config = {
        # Encoding and metadata enums pulled from https://git.io/JeVSX
    	"encoding": 8,
        "metadata": {
        "recording_device_type": 3
        },
    	"enable_automatic_punctuation": True,
        # Enter sample rate - should be available in audio file properties.
        "sample_rate_hertz": 8000,
        # Enter language code. Options list at https://bit.ly/32xIkjJ.
        "language_code": 'en-US',
        # Add up to two alternate language codes if needed.
        "alternative_language_codes": ['en-CA', 'en-GB'],
        # Add specific words or phrases to increase transcription accuracy.
        # More information at https://bit.ly/2NyOxYe and https://bit.ly/2NAOlbb.
        "speech_contexts": [{
            "phrases": [
                "Good afternoon",
                "Good evening",
                "Good morning",
            ],
            # boost value determining bias toward phrasing, value of 1-20.
            # Feature only available for en_US (https://bit.ly/2NAOlbb)
            "boost": 10,
        }],
    }
    operation = client.long_running_recognize(config, audio)

    print('Transcribing your local audio file...')
    response = operation.result(timeout=10000)

    # Each result is for a consecutive portion of the audio. Iterate through
    # them to get the transcripts for the entire audio file.
    for result in response.results:
        print('Transcript:', file=f)
        print(format(result.alternatives[0].transcript), end='\n\n', file=f)
        print('Confidence: {}'.format(result.alternatives[0].confidence), file=f)
    # [END speech_python_migration_async_response]

# Specify as "exten" the extension of the audio files to be processed.
exten = '.mp3'

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'path', help='Directory to scan')
    args = parser.parse_args()
    for dirpath, dirnames, files in os.walk(args.path):
        for fullname in files:
            (name, ext) = os.path.splitext(fullname)
            if ext == exten:
                fullpathname = os.path.join(dirpath, fullname)
                # Saves the .txts in original file's directory. To save .txts to
                # one directory, replace "dirpath" with the desired directory.
                f = open(dirpath + '/' + name + '.txt',"w+")
                print("collecting for:" + fullpathname)
                collect_metadata(fullpathname)
                transcribe_file(fullpathname)
                f.close()
