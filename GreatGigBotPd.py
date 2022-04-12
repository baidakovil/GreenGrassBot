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

# START CONVERSATION
USERNAME, MINLISTENS, PLACES, RUNSEARCH = range(4)

def removeJob(name: str, context: CallbackContext) -> bool:
    """Remove job with given name. Returns whether job was removed."""
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True


def connectLastm(update: Update, context: CallbackContext):
    """Starts the conversation and asks the user about lastfmUser."""
    user = update.message.from_user
    userId = str(user.id)
    context.user_data['userId'] = userId
    ggbl.writeSett(userId, 'userId', userId)
    logger.info(f'User {user.first_name} {user.last_name} id: {userId}')
    update.message.reply_text('Enter lastfm\'s profile name:')
    return USERNAME

def username(update: Update, context: CallbackContext):
    """Waits for lastfmUser"""
    reply_keyboard = [['Listened at least twice a day'],['All listened artists']]
    user = update.message.from_user
    userId = str(user.id)
    lastfmUser = update.message.text.lower()
    ggbl.writeSett(userId, 'lastfmUser', lastfmUser)
    logger.info(f'User {user.first_name} {user.last_name} username: {lastfmUser}')
    update.message.reply_text('Which artist are you interested?',
                              reply_markup=ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=True))
    return MINLISTENS


def minlistens(update: Update, context: CallbackContext):
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
    update.message.reply_text('Now, run the search?',
                              reply_markup=ReplyKeyboardMarkup(
                                  reply_keyboard, one_time_keyboard=True, input_field_placeholder='Yes or No?'))
    # reply_keyboard = [['Yes'], ['No, search worldwide']]
    # update.message.reply_text("""Would you like to specify countries or cities for event
    # searching? Only this locations will shown""", reply_markup=ReplyKeyboardMarkup(reply_keyboard,
    #                                                 resize_keyboard=True, one_time_keyboard=True))
    return RUNSEARCH

# def places(update: Update, context: CallbackContext):
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

# def countries(update: Update, context: CallbackContext):
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

def runsearch(update: Update, context: CallbackContext):
    user = update.message.from_user
    userId = str(user.id)
    chat_id = update.message.chat_id
    timeToGetEvents = 3
    removeJob(userId, context)
    logger.info('Job removed if any')
    context.job_queue.run_once(getEventsJob, timeToGetEvents,
                               context=context, name=str(userId))
    logger.info('Timer set to %s sec', timeToGetEvents)
    logger.info('User %s will run search: %s', user.first_name, update.message.text)
    # userId = str(context.user_data['userId'])
    # infoText = ggbl.getInfoText(userId)
    # update.message.reply_text(infoText, reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END


def skiprunsearch(update: Update, context: CallbackContext):
    user = update.message.from_user
    logger.info('User %s skips search', user.first_name)
    update.message.reply_text('Bye', reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


def cancel(update: Update, context: CallbackContext):
    """Cancels and ends the conversation."""
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    update.message.reply_text('Bye! I hope we can talk again some day.',
        reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END


def getEvents(update: Update, context: CallbackContext):
    userId = str(update.message.from_user.id)
    infoText = ggbl.getInfoText(userId)
    update.message.reply_text(infoText, reply_markup=ReplyKeyboardRemove(),parse_mode='MarkdownV2')
    logger.info('infoText was sent')

def getEventsJob(context: CallbackContext):
    """
    1) отправляет в чат список исполнителей с новыми концертами
    2) посредством ggbl.infoText() чистит и обновляет список всех когда-либо полученных концертов (sentEvents)
    3) посредством ggbl.infoText() обновляет список концертов, доступных по команде "/хх" (lastEvents)
    """
    logger.info('Start getEventsJob')
    job = context.job
    userId = str(job.context.user_data['userId'])
    infoText = ggbl.getInfoText(userId)
    context.bot.send_message(userId, text=infoText, parse_mode='MarkdownV2')
    logger.info('Job done')


def showNews(update, context):
    """
    Отправляет в чат список концертов исполнителя, выбранного командой '/xx'
    """
    userId = str(update.message.from_user.id)
    command = update.message.text
    newsText = ggbl.getNewsText(userId, command)
    update.message.reply_text(text=newsText, parse_mode='MarkdownV2', disable_web_page_preview=True)
    logger.info('newsText sent to ')


def getinfo(update, context):
    getinfostring = str(context.user_data)
    update.message.reply_text('I know: \n' + getinfostring)


def main():
    persistence = PicklePersistence(filename='connectBot')
    updater = Updater("...", persistence=persistence)
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


if __name__ == '__main__':
    main()
