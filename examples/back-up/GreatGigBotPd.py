#!/usr/bin/env python
# coding: utf-8
# -*- coding: utf-8 -*-
import logging
import urllib.parse
from datetime import date, datetime
from typing import Dict
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
import GreatGigBotLibPd as ggbl
from pathlib import Path
import pandas as pd
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    PicklePersistence,
    CallbackContext,
)

Path('connectBot').unlink(missing_ok=True)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

def start(update, context):
    userId = context.user_data['userId']
    context.bot.send_message(chat_id=userId,
                             text='<a href="https://www.last.fm/user/trygreatgigbot">Link</a>', 
                             parse_mode='HTML')
  
def echo(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.text)

def error(update, context):
    logger.warning('Update "%s" caused error "%s"', update, context.error)
 
def caps(update, context):
    text_caps = ' '.join(context.args).upper()
    context.bot.send_message(chat_id=update.effective_chat.id, text=text_caps)      

#START CONVERSATION

USERNAME, TRACKCOUNTS, RUNSEARCH = range(3)

def removeJob(name: str, context: CallbackContext) -> bool:
    """Remove job with given name. Returns whether job was removed."""
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True

def factsToStr(user_data: Dict[str, str]) -> str:
    """Helper function for formatting the gathered user info."""
    facts = [f'{key} - {value}' for key, value in user_data.items()]
    return "\n".join(facts).join(['\n', '\n'])

def connectLastm(update: Update, context: CallbackContext) -> int:
    """Starts the conversation and asks the user about lastfmUser."""
    user = update.message.from_user
    context.user_data['userId'] = user.id
    update.message.reply_text('Enter lastfm\'s profile name')
    return USERNAME


def username(update: Update, context: CallbackContext) :
    """Waits for lastfmUser"""
    user = update.message.from_user
    lastfmUser = update.message.text.lower()
    context.user_data['lastfmUser'] = lastfmUser
    logger.info('User %s enters username: %s', user.first_name, lastfmUser)
    update.message.reply_text('Haha, now many hours of listening will I load?')
    return TRACKCOUNTS


def trackcounts(update: Update, context: CallbackContext) :
    """Waits for days to load"""
    reply_keyboard = [['Yes', 'No']] 
    daysDelta = update.message.text
    userId = update.message.from_user.id
    context.user_data['daysDelta'] = daysDelta
    lastfmUser = context.user_data['lastfmUser']
    logger.info('User %s enters hours: %s', userId, daysDelta)
    
    timeToGetEvents = 3
    job_removed = removeJob(userId, context)
    logger.info('Job removed if any')
    context.job_queue.run_once(getEventsJob, timeToGetEvents, 
                        context=context, name=str(userId))
    logger.info('Timer set to %s sec', timeToGetEvents)
    
    dataToWrite = str(context.user_data)
    ggbl.writeData(str(userId),dataToWrite)
    logger.info('Data is written for'+str(userId))
    
    update.message.reply_text('Huhu, now, run the search?',
                reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder='Yes or No?') )
    return RUNSEARCH
    
def runsearch(update: Update, context: CallbackContext) :
    user = update.message.from_user
    chat_id = update.message.chat_id
    logger.info('User %s will run search: %s', user.first_name, update.message.text)

    eventBasket = ggbl.getLastfmEvents(
        lastfmUser = context.user_data['lastfmUser'],
        daysDelta = int(context.user_data['daysDelta']),
        minListens = 3)
    logger.info('EB done')
    if eventBasket == {} :
        update.message.reply_text('No concerts (',reply_markup=ReplyKeyboardRemove())
    else :
        eventString = ggbl.prettyThree(eventBasket)
        update.message.reply_text(eventString,reply_markup=ReplyKeyboardRemove())
   
    return ConversationHandler.END
           
