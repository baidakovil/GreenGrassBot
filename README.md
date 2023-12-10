# Green Grass Bot

[![Pylint](https://github.com/baidakovil/GreenGrassBot/actions/workflows/pylint-workflow.yml/badge.svg)](https://github.com/baidakovil/GreenGrassBot/actions/workflows/pylint-workflow.yml) [![Docker](https://github.com/baidakovil/GreenGrassBot/actions/workflows/docker-publish.yml/badge.svg)](https://github.com/baidakovil/GreenGrassBot/actions/workflows/docker-publish.yml) [![Deployment](https://github.com/baidakovil/GreenGrassBot/actions/workflows/deployment.yml/badge.svg)](https://github.com/baidakovil/GreenGrassBot/actions/workflows/deployment.yml)


<img src=".github/readme-files/GitHubLogo.jpg" width="40%" height="40%">

----------------- 
## What is it?

Green Grass Bot notifies you about music concerts. It searches for musical events  
according to the artists you've been listening to lately. 🎶

The project gives listeners the freedom to know about musical events, regardless of the  
artists' advertising budgets. 🆓

Project gives artists the freedom to spread the news about their concerts, no matter  
what kind of advertisements their listeners watch.    🎸

What matters is what kind of music you listen to. Join
[Telegram](https://t.me/try_greatgigbot).

----------------- 

## Table of contents
- [General info](#general-info)
- [Technologies](#technologies)
- [Feedback](#feedback)
- [Setup](#setup)
- [Built with](#built-with)
- [Deployment](#deployment)
- [Contributing](#contributing)
- [Program logic](#program-logic)
- [Program name](#program-name)


## General info

As of the end of 2023, the project is actively developing with single contributor.  

The ultimate project goal is **to create an independent information "hub"** that  
collects information about concerts from as many sources as possible, and also collects  
user listening sessions (scrobbles) directly from music services.  

At the moment, both concerts and scrobbles are **obtained with Last.fm**, and concerts  
using html parsing, what is disadvantage now.

What GreenGrass Bot does in version 0.2-beta:

- Easy adds/removes Last.fm accounts on the `/connect`, `/disconnect` commands
- Monitors unlimited number of Last.fm accounts for each user (current deployment 3 max)
- Checks new concerts on request with `/getgigs` command
- Shows the date and place of concerts with one tap
- Automatically checks new scrobbles and new concerts daily
- Deletes all user data with a single `/delete` command

  <img src=".github/readme-files/connect-and-getgigs-process.gif" alt="How to connect Last.fm and get list of concerts"/>



## Technologies

  <img img width="240" src="https://www.python.org/static/community_logos/python-logo.png" alt="Python logo"/> 

  <img img width="160" src="https://www.sqlite.org/images/sqlite370_banner.gif" alt="SQLite Logo"/>

## Feedback

If you have any opinion about Green Grass Bot, I will appreciate if you send me any  
feedback on [my Telegram] — even two words will be helpful. Also you can [file an  
issue].  
Feature requests are welcome too.

## Setup 
You can setup you own concert notificator in five minutes. The bare minimum that needs  
to be done is for you to replace the `API_KEY` and `BOT_TOKEN` in `.env-example` and  
rename in to `.env`. [Telegram] and [Last.fm API] accounts are required. Commands below  
works for Linux; may be for Mac too.

1) Clone the project:
    ```
    $ cd /project_folder/
    $ git clone https://github.com/baidakovil/Green-Grass-Bot .
    ```

2) Open [BotFather], create telegram bot with `/newbot`. Pass provided **Bot Token** to  
    `.env` file using provided `.env-example` file

3) Same, insert **API Key** provided by Last.fm to `.env`

4) (Optional, recommended) Create dedicated virtual environment to use the bot and  
    activate it. I use *virtualenv*, some *venv*. Path and name are to your discretion. 
    ```
    $ cd /virtual_environments_folder/
    $ virtualenv env_name
    $ source env_name/bin/activate
    ```

5) With virtual env activated, `cd` into project folder and install dependencies:
    ```
    $ cd /project_folder/
    $ python3 -m pip install --no-cache-dir -r requirements.txt
    ```

6) Finally, execute the following command to launch your bot:
    ```
    $ python3 main.py
    ```

[my Telegram]: https://t.me/i_baidakov_ggb_support
[file an issue]: https://github.com/baidakovil/Green-Grass-Bot/issues/new
[BotFather]: https://t.me/BotFather
[Last.fm API]: https://www.last.fm/api/account/create
[Telegram]: https://telegram.org/

## Built with

#### Online-services (proprietary)
**[Last.fm]** - The world's largest online music service founded in 2002. Server proprietary  
**[Telegram]** - A cloud-based mobile and desktop messaging app founded in 2013.

#### Software
**[Python]** - Programming language that lets you work quickly and integrate systems  
  more effectively **|** GPL compatible  
**[APScheduler]** - Advanced Python scheduler coming with python-telegram-bot **|** MIT  
**[python-dotenv]** - Read key-value pairs from a .env file and set them as envir-t variables **|** BSD  
**[python-i18n]** - Translation library for Python **|** MIT  
**[python-telegram-bot]** - Python interface for the Telegram Bot API for Python >= 3.8 **|** GPL  

[Last.fm]: https://www.last.fm
[Telegram]: https://telegram.org
[Python]: https://www.python.org/
[python-telegram-bot]: https://github.com/python-telegram-bot/python-telegram-bot  
[APScheduler]: https://apscheduler.readthedocs.io/en/3.x/userguide.html  
[python-dotenv]: https://pypi.org/project/python-dotenv/
[python-i18n]: https://pypi.org/project/python-i18n/


## Deployment

#### Docker
Docker is simplest approach for deployment. If you are unfamiliar with docker, it is  
recommended you go through a quick tutorial for it first.

1) Create a *.env* file using [*.env-example*] and update **BOT_TOKEN** and **API_KEY** 
2) If you using the project as it is (**no intended code changes**), then simply run  
 `./scripts/deploy_docker.sh` and your deployment will be automatically done. 
 
3) If you made code changes, you should build docker image again. Refer to  Docker  
 tutorial [Update the application] section, your commands will looks like:
    ```
    $ cd /project_folder/
    $ docker build -t ggb .
    $ docker run -d --name green-grass-bot --env-file ../.env --restart=always ggb
    ```
`green-grass-bot`, `ggb`, up to your discretion.  
Notice: *.env* file we configured in **(1)** is being passed via the `--env-file` argument. 

#### Manual
Alternatively, if you are unfamiliar with docker or would like a more manual approach,  
you may also setup the bot 24/7. Two main approaches is:
* **systemd (systemctl)** Linux system, the way I do prefer. You will need to store provided file  
`greengrassbot.service` on your system in `/lib/systemd/system/`. You can use example in  
`scripts` folder.  
Note:  
to use `.github/deployment.yml` workflow for automatic deploy you'll need to set system rule  
for executing `sudo systemctl restart greengrassbot.service` command without password.  
[askUbuntu] on this topic.
* **screen** utility on Linux systems. For example, you can follow the [tjtanjin's guide].

[Update the application]: https://docs.docker.com/get-started/03_updating_app/
[askUbuntu]: https://askubuntu.com/a/878434
[*.env-example*]: https://github.com/baidakovil/green-grass-bot/blob/master/.env-example
[tjtanjin's guide]: https://gist.github.com/tjtanjin/ce560069506e3b6f4d70e570120249ed


## Contributing
If you wish to make code contributions to the project, you are welcome. What it need at  
most — professional **review** and **vectors of evolution**. 

## Program logic
*soon*

## Next steps
*soon*

## Program name

**Green Grass** refers to *High Hopes* popular *Pink Floyd*'s song. To be honest I do not like it much. 

**Title photo credit**: *American rock guitarist Jimi Hendrix performing with The Jimi Hendrix  
Experience at the Monterey Pop Festival, California, USA, June 18, 1967. Bruce Fleming/AP Images*