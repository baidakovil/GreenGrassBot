<img src="./github-logo.jpg" width="30%" height="20%">

## Table of Contents
* [Introduction](#introduction)
* [Project structure](#project-structure)
* [Assets & Languages](#Assets-&-Languages)
* [Database](#code-documentation)
* [Services & UI](#services-&-ui)
* [Testing](#testing)

<div  style="page-break-after: always;"></div>

## Introduction
Please spare some time for *[README]* before reading this guide. This developer guide  
assumes its readers to have at least a basic understanding of [Python] and [Python Telegram Bot].


[README]: https://github.com/tjtanjin/simple-media-converter/blob/master/README.md
[Python]: https://www.python.org/
[Python Telegram Bot]: https://python-telegram-bot.org/

In this guinde, following syntaxes is used:

| Syntax               | Description                                                                       |
|----------------------|-----------------------------------------------------------------------------------|
| `Monotype`           | Denotes functions/commands (e.g. `create_group`, `create_user`, `/start`)         |    
| *Italics*            | Denotes folders/files in the projects (e.g. *main.py*, *services*)                |                                
| **Bold**             | Keywords that are emphasized                                                      |

<div  style="page-break-after: always;"></div>

## Project structure

At a high level overview, the entire project can be broken down into **4 components**:

- *assets* & *lang*
- *database*
- *commands* & *interactions**
- *services* & *ui*

Each of components corresponds to one or two folders in project structure. Below a short\
description of folders and files.

----------------------
Note: This tree not use syntax described above

.\
├── assets |                *RESOURSES*\
│   └── lang |                *TRANSLATION FILES*\
│                   ├── en.json\
│                   ├── ru.json |                *NAMED AS IETF LANGUAGE TAG*\
│                   └── uk.json\
│\
├── commands |                *CALLBACKS FOR TELEGRAM COMMANDS*\
│   ├── details.py |                *CALL FOR prepare_details_text()*\
│   ├── getgigs.py |                *+EVERYDAY JOB PROCEDURE. CALL FOR prepare_gigs_text()*\
│   ├── help.py |                *SIMPLE TEXT SENDER*\
│   ├── nonewevents.py |                *TOGGLE SETTING 0/1*\
│   ├── start.py |                *COMPLEX TEXT SENDER*\
│   └── warranty.py |                *SIMPLE TEXT SENDER*\
│\
├── db *DATABASE FILES*\
│   ├── db_service.py |                *CLASS DB AND FUNCTIONS FOR IT*\
│   ├── ggb_sqlite.db |                *SQLITE3 DATABASE CREATES BY BOT AT FIRST RUN*\
│   └── ggb_sqlite.sql |                *SQLITE3 CREATE SCRIPT, RECREATED WITH DBEAVER*\
│\
├── interactions |                *CONVERSATIONS AND AUX CONVERSATIONAL FILES*\
│   ├── common_handlers.py |                *CANCEL, UNKNOWN CMD, ERROR HANDLERS*\
│   ├── conn_lfm_conversation.py |                */CONNECT CONVERSATION*\
│   ├── delete_user_conversation.py |                */DELETE CONVERSATION*\
│   ├── disconn_lfm_conversation.py |                */DISCONNECT CONVERSATION*\
│   ├── loader.py |                */ADDING HANDLERS AT STARTUP* \
│   └── locale_conversation.py |                */LOCALE CONVERSATION*\
│\
├── scripts |                *DEPLOYING SCRIPTS*\
│   ├── deploy_docker.sh |                *DOCKER RUN COMMAND WRAPPER*\
│   └── greengrassbot.service-example |                *SYSTEMD CONFIG*\
│\
├── services |                *ESSENTIAL AND SECONDARY FUNCTIONS*\
│   ├── custom_classes.py |                *DATA-STORING CLASSES*\
│   ├── logger.py |                *LOGGER*\
│   ├── message_service.py |                *IMPORTANT. I18N, ESCAPE CHARS*\
│   ├── parse_services.py |                *LAST.FM API WRAPPER*\
│   ├── schedule_service.py |                *DAILY JOBS LOGIC*\
│   └── timeconv_service.py |                *CONVERTING TIME CONVENTIONS*\
│\
├── ui\
│   ├── commands_setter.py |                *SET TEXT FOR CMDS AT MENU BUTTON*\
│   ├── descriptions_setter.py |                *SET TWO 'ABOUT' DESCRIPTIONS*\
│   ├── error_builder.py |                *SIMPLE error_text() FUNC*\
│   └── news_builders.py |                *IMPORTANT. prepare_details_text(),\
│                                                                            prepare_gigs_text()*\
├── config.py |                *BOT SETTINGS, CONSTANTS*\
├── Dockerfile |                *REAL DOCKERFILE*\
├── LICENSE.md |                *GPL3 FROM gnu.org*\
├── logger.log |                *LOG FILE, CREATES OR APPENDS*\
├── main.py |                *MAIN FILE FOR CREATE DB AND APP, LAUNCH POLLING*\
├── pyproject.toml |                *ALMOST UNUSED*\
├── README.md |                *GITHUB README\
├── requirements.txt |                *CREATES WITH pipreqs*\
└── WORKFLOW.md |                *THIS FILE*

------------------

## Assets & Languages
*soon*

## Database
*soon*

## Commands & Interactions
*soon*

## Services & UI
*soon*

## Testing
