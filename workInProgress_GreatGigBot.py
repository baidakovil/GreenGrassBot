# -*- coding: utf-8 -*-
import logging
from urllib.request import urlopen
from datetime import datetime, timedelta
from typing import Dict
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
import GreatGigBotLib as ggbl
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    PicklePersistence,
    CallbackContext,
)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

def start(update, context):
    update.message.reply_text('Hey this is my bot! Lastfm run 6')
  
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
    """Waits for hours to load"""
    reply_keyboard = [['Yes', 'No']] 
    hoursDelta = update.message.text
    userId = update.message.from_user.id
    lastfmUser = context.user_data['lastfmUser']
    hoursDelta = int(context.user_data['hoursDelta'])
    dataForGetEvents = [ userId, lastfmUser, hoursDelta ]
    context.user_data['hoursDelta'] = hoursDelta
    logger.info('User %s enters hours: %s', userId, hoursDelta)
    
    timeToGetEvents = 15
    logger.info('Prepare to remove job')
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
    """Waits for answer whether to run search"""
    user = update.message.from_user
    chat_id = update.message.chat_id 
    logger.info('User %s will run search: %s', user.first_name, update.message.text)
    
    eventString = ggbl.getLastfmEvents(
        lastfmUser = context.user_data['lastfmUser'],
        hoursDelta = int(context.user_data['hoursDelta']),
        minListens = 3)
    if eventString == '' :
        update.message.reply_text('No concerts (',reply_markup=ReplyKeyboardRemove())
    else :
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
    eventString = ggbl.getLastfmEvents(
        lastfmUser = context.user_data['lastfmUser'],
        hoursDelta = int(context.user_data['hoursDelta']),
        minListens = 3)
    if eventString == '' :
        update.message.reply_text('No concerts (',reply_markup=ReplyKeyboardRemove())
    else :
        update.message.reply_text(eventString,reply_markup=ReplyKeyboardRemove())

def getEventsJob(context: CallbackContext) :

    logger.info('Start getEventsJob')
    job = context.job

    userId = job.context.user_data['userId']
    lastfmUser = job.context.user_data['lastfmUser']
    hoursDelta = int(job.context.user_data['hoursDelta'])
    logger.info('Data is found')
    
    eventString = ggbl.getLastfmEvents(lastfmUser,int(hoursDelta),minListens = 3)
    logger.info('eventString done')
    
    if eventString == '' :
        eventString = 'No concerts ('
    context.bot.send_message(userId, text=eventString)

    logger.info('Job done')

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
    getinfoHandler = CommandHandler('getinfo', getinfo)
    
    dispatcher.add_handler(startHandler)   
#    dispatcher.add_handler(echoHandler) 
    dispatcher.add_handler(capsHandler)
    dispatcher.add_handler(getEventsHandler)
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
