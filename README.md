# Renarrate

This is a GenAI powered pipeline for automatically narrating youtube video voice-overs. 

1) Clone repo
2) Configure .env
3) Run `docker compose build` and `docker compose up -d`
4) Install your chrome extension by going to `chrome://extensions/` and clicknig `Load Unpacked` then select the entire `extension` dir in this repo and accept
5) Click the extension icon in your browser and confirm BE url
6) Then click it again on any YT video link to send it to the backend for processing
![extension preview](extension.png)
7) You can click "See VO'ed videos" in the extension to see WebUI
![web ui preview](webui.png)

**IMPORTANT**
- It's super early PoC and it's buggy
- Works worse for longer videos, but quite great for shorter ones
- It costs some money to run via API costs
- If you end up bugging out the WebUI or the worker you can run POST request to `http://localhost:8000/admin/clear` to clear all
- Only tested while building a bit
- Read TO_DO to see what can be improved easily, I might have time but probably I won't 