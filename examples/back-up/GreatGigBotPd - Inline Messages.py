#!/usr/bin/env python
# coding: utf-8
# -*- coding: utf-8 -*-
import logging
import urllib.parse
from datetime import date, datetime
from typing import Dict
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update, InlineKeyboardButton, InlineKeyboardMarkup
import GreatGigBotLibPd as ggbl
from pathlib import Path
import pandas as pd
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackQueryHandler,
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
USERNAME, MINLISTENS, RUNSEARCH = range(3)

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
    update.message.reply_text('Enter lastfm\'s profile name')
    return USERNAME

def username(update: Update, context: CallbackContext):
    """Waits for lastfmUser"""
    reply_keyboard = [[InlineKeyboardButton('Listened at least twice a day', callback_data='2')],
                      [InlineKeyboardButton('All listened artists', callback_data='1')]]
    user = update.message.from_user
    userId = str(user.id)
    lastfmUser = update.message.text.lower()
    ggbl.writeSett(userId, 'lastfmUser', lastfmUser)
    logger.info(f'User {user.first_name} {user.last_name} username: {lastfmUser}')
    update.message.reply_text('Haha, which artist are you interested?',
                              reply_markup=InlineKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=True))
    return MINLISTENS


def minlistens(update: Update, context: CallbackContext):
    """Waits for days to load"""
    reply_keyboard = [['Yes', 'No']]


    query = update.callback_query
    user = update.callback_query.from_user
    query.answer()
    minListens = query.data
    newText = 'All listened artists' if minListens == 1 else 'Artists, listened at least twice a day'
    query.edit_message_text(text=f'— Which artist are you interested?\n — _{newText}_', parse_mode='MarkdownV2')

    userId = str(user.id)

    ggbl.writeSett(userId, 'minListens', query.data)
    logger.info(f'User {user.first_name} {user.last_name} minListens: {minListens}')

    timeToGetEvents = 3
    job_removed = removeJob(userId, context)
    logger.info('Job removed if any')
    context.job_queue.run_once(getEventsJob, timeToGetEvents,
                               context=context, name=str(userId))
    logger.info('Timer set to %s sec', timeToGetEvents)
    query.message.reply_text('Huhu, now, run the search?',
                              reply_markup=ReplyKeyboardMarkup(
                                  reply_keyboard, one_time_keyboard=True, input_field_placeholder='Yes or No?'))
    return RUNSEARCH


def runsearch(update: Update, context: CallbackContext):
    user = update.message.from_user
    chat_id = update.message.chat_id
    logger.info('User %s will run search: %s', user.first_name, update.message.text)
    userId = str(context.user_data['userId'])
    infoText = ggbl.getInfoText(userId)
    update.message.reply_text(infoText, reply_markup=ReplyKeyboardRemove())

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
            MINLISTENS: [CallbackQueryHandler(minlistens)],
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
