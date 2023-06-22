import whisper
import os
import datetime
from art import text2art
import re
import sys

from gpt import call as call_gpt
from utils import print_status
from audio import generate_final as generate_final_audio
from audio import get_length as get_audio_length
 
# Print the title
print(text2art("Blame.FM - Climo"))

# Check, if the user is in the blame.fm repository before continuing
# This is to prevent the user from accidentally running the script in the wrong directory
# The blame.fm repository contains folders like "content", "achetypes" and "static"
if not os.path.isdir("content") or not os.path.isdir("archetypes") or not os.path.isdir("static"):
    print("Please run this script in the blame.fm repository.")
    exit()

# Ask the user for the episode number
# The episode number can also be provided as a command line argument --> python main.py episode_number
if len(sys.argv) > 1:
    episode_number = sys.argv[1]
else:
    episode_number = input("Please enter the episode number: ")

# Check if the episode number is valid
if not episode_number.isdigit():
    print("The episode number is invalid.")
    exit(1)

print_status("Episode number: " + episode_number)

# Convert the episode number to 3 digits with leading zeros
episode_number_filled = episode_number.zfill(3)

# Check if there is already a final recording available in the folder "recordings/[episode number]"
# Search for the first .mp3 file in the folder, the name is not fixed
# If yes, ask the user, if the final recording should be used
# If no, ask the user for the path to the raw post processing audio file
final_audio_file_path = "recordings/" + episode_number_filled + "/final.mp3"
use_final_recording = False

if os.path.isdir("recordings/" + episode_number_filled):
    for file in os.listdir("recordings/" + episode_number_filled):
        if not file.endswith(".mp3"):
            continue

        final_audio_file_path = "recordings/" + episode_number_filled + "/" + file
        use_final_recording = input("A final recording has already been created. Do you want to use this recording? (Y/n) ") != "n"  

if not use_final_recording:
    print_status("No final recording available")

    # Search for a raw recording in the raw_recordings[episode number] folder
    # Search for the first .mp3 file in the folder, the name is not fixed
    # Generate code now
    raw_audio_file_path = None
    if os.path.isdir("raw_recordings/" + episode_number_filled):
        for file in os.listdir("raw_recordings/" + episode_number_filled):
            if not file.endswith(".mp3"):
                continue

            raw_audio_file_path = "raw_recordings/" + episode_number_filled + "/" + file
            break

    # Check if the file exists
    if not os.path.isfile(raw_audio_file_path):
        print("No raw recording available, please put the raw recording in the raw_recordings/" + episode_number_filled + " folder.")
        exit(1)

    print_status("Raw recording found, generating final recording: " + raw_audio_file_path)

    if not os.path.isdir("recordings/" + episode_number_filled):
        os.mkdir("recordings/" + episode_number_filled)

    # Generate the final audio file
    generate_final_audio(raw_audio_file_path, final_audio_file_path)

# Convert the audio length to a time format
audio_length_time_format = get_audio_length(final_audio_file_path)

# Check if the transcript file already exists
# Check for any txt file in the recordings/[episode number] folder
transcript_file_path = "recordings/" + episode_number_filled + "/transcript.txt"

if os.path.isfile(transcript_file_path):
    with open(transcript_file_path, "r") as f:
        transcript = f.read()

    print_status("Transcript loaded from file successfully")
else:
    # Transcribe the audio file
    model = whisper.load_model("tiny")
    result = model.transcribe(final_audio_file_path, language="German")
    transcript = result["text"]
    # Speichere das Transkript im Cache
    with open(transcript_file_path, "w") as f:
        f.write(transcript)

    print_status("Transcript generated successfully via Whisper")

# Default values for the episode summary, title and speaker list
summary = None
title = None
speaker_list = None

