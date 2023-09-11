#!/usr/bin/env python
# coding: utf-8
# -*- coding: utf-8 -*-
import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import urllib.parse
from datetime import date, datetime
from typing import Dict
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.helpers import escape_markdown
import GreatGigBotLibPd as ggbl
from pathlib import Path
import pandas as pd
from telegram.ext import (
    Application,
    CallbackContext,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    filters,
    MessageHandler,
    PicklePersistence,
)


BOTFOLDER = '/home/eva/git/GreatGigBot/'
Path('connectBot').unlink(missing_ok=True)

def startLogger():
    logger = logging.getLogger('A')
    logger.setLevel(logging.DEBUG)
    class ContextFilter(logging.Filter):
        def filter(self, record):
            if (record.name=='A') and (record.levelname=='DEBUG'):
                return 0
            else:
                return 1
    ch = logging.StreamHandler()
    fh = logging.FileHandler(
        filename='/home/eva/git/GreatGigBot/logger.log',
        mode='w')
    rh = RotatingFileHandler(
        filename='/home/eva/git/GreatGigBot/data/log/logger_rotating.log',
        mode='a',
        maxBytes=1024*1024*20,
        backupCount=5)
    ch_formatter = logging.Formatter(
        '[%(asctime)s.%(msecs)03d - %(name)3s - %(levelname)8s - %(funcName)18s()] %(message)s',
        '%H:%M:%S')
    fh_formatter = logging.Formatter(
        '[%(asctime)s.%(msecs)03d - %(name)20s - %(filename)20s:%(lineno)4s - %(funcName)20s() - %(levelname)8s - %(threadName)10s] %(message)s',
        '%Y-%m-%d %H:%M:%S')
    ch.setLevel(logging.DEBUG)
    fh.setLevel(logging.DEBUG)
    rh.setLevel(logging.DEBUG)
    ch.setFormatter(ch_formatter)
    fh.setFormatter(fh_formatter)
    rh.setFormatter(fh_formatter)
    logger.addHandler(ch)
    logger.addHandler(fh)
    logger.addHandler(rh)
    ch_filter = ContextFilter()
    ch.addFilter(ch_filter)
    return logger

logger = startLogger()

logger.info(f'App started, __name__ is {__name__}')

async def start(update, context):
    userId = context.user_data[id]
    context.bot.send_message(chat_id=userId,
                             text='<a href="https://www.last.fm/user/trygreatgigbot">Link</a>',
                             parse_mode='HTML')

async def echo(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.text)


async def error(update, context):
    logger.warning('Update "%s" caused error "%s"', update, context.error)

async def caps(update, context):
    text_caps = ' '.join(context.args).upper()
    context.bot.send_message(chat_id=update.effective_chat.id, text=text_caps)

# START CONVERSATION
USERNAME, MINLISTENS, RUNSEARCH = range(3)

def remove_job_if_exists(name: str, context) -> bool:
    """Remove job with given name. Returns whether job was removed."""
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True


async def connectLastm(update, context):
    """Starts the conversation and asks the user about lastfmUser."""
    user = update.message.from_user
    userId = str(user.id)
    context.user_data['userId'] = userId
    ggbl.writeSett(userId, 'userId', userId)
    logger.info(f'User {user.first_name} {user.last_name} id: {userId}')
    await update.message.reply_text('Enter lastfm\'s profile name:')
    return USERNAME

async def username(update, context):
    """Waits for lastfmUser"""
    reply_keyboard = [['Listened at least twice a day'],['All listened artists']]
    user = update.message.from_user
    userId = str(user.id)
    lastfmUser = update.message.text.lower()
    ggbl.writeSett(userId, 'lastfmUser', lastfmUser)
    logger.info(f'User {user.first_name} {user.last_name} username: {lastfmUser}')
    await update.message.reply_text('Which artist are you interested?',
                              reply_markup=ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=True))
    return MINLISTENS


