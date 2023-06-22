from pydub import AudioSegment
import os

def generate_final(audio_file_path, final_audio_file_path):
  # Load audio files, the static/theme.mp3 are located next to the main.py file
  intro = AudioSegment.from_mp3(os.path.abspath(__file__ + "/../../static/theme.mp3"))[:14000]
  audio = AudioSegment.from_mp3(audio_file_path)
  outro = AudioSegment.from_mp3(os.path.abspath(__file__ + "/../../static/theme.mp3"))[:14000]

  # Crossfade duration in milliseconds
  crossfade_duration = 11 * 1000  # 11 seconds

  # Combine intro and main audio with crossfade
  silence_5_seconds = AudioSegment.silent(duration=5000)
  audio = intro.append(silence_5_seconds + audio + silence_5_seconds, crossfade=crossfade_duration)

  # Add outro with crossfade
  final_audio = audio.append(outro, crossfade=crossfade_duration)

  # Export the final audio file
  final_audio.export(final_audio_file_path, format="mp3")

def get_length(audio_file_path):
  audio = AudioSegment.from_mp3(audio_file_path)
  return audio.duration_seconds