# Checking if the episode has already been created
# If yes, it should load the episode summary, title and number from the file
if os.path.isfile("content/episode/" + episode_number + ".md"):
    with open("content/episode/" + episode_number + ".md", "r") as f:
        episode = f.read()
    summary = re.search(r"Description = \"(.*)\"\n", episode).group(1)
    title = re.search(r"title = \"(.*)\"\n", episode).group(1)
    speaker_list = re.search(r"hosts = (.*)\n", episode).group(1)

    print_status("Episode loaded from file successfully")
    print_status("Found Summary: " + summary)
    print_status("Found Title: " + title)
    print_status("Found Speaker: " + speaker_list)

# Ask user, if the summary should be regerated, if the summary is already defined and of valid value
if summary is None or len(summary) == 0:
    summary = call_gpt(
        "gpt-3.5-turbo-16k", 
        "You are a person which is good at summarizing things. The summary should not be longer than 6 sentences. The summary should be in german. You are summorizing the text for good friend of you in a non formal way.", 
        "This is the text based content of the podcast Blame.FM. Please provide a summary of the podcast. Please always mention the number of the podcast episode within the summary. Please informal. Content:" + transcript
    )
    print_status("Summary: " + summary)

# Ask user, if the title should be regerated, if the title is already available
if title is None or len(title) == 0:
    title = call_gpt(
        "gpt-3.5-turbo",
        "You are a person which is good at giving text a proper titel which attrackts listeners to hear our podcast. The title needs to be be in german languag and should not be longer than 10 words. The title should be non-formal.",
        "This is the summary of the podcast, please provide a single title in german: " + summary
    )
    print_status("Title: " + title)

# Check if the speaker list is already available, if not generate it
if speaker_list is None or len(speaker_list) == 0:
    speaker = call_gpt(
        "gpt-3.5-turbo-16k",
        "You are good at detecting which people are part of the dicussion. Please only provide names of the people which are part of the discussion as a comma seperated list. Names of the people are limited to Stefan, Martin, Timo and Sebastian.",
        "Please answer with the name of the People in the format Name, Name2. This is the transcript: " + transcript
    )

    speaker_list_raw = '", "'.join(speaker.replace(" ", "").split(","))
    speaker_list = f'["{speaker_list_raw}"]'

    print_status("Speaker: " + str(speaker_list))

# Rename the final audio file to recordings/[episode number]/[episode number][title without special characters and spaces, words seperated by dots].mp3
final_audio_file = "recordings/" + episode_number_filled + "/" + episode_number_filled + "-" + title.replace(" ", ".").replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss").replace(":", "").replace("?", "").replace("!", "").replace(",", "").replace(";", "").replace("(", "").replace(")", "").replace("„", "").replace("“", "").replace('"', "").replace("'", "").replace("’", "").replace("‘", "")  + ".mp3"
os.rename(final_audio_file_path, final_audio_file)

print_status("Final audio file: " + final_audio_file)

episode_md = f"""
+++
Description = "{summary.replace('"', "")}"
author = "Stefan"
date = "{datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S%z")}"
episode = {episode_number}
episode_image = "img/blame-fm-podcast-logo.png"
svg = "owl"
background = "home"
#episode_banner = "img/episode/default-banner.jpg"
explicit = "no"
guests = []
hosts = {speaker_list}
sponsors = [""]
images = ["img/episode/default-social.jpg"]
news_keywords = []
podcast_duration = "{audio_length_time_format}"
podcast_file = "{final_audio_file}"
podcast_bytes = "{os.path.getsize(final_audio_file)}"
title = "{title.replace('"', "")}"
youtube = ""
truncate = ""
transcript = "{transcript.replace('"', "")}"
upcoming = false
categories = []
series = []
tags = []
hashero = false
+++

{summary}
"""

# Create the episode.md file
episode_md_file_path = "content/episode/" + episode_number + ".md"
with open(episode_md_file_path, "w") as f:
    f.write(episode_md)

print_status("Episode.md file create at: " + episode_md_file_path)
