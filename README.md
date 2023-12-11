# Green Grass Bot

[![Pylint](https://github.com/baidakovil/GreenGrassBot/actions/workflows/pylint-workflow.yml/badge.svg)](https://github.com/baidakovil/GreenGrassBot/actions/workflows/pylint-workflow.yml) [![Docker](https://github.com/baidakovil/GreenGrassBot/actions/workflows/docker-publish.yml/badge.svg)](https://github.com/baidakovil/GreenGrassBot/actions/workflows/docker-publish.yml) [![Deployment](https://github.com/baidakovil/GreenGrassBot/actions/workflows/deployment.yml/badge.svg)](https://github.com/baidakovil/GreenGrassBot/actions/workflows/deployment.yml)


<img src=".github/readme-files/github-logo.jpg" width="40%" height="40%">

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
- [Built with](#built-with)
- [Deployment](#deployment-with-docker)
- [Contributing](#contributing)
- [Program logic](#program-logic)
- [Program name](#program-name)


## General info

As of the end of 2023, the project is in **Python** and is actively developing with single contributor.

The ultimate project goal is **to create an independent information "hub"** that  
collects information about concerts from as many sources as possible, and also collects  
user listening sessions (scrobbles) directly from music services.  

At the moment, both concerts and scrobbles are **obtained with Last.fm proprietary  
service**. More of that, concerts obtained using html parsing, what is disadvantage now.\

SQLite3 single-file database: [schema], [class Db].

What Green Grass Bot does in version 0.2-beta:

- Easy adds/removes Last.fm accounts on the `/connect`, `/disconnect` commands
- Monitors unlimited number of Last.fm accounts for each user (current deployment 3 max)
- Checks new concerts on request with `/getgigs` command
- Shows the date and place of concerts with one tap
- Automatically checks new scrobbles and new concerts daily
- Change bot language with `/locale`: `en`, `ru`, `uk` localizations are there
- Deletes all user data with a single `/delete` command

  <img width="300" src=".github/readme-files/connect-and-getgigs-process.gif" alt="How to connect Last.fm and get list of concerts"/>

  [schema]: .github/readme-files/db.png
  [class Db]: db/db_service.py

## Technologies

  <img width="200" src="https://www.python.org/static/community_logos/python-logo.png" alt="Python logo"/>  <img width="170" src="https://www.sqlite.org/images/sqlite370_banner.gif" alt="SQLite Logo"/>

## Feedback

If you have any opinion about Green Grass Bot, I will appreciate if you send me any  
feedback on [my Telegram] — even two words will be helpful. Also you can [file an issue].  
Feature requests are welcome too.

[my Telegram]: https://t.me/i_baidakov_ggb_support
[file an issue]: https://github.com/baidakovil/Green-Grass-Bot/issues/new


## Built with

#### Online-services
**[Last.fm]** - The world's largest online music service founded in 2002 **|** *proprietary*  
**[Telegram]** - A cloud-based messaging app founded in 2013 **|** *proprietary*

#### Software
**[Python]** - Language to work quickly and integrate systems more effectively **|** *GPL compatible*  
**[APScheduler]** - Advanced Python scheduler coming with python-telegram-bot **|** *MIT*  
**[python-dotenv]** - Read key-value pairs from a .env file and set them as envir-t variables **|** *BSD*  
**[python-i18n]** - Translation library for Python **|** *MIT*  
**[python-telegram-bot]** - Python interface for the Telegram Bot API for Python >= 3.8 **|** *GPL*  

***Note**: As a designer and programmer, I have nothing to do with any of these services  
or softwares. As a user of the Last.fm for 15 years, I have a positive opinion about Last.fm.*  

[Last.fm]: https://www.last.fm
[Telegram]: https://telegram.org
[Python]: https://www.python.org/
[python-telegram-bot]: https://github.com/python-telegram-bot/python-telegram-bot  
[APScheduler]: https://apscheduler.readthedocs.io/en/3.x/userguide.html  
[python-dotenv]: https://pypi.org/project/python-dotenv/
[python-i18n]: https://pypi.org/project/python-i18n/


## Deployment 24/7

This section assumes you have server: VPS, VDS or old computer in garage with internet.\
There are two main ways to deploy the bot:
- **Docker software**. It's free for personal use
- **manual deploy**, with Python installed on your system.

### Accounts prepare
In both cases, bare minimum that needs to be done is for you to:
- with your Telegram account, open [BotFather] and create telegram bot with `/newbot`.  
 You'll get **Bot Token**. Update **BOT_TOKEN** in `.env-example` file with provided **Bot Token** 

- create [Last.fm API] account. You'll get **API key**. Update **API_KEY** in `.env-example`  
 file with provided **API key**.

 - rename `.env-example` to `.env`. Keep this file secure.

### Deployment with Docker

Docker is simplest approach for deployment. If you are unfamiliar with docker, it is  
recommended you go through a [quick tutorial] for it first. Commands below works for Linux;  
may be for Mac too.


1) Create a *.env* file as described in **[accounts prepare](#accounts-prepare)**  section.
2) If you are using the project as it is (**no intended code changes**), then simply download  
 `scripts/deploy_docker.sh` file, put it in subfolder (e.g. `scripts`) and run it in CLI: 
    ```
    $ cd /folder-with-.env/scripts
    $ deploy_docker.sh
    ```
    Your deployment will be automatically done.
 
3) If you want to make code changes, you should load project with source files. After  
    changing the code, build docker image as shown below.
    ```
    $ cd /project_folder/
    $ git clone https://github.com/baidakovil/Green-Grass-Bot .
    ---- MAKE CODE CHANGES ----
    $ docker build -t ggb .
    $ docker run -d --name green-grass-bot --env-file ../.env --restart=always ggb
    ```

    Notices:
    - `project_folder`, `green-grass-bot`, `ggb` names are up to your discretion
    - may be you want to look at [Update the application] Docker tutorial section
    - *.env* file is being passed via the `--env-file` argument
    - you can run bot without server, withour docker installed, having only browser and\
    Docker account. For this, go to [Docker playground], log in and paste to CLI this line:
        ```
        $ docker run --env API_KEY=<<you_api_key>> --env BOT_TOKEN=<<your_bot_token>> baidakovil\greengrassbot:stable
        ```

### Manual deployment

Manual approach is good when you are unfamiliar with Docker, or your VPS not satisfy Docker's  
[system requirements], or you prefer manual approaches. 

1) Create a *.env* file as described in **[accounts prepare](#accounts-prepare)**  section.

1) Create project folder and clone the project:
    ```
    $ cd /projects/project_folder/
    $ git clone https://github.com/baidakovil/Green-Grass-Bot .
    ```

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

6) Try to run the bot (not good for 24/7 deployment) by running main.py file:
    ```
    $ python3 main.py
    ```
7) Choose one of approaches to sustainable deploy 7/24/365. Most known are: 
    - **systemd** - Linux process manager, default in many distributives (e.g. Ubuntu)  
    the way I do prefer. With this, you'll need to create a file for **systemd** with  
    deploy settings. As example of this file, use `greengrassbot.service-example`\
    file in `scripts`.  
    As shortest as possible manual, possibly missing some steps needed in your system,  
    include these steps:
        1. Insert paths to `greengrassbot.service-example` file  
        2. Delete `-example` from the filename  
        3. Copy the file to `/lib/systemd/system/`  
        4. Run in CLI: `sudo systemctl start greengrassbot`  
    
    - **screen** - utility for Linux systems. I never used it, but there is a signs it  
    popular. For sample tutorial, I think, you can follow the [tjtanjin's guide].


    *Note:*  to use `.github/deployment.yml` workflow for automatic deploy you'll need to  
    set system rule for executing `sudo systemctl restart greengrassbot.service` command  
    without password. [askUbuntu] on this topic.


[Docker playground]: http://play-with-docker.com/
[quick tutorial]: https://docs.docker.com/get-started/
[Last.fm API]: https://www.last.fm/api/account/create
[Telegram]: https://telegram.org/
[BotFather]: https://t.me/BotFather
[system requirements]: https://docs.docker.com/desktop/install/linux-install/
[Update the application]: https://docs.docker.com/get-started/03_updating_app/
[askUbuntu]: https://askubuntu.com/a/878434
[*.env-example*]: https://github.com/baidakovil/green-grass-bot/blob/master/.env-example
[tjtanjin's guide]: https://gist.github.com/tjtanjin/ce560069506e3b6f4d70e570120249ed

## Contributing
If you wish to make code contributions to the project, you are welcome. What it need at  
most — professional **review** and **vectors of evolution**. 

## Program logic
Please look for [Developer Guide]

## Next steps
*soon*

## Program name

**Green Grass** refers to *High Hopes* popular *Pink Floyd*'s song. To be honest I do not like it much. 

**Title photo credit**: *American rock guitarist Jimi Hendrix performing with The Jimi Hendrix  
Experience at the Monterey Pop Festival, California, USA, June 18, 1967. Bruce Fleming/AP Images*

[Developer Guide]: /.github/readme-files/DEVELOPER_GUIDE.md