async def minlistens(update, context):
    """Waits for answer which artists are in interest"""
    user = update.message.from_user
    # logger.info(f'User {user.first_name} {user.last_name} minListens: {minListens}')
    userId = str(user.id)
    minlistensAnswer = update.message.text
    if minlistensAnswer == 'Listened at least twice a day':
        minListens = 2
    elif minlistensAnswer == 'All listened artists':
        minListens = 1
    ggbl.writeSett(userId, 'minListens', minListens)
    reply_keyboard = [['Yes (I know it takes time)', 'No']]
    await update.message.reply_text('Now, run the search?',
                              reply_markup=ReplyKeyboardMarkup(
                                  reply_keyboard, one_time_keyboard=True, input_field_placeholder='Yes or No?'))
    # reply_keyboard = [['Yes'], ['No, search worldwide']]
    # update.message.reply_text("""Would you like to specify countries or cities for event
    # searching? Only this locations will shown""", reply_markup=ReplyKeyboardMarkup(reply_keyboard,
    #                                                 resize_keyboard=True, one_time_keyboard=True))
    return RUNSEARCH

# def places(update, context: CallbackContext):
#     """Waits for answer whether specify countries"""
#     user = update.message.from_user
#     placesAnswer = update.message.text
#     logger.info(f'User {user.first_name} {user.last_name} placesAnswer: {placesAnswer}')
#     if placesAnswer == 'Yes':
#         logger.info(f'User {user.first_name} {user.last_name} choose to specify country')
#         answer = 'Please type country you want:'
#         update.message.reply_text(text=answer, reply_markup=ReplyKeyboardRemove())
#         return COUNTRIES
#     elif (placesAnswer == 'No, search worldwide') or (placesAnswer == 'Done'):
#         answer = 'Ok.\nHow often should bot notice you about new concerts?'
#         update.message.reply_text(text=answer, reply_markup=ReplyKeyboardRemove())
#         return SCHEDULE
#
#     update.message.reply_text(text= reply_markup=ReplyKeyboardRemove())

# def countries(update, context: CallbackContext):
#     """Waits for country specified"""
#     user = update.message.from_user
#     userId = str(user.id)
#     countryAnswer = update.message.text
#     logger.info(f'User {user.first_name} {user.last_name} countryAnswer: {countryAnswer}')
#     if countryAnswer = 'Skip':
#         if 'Russia' in ggbl.readSett(['places'],userId)[0].keys():
#             answer = 'Would you like to specify cities for Russia?'
#             reply_keyboard = [['Yes'], ['No, search for whole Russia']]
#             update.message.reply_text(text=answer, reply_markup=ReplyKeyboardMarkup(reply_keyboard,
#                                                             resize_keyboard=True, one_time_keyboard=True))
#             return CITIES
#         else:
#             return SCHEDULE
#     else:
#         reply_keyboard = [[Skip]]
#         if ggbl.addCountry(countryAnswer, userId):
#             answer = 'Country added to filter.\n If want to add another one, send now. If done, press Skip»'
#         else:
#             answer = "Can\'t find this country. Try use common country name or press «Skip» to go next step"
#         update.message.reply_text(text=answer, reply_markup=ReplyKeyboardMarkup(reply_keyboard,
#                                                         resize_keyboard=True, one_time_keyboard=True))
#         return COUNTRIES

async def runsearch(update, context):
    user = update.message.from_user
    userId = str(user.id)
    chat_id = update.message.chat_id
    timeToGetEvents = 3
    remove_job_if_exists(userId, context)
    logger.info(f'Job removed if any. {timeToGetEvents} sec to run job')
    context.job_queue.run_once(
                                callback=getEventsJob,
                                when=timeToGetEvents,
                                chat_id=chat_id,
                                user_id=userId,
                                data=context,
                                name=str(userId),
                                job_kwargs={'misfire_grace_time':3600}
                                )
    return ConversationHandler.END


