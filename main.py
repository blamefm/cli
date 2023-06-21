import whisper
from pydub import AudioSegment
import openai
import os
import time
import datetime
from art import text2art
import re

# Create ASCII art from the "Blame.FM" text
ascii_art = text2art("Blame.FM - Climo")

# Print the ASCII art in the console
print(ascii_art)

# Function to display the status of the application
def print_status(status):
    print(f"[{time.strftime('%H:%M:%S')}] {status}")

# File paths for intro, main audio, and outro
audio_file = "episode-20_postproduction-1_audio"
final_audio_file = audio_file + "_final.mp3"
transcript_file = audio_file + ".txt"

# Check if the final audio has already been created
if not os.path.isfile(final_audio_file):
  # Load audio files
  intro = AudioSegment.from_mp3("melody.mp3")[:14000]
  audio = AudioSegment.from_mp3(audio_file + ".mp3")
  outro = AudioSegment.from_mp3("melody.mp3")[:14000]

  # Crossfade duration in milliseconds
  crossfade_duration = 11 * 1000  # 11 seconds

  # Combine intro and main audio with crossfade
  silence_5_seconds = AudioSegment.silent(duration=5000)
  audio = intro.append(silence_5_seconds + audio + silence_5_seconds, crossfade=crossfade_duration)

  # Add outro with crossfade
  final_audio = audio.append(outro, crossfade=crossfade_duration)

  # Export the final audio
  final_audio.export(final_audio_file, format="mp3")
else:
  final_audio = AudioSegment.from_mp3(final_audio_file)

# Konvertieren der Länge in Stunden, Minuten und Sekunden
audio_length_time_format = str(datetime.timedelta(seconds=final_audio.duration_seconds))

print_status("Created final audio successfully")

# Check if the transcript file already exists
if os.path.isfile(transcript_file):
    with open(transcript_file, "r") as f:
        transcript = f.read()
else:
    # Transcribe the audio file
    model = whisper.load_model("medium")
    result = model.transcribe(final_audio_file, language="German")
    transcript = result["text"]
    # Speichere das Transkript im Cache
    with open(transcript_file, "w") as f:
        f.write(transcript)

print_status("Transcribed audio successfully")

openai.api_key_path = ".api-key"

def call_gpt(model, systemMessage, userMessage):
  while True:
    # Generate a response
    response = openai.ChatCompletion.create(
        model=model,
        messages=[
            {"role": "system", "content": systemMessage},
            {"role": "user", "content": userMessage},
        ]
    )

    # Print the choices
    choices = response["choices"]
    for i, choice in enumerate(choices):
        print_status(f"{i}: {choice['message']['content']}")

    # Ask the user to choose a response
    choice_index = input("\033[1m\033[32mPlease choose a response (0-x) or press Enter to generate a new one:\033[0m ")
    if choice_index == "":
        continue
    try:
        choice_index = int(choice_index)
        message = choices[choice_index]["message"]['content']
        break
    except (ValueError, IndexError):
        print_status("Invalid choice. Please choose a number between 0 and 4.")
        continue
    
  return message

summary = call_gpt(
    "gpt-3.5-turbo-16k", 
    "You are a person which is good at summarizing things. The summary should not be longer than 6 sentences. The summary should be in german.", 
    "This is the text based content of the podcast Blame.FM. Please provide a summary of the podcast. Please always mention the number of the podcast episode within the summary. Please informal. Content:" + transcript
)

print_status("Summary created successfully")

title = call_gpt(
    "gpt-3.5-turbo",
    "You are a person which is good at giving text a proper titel which attrackts listeners to hear our podcast. The title needs to be be in german languag and should not be longer than 10 words.",
    "This is the summary of the podcast, please provide a single title in german: " + summary
)

print_status("Title created successfully")

episode = call_gpt(
    "gpt-3.5-turbo",
    "Your answer only contains one number. There should be no content besides that in your answer.",
    "This is the transcript of the podcast, please provide the Episode Number: " + summary
)
episode_number = re.findall(r'\d+', episode)

print_status("Episode number created successfully")

speaker = call_gpt(
    "gpt-3.5-turbo-16k",
    "You are very good at detecting which people are part of the dicussion. Please provide names of the people which are part of the discussion as a comma seperated list. Names of the people are limited to Stefan, Martin, Timo and Sebastian. Only output a comma seperated list.",
    "This is the transcript of the podcast Blame.FM, please only provide the number of the episode of Blame.FM, nothing else: " + transcript
)

print_status("Speaker defined successfully")

speaker_list = speaker.replace(" ", "").split(",")

episode_md = f"""
+++
Description = {summary}
author = "Stefan"
date = "{datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S%z")}"
episode = {episode}
episode_image = "img/blame-fm-podcast-logo.png"
svg = "owl"
background = "home"
#episode_banner = "img/episode/default-banner.jpg"
explicit = "no"
guests = []
hosts = ['"' + {'", "'.join(speaker_list) + '"'}]
sponsors = [""]
images = ["img/episode/default-social.jpg"]
news_keywords = []
podcast_duration = "{audio_length_time_format}"
podcast_file = "{final_audio_file}"
podcast_bytes = "{os.path.getsize(final_audio_file)}"
title = "{title}"
youtube = ""
truncate = ""
transcript = "{transcript}"
upcoming = false
categories = []
series = []
tags = []
hashero = false
+++
"""

print_status("Create episode.md successfully")
print_status(episode_md)

with open(episode_number + ".md", "w") as file:
  # Write the episode.md file
  file.write(episode_md)