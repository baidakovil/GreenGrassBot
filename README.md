# Green Grass Bot

[![Pylint](https://github.com/baidakovil/GreenGrassBot/actions/workflows/pylint-workflow.yml/badge.svg)](https://github.com/baidakovil/GreenGrassBot/actions/workflows/pylint-workflow.yml) [![Docker](https://github.com/baidakovil/GreenGrassBot/actions/workflows/docker-publish.yml/badge.svg)](https://github.com/baidakovil/GreenGrassBot/actions/workflows/docker-publish.yml) [![Deployment](https://github.com/baidakovil/GreenGrassBot/actions/workflows/deployment.yml/badge.svg)](https://github.com/baidakovil/GreenGrassBot/actions/workflows/deployment.yml)


<img src="https://github.com/baidakovil/GreenGrassBot/blob/main/assets/logo/GitHubLogo.jpg" width="40%" height="40%">

----------------- 
## What is it?

Green Grass Bot notifies about music concerts. It searches for musical  
events according to the artists you've been listening to lately. 🎶

The project gives you the freedom to know about musical events, regardless  
of the advertising budgets of the artists. 🆓

Project gives artists the freedom to spread the news about their concerts,  
no matter what kind of advertisements their listeners watch.    🎸

What matters is what kind of music you listen to. Join in [Telegram](https://t.me/try_greatgigbot).

----------------- 

## Table of contents
- [General info](#general-info)
- [Features](#features)
- [Feedback](#feedback)
- [Technologies](#technologies)
- [Built with](#built-with)
- [Documentation](#documentation)
- [TODO](#todo)
- [Release Notes](#release-notes)
- [Support](#support)  


The bot use your __last.fm__ music statistics for searhcing those artists you prefer. 

- The only source to choose artists is your listened statistic

## Options and settings in developing:
- Work 'on query' and as automatic notificator
- Any public lastfm account can used: you may search events for your mom basing on your mom's listening
- User can choose which artists considering: all or listened at least twice for near last time

## Options and settings in developing:
- Country and city of Gig location
- Notification time and quantity

## Workflow in Telegram for userchat looks like 3 stages:
- I. Connecting to last.fm account just typing username in chat
- II. Getting list of artist with concerts in future — immediately or by schedule

<img src="https://user-images.githubusercontent.com/90848485/162991341-6d712501-cb84-4219-bc1c-3928c4c32b93.png" alt="First and second stages" width="500"/>



- II. If interested, detailed view to artist concert by tapping _/nn_ in artist list 
<img src="https://user-images.githubusercontent.com/90848485/162991339-f6fbe73e-b063-47f8-b08f-3de8c67b6404.png" alt="Third stage" width="500"/>


# Information about of concerts will parsed from:
- __last.fm__ event page
- __concert.ru__ or other event-aggregators
- separate sites of music halls, clubs