def skiprunsearch(update: Update, context: CallbackContext) :
    user = update.message.from_user
    logger.info('User %s skips search', user.first_name)
    update.message.reply_text('Bye',reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END
    
def cancel(update: Update, context: CallbackContext):
    """Cancels and ends the conversation."""
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    update.message.reply_text(
        'Bye! I hope we can talk again some day.', 
        reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END

def getEvents (update: Update, context: CallbackContext) :
    eventBasket = ggbl.getLastfmEvents(
        lastfmUser = context.user_data['lastfmUser'],
        daysDelta = int(context.user_data['daysDelta']),
        minListens = 3)
    if eventBasket == {} :
        update.message.reply_text('No concerts (',reply_markup=ReplyKeyboardRemove())
    else :
        eventString = ggbl.prettyThree(eventBasket)        
        update.message.reply_text(eventString,reply_markup=ReplyKeyboardRemove())

def getEventsJob(context: CallbackContext) :
    """
    1) отправляет в чат список исполнителей с новыми концертами
    2) обновляет список всех когда-либо полученных концертов (sentEvents)
    3) обновляет список концертов, доступных по команде "/хх" (lastEvents)
    """
    # сбор информации
    logger.info('Start getEventsJob')
    job = context.job
    user_data = job.context.user_data
    userId = user_data['userId']
    lastfmUser = user_data['lastfmUser']
    daysDelta = int(user_data['daysDelta'])
    if 'sentEvents' in user_data :
        sentEvents = user_data['sentEvents']
        logger.info('sentEvents in user_data')
    else :
        logger.info('sentEvents not in user_data')
        sentEvents = pd.Series([], dtype='boolean')
        old = sentEvents
    
    # чистка копии списка к-л отправленных концертов, если он есть
    if not sentEvents.empty :      
        logger.info('start checking old events in sendEvents')
        chkSentEvents = sentEvents.copy()
        today = pd.to_datetime(date.today())
        eventTimes = pd.to_datetime(sentEvents.loc[:,'eventtime'])
        oldEvents = chkSentEvents[eventTimes < today].index
        chkSentEvents = sentEvents.drop(oldEvents).copy()
        chkSentEvents.reset_index(drop = True,inplace = True)
        logger.info(len(oldEvents), ' events was deleted') 
        old = chkSentEvents['eventid']
        user_data['sentEvents'] = chkSentEvents
        logger.info('chkSentEvents added to user_data')

    # получение списка концертов
    twice = False
    places = {}
    eventsDf = ggbl.getLastfmEvents(lastfmUser,int(daysDelta),twice,places,old)  
    logger.info('eventsDf done')
    infoText = ggbl.getInfoText(eventsDf)
    user_data['lastEvents'] = eventsDf
    # отправка сообщения и сохранение списка отправленных концертов в user_data['eventBasket']
    context.bot.send_message(userId, text=infoText, parse_mode='MarkdownV2')

    newEvents = eventsDf.copy()
    newEvents.loc[:, 'eventnumber'] = ''
    if not sentEvents.empty :
        user_data['sentEvents'] = chkSentEvents.append(newEvents)
    else :
        user_data['sentEvents'] = newEvents
    logger.info('sentEvents written to pickle')
       
    # запись всех данных в файл 
    dataToWrite = str(user_data)
    ggbl.writeData(str(userId),dataToWrite)
    logger.info('Data is written for '+str(userId))
    
    logger.info('Job done')

def alChar(text) :
    alarmCharacters = ('-','(',')','.','+','!','?','"','#')
    safetext = "".join([c if c not in alarmCharacters else f'\\{c}' for c in text])    
    return safetext



def showNews(update, context) :


    userId = update.message.from_user
    command = update.message.text
    eventsDf = context.user_data['lastEvents']
    artistsDf = eventsDf.loc[eventsDf.eventnumber == command]
    logger.info('data get')
    
    ids = artistsDf['eventid'].sort_values()
    prevCountry = None
    showEvents = list()
    for i in range(0,len(artistsDf)) :
        event = artistsDf.loc[artistsDf.eventid == ids.iat[i]]
        eventTime = datetime.strptime(event.eventtime.values[0],'%Y-%m-%d').strftime('%d %b %Y')
        artist = event.eventartist.values[0]
        eventCountry = event.eventcountry.values[0]
        eventCity = event.eventcity.values[0]
        eventVenue = event.eventvenue.values[0]        
        if (prevCountry is None) or (prevCountry != eventCountry) :
            showEvents.append(f'\nIn {eventCountry}\n')
        prevCountry = event.eventcountry.values[0]
        showEvents.append(f'*{eventTime}* in {eventCity}, {eventVenue}\n')
    showEvents = [alChar(string) for string in showEvents]
    logger.info('events inserted in showEvents')
 
    sentEvents = context.user_data['sentEvents']
    logger.info('got sentEvents')
    artist = artistsDf['eventartist'].iat[0]
    logger.info('got artist')
    new = ' *\(new\)*' if sentEvents['eventartist'].isin([artist]).any().sum() > 0 else '' 
    logger.info('got new')
    newSentEvents = eventsDf.copy()
    newSentEvents.eventnumber = ''
    context.user_data['sentEvents'] = newSentEvents
    
    lastfmEventUrl = 'https://www.last.fm/music/' + urllib.parse.quote(artist,safe='') + '/+events'

    showEvents.insert(0,f'[_{alChar(artist)}_]({alChar(lastfmEventUrl)}) events{new}\n\n')
    showEvents = ''.join(showEvents)
    logger.info('text ready')
    
    update.message.reply_text(text=showEvents, parse_mode='MarkdownV2', disable_web_page_preview=True)
    logger.info('showNews sent to ')  

def getinfo(update, context) :
    getinfostring = str(context.user_data)
    update.message.reply_text('I know: \n'+getinfostring)
          
def main():
    persistence = PicklePersistence(filename='connectBot')
    updater = Updater("1956526158:AAHeeFZFzkmQeMIVcS1kCXzCm0zfKmeK53Q", persistence=persistence)
    dispatcher = updater.dispatcher
        
    startHandler = CommandHandler('start', start)
#    echoHandler = MessageHandler(Filters.text & (~Filters.command), echo)
    capsHandler = CommandHandler('caps', caps)
    getEventsHandler = CommandHandler('getevents', getEvents)
    showNewsHandler = MessageHandler(Filters.regex('/([0-9]{2,3})$'), showNews)
    getinfoHandler = CommandHandler('getinfo', getinfo)
    
    dispatcher.add_handler(startHandler)   
#    dispatcher.add_handler(echoHandler) 
    dispatcher.add_handler(capsHandler)
    dispatcher.add_handler(getEventsHandler)
    dispatcher.add_handler(showNewsHandler)    
    dispatcher.add_handler(getinfoHandler)

    # Add conversation handler 
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('connect', connectLastm)],
        states={
            USERNAME: [MessageHandler(Filters.text, username)],
            TRACKCOUNTS: [MessageHandler(Filters.text, trackcounts)],
            RUNSEARCH: [MessageHandler(Filters.text('Yes'), runsearch),
                        MessageHandler(Filters.text('No'), skiprunsearch)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        allow_reentry=True,
        name="ggb_picklefile",
        persistent=True,
    )

    dispatcher.add_handler(conv_handler)

    # log all errors
    dispatcher.add_error_handler(error)
    # Start the Bot
    updater.start_polling()

    updater.idle()

if __name__ == '__main__':
    main()

