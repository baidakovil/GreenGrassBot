# GreenGrassBot


![Docker Cloud Automated build](https://img.shields.io/docker/cloud/automated/baidakovil/greengrassbot)



## Nice and Bads

| **What's nice**           |**Nice metric**                                                                                                |
|---------------------------|---------------------------------------------------------------------------------------------------------------|
| I am the only contributor |   ![GitHub commit activity (branch)](https://img.shields.io/github/commit-activity/m/baidakovil/GreenGrassBot)|


| **What's bad**            |**Bad metric**                                                                                                 |
|---------------------------|---------------------------------------------------------------------------------------------------------------|
| I am the only contributor | ![GitHub contributors](https://img.shields.io/github/contributors/baidakovil/GreenGrassBot)                   |


Green Grass Telegram Bot is a notificator abour music events.  

The bot provides automatic search and of music events (concerts, shows, festivals) according to music artists you have listen last time.  
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
