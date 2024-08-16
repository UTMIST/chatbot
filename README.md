## UTMIST Discord Chatbot

# Setup:

- clone repo
- create a virtual environment (venv)
  - windows: `python -m venv utmist-chatbot-env`
  - mac/unix: `python3 -m venv utmist-chatbot-env`
- make sure you are in the project directory and activate the (venv).
  - windows (powershell): `utmist-chatbot-env\Scripts\activate`
  - windows (bash): `source utmist-chatbot-env/Scripts/activate`
  - mac/unix: `source utmist-chatbot-env/bin/activate`
- next install dependencies via `pip install requirements.txt`
  - if the above command fails run: `pip install --upgrade -r requirements.txt --user`
- add discord API key to discord_bot.py (hard coded for now)
- run the project via `python app/discord_bot.py`
