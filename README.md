# WhisperMate BOT

[![https://telegram.me/WhisperMateBot](https://img.shields.io/badge/💬_Bot_Telegram-WhisperMate-blue.svg)](https://telegram.me//WhisperMateBot) 
[![https://pypi.org/project/python-telegram-bot/](https://img.shields.io/pypi/pyversions/python-telegram-bot.svg)](https://pypi.org/project/python-telegram-bot/)

The BOT is hosted on [Heroku](https://www.heroku.com/), and it has been tested using Python `v3.11.4`. Also, [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) API and [sqlite3](https://docs.python.org/2/library/sqlite3.html) are needed.  

# How to host BOT on Heroku

1. Register on [Heroku](https://www.heroku.com/).
2. Download and install [Heroku CLI](https://devcenter.heroku.com/articles/getting-started-with-python#set-up) and [git](https://git-scm.com/downloads).
3. Create a project folder and put inside it the following files
        
       bot.py
       Procfile
       runtime.txt
       requirements.txt
       
   You can also have a `app.json` schema in order to declare environment variables, add-ons, and other information required to run an app on Heroku. More info [here](https://devcenter.heroku.com/articles/app-json-schema).

4. Put inside `Procfile`

       worker: python script.py
   
5. Put the python version you want to use in `runtime.txt`. 
   
    For instance, if you want to use Python `v3.11.4` just put inside the file:
   
       python-3.11.4

6. Specify explicit dependencies versions inside `requirements.txt`.
   
   For instance, I'm using [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) API.
   So my file `requirements.txt` will look like 
   
       python-telegram-bot==20.3
       
   To update this file, you can use the `pip freeze` command in your active virtual environment:
   
       pip freeze > requirements.txt
       
   More info [here](https://devcenter.heroku.com/articles/python-runtimes#selecting-a-runtime).
   
7. At this stage, if you haven't already, log in to your Heroku account and follow the prompts to create a new SSH public key
   
       heroku login
   
8. Create git repository   

       git init
           
    or clone this repo
    
       git clone https://github.com/sh1zen/WhisperMateBot.git
   
9. Create heroku app
   
       heroku create
   
10. Push your code (or deploy changes) into heroku app
   
        git add .
        git commit -m 'message'
        git push heroku master

11. Run your worker

        heroku ps:scale worker=1

12. Check logs with and enjoy your bot

        heroku logs --tail

#### Official Heroku Guide

Checkout also the official heroku guide: [Getting Started on Heroku with Python](https://devcenter.heroku.com/articles/getting-started-with-python#set-up).

# Resources

- [First steps](https://github.com/python-telegram-bot/python-telegram-bot/wiki/Extensions---Your-first-Bot)
- [Telegram Bot’s documentation](https://docs.python-telegram-bot.org/en/stable/index.html)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [Code snippets](https://github.com/python-telegram-bot/python-telegram-bot/wiki/Code-snippets)