async def skiprunsearch(update, context):
    user = update.message.from_user
    logger.info('User %s skips search', user.first_name)
    await update.message.reply_text('Bye', reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END


async def cancel(update, context):
    """Cancels and ends the conversation."""
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    await update.message.reply_text('Bye! I hope we can talk again some day.',
        reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END


async def getEvents(update, context):
    userId = str(update.message.from_user.id)
    infoText = ggbl.getInfoText(userId)
    await update.message.reply_text(infoText, reply_markup=ReplyKeyboardRemove(),parse_mode='MarkdownV2')
    logger.info('infoText was sent')

async def getEventsJob(context):
    """
    Sent list of artists with new concerts to user.
    Refresh sentEvents on disk to escape multiple user notification of similar events.
    Refresh lastEvents on disk (need for using /** command)
    """ 
    logger.info('Start getEventsJob')
    job = context.job

    userId = str(job.user_id)
    infoText = ggbl.getInfoText(userId)

    await context.bot.send_message(
                            chat_id=job.chat_id,
                            text=infoText,
                            parse_mode='MarkdownV2')

    # await update.message.reply_text(infoText, reply_markup=ReplyKeyboardRemove())

    logger.info('Job done')


async def showNews(update, context):
    """
    Отправляет в чат список концертов исполнителя, выбранного командой '/xx'
    """
    userId = str(update.message.from_user.id)
    command = update.message.text
    newsText = ggbl.getNewsText(userId, command)
    await update.message.reply_text(text=newsText, parse_mode='MarkdownV2', disable_web_page_preview=True)
    logger.info('newsText sent to ')


async def getinfo(update, context):
    getinfostring = str(context.user_data)
    await update.message.reply_text('I know: \n' + getinfostring)


def main():

    with open(os.path.join(BOTFOLDER, 'token')) as file:
        token = file.read()

    persistence = PicklePersistence(filepath='connectBot')
    application = Application.builder().token(token).persistence(persistence).build()

    startHandler = CommandHandler('start', start)
    # echoHandler = MessageHandler(filters.TEXT & ~filters.COMMAND, echo)
    capsHandler = CommandHandler('caps', caps)
    getEventsHandler = CommandHandler('getevents', getEvents)
    showNewsHandler = MessageHandler(filters.Regex('/([0-9]{2,3})$'), showNews)
    getinfoHandler = CommandHandler('getinfo', getinfo)

    application.add_handler(startHandler)
    # application.add_handler(echoHandler)
    application.add_handler(capsHandler)
    application.add_handler(getEventsHandler)
    application.add_handler(showNewsHandler)
    application.add_handler(getinfoHandler)

    # Add conversation handler 
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('connect', connectLastm)],
        states={
            USERNAME: [MessageHandler(filters.TEXT, username)],
            MINLISTENS: [MessageHandler(filters.Text('Listened at least twice a day') | filters.Text('All listened artists'), minlistens)],
            # PLACES: [MessageHandler(filters.TEXT('Yes'), places),
            #             MessageHandler(filters.TEXT('No, search worldwide'), places)],
            RUNSEARCH: [MessageHandler(filters.Text('Yes (I know it takes time)'), runsearch),
                        MessageHandler(filters.Text('No'), skiprunsearch)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        allow_reentry=True,
        name="ggb_picklefile",
        persistent=True,
    )
    application.add_handler(conv_handler)

    # log all errors
    application.add_error_handler(error)
    # Start the Bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

""" def main():
    persistence_path='./connectBot'
    # updater = Updater("...", persistence=persistence)
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
            MINLISTENS: [MessageHandler(Filters.text('Listened at least twice a day') | Filters.text('All listened artists'), minlistens)],
            # PLACES: [MessageHandler(Filters.text('Yes'), places),
            #             MessageHandler(Filters.text('No, search worldwide'), places)],
            RUNSEARCH: [MessageHandler(Filters.text('Yes (I know it takes time)'), runsearch),
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
    """


if __name__ == '__main__':
    main()
