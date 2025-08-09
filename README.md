# Renarrate

This is a GenAI powered pipeline for automatically narrating youtube video voice-overs. 

1) Clone repo
2) Install ffmpeg and ensure it's added to path
3) Install requirements.txt (ensure you have python 3.12 - haven't tested on earlier versions)
4) Rename .env.example to .env then paste in your api keys for Gemini and Elevenlabs (if you want to use just Gemini make sure to pick gemini voice for narration)
5) Open `main.py` and paste in your link the run the script and select your language 
6) Once the process is done you'll find path to your final video in the console, and at ./storage/{id}/final_video.mp4

It's a pretty clean code and there are some extra features like video converter, ability to pick from a bunch of predefined voices, or adjust how loud the original audio should be