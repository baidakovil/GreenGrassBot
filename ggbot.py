import logging
import os
from pathlib import Path
import urllib.parse
from datetime import date, datetime, time
from typing import Dict
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
import gglib
import pandas as pd
from telegram.ext import (
    CallbackContext,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    filters,
    MessageHandler,
)

logger = logging.getLogger('A.C')
logger.setLevel(logging.DEBUG)


async def start(update, context):

    # TODO  if account_quantity:
            #     send_message...
            # else:
            #     send message ...

    userId = context.user_data[id]
    context.bot.send_message(chat_id=userId,
                             text='<a href="https://www.last.fm/user/trygreatgigbot">Link</a>',
                             parse_mode='HTML')

async def error(update, context):
    logger.warning('Update "%s" caused error "%s"', update, context.error)

async def caps(update, context):
    text_caps = ' '.join(context.args).upper()
    context.bot.send_message(chat_id=update.effective_chat.id, text=text_caps)

USERNAME, MINLISTENS, RUNSEARCH = range(3)

def remove_job_if_exists(name: str, context) -> bool:
    """Remove job with given name. Returns whether job was removed."""
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True


async def connect(update, context):
    """
    Starts the conversation and asks the lastfm username.
    """

    # if len(account_quantity) == 0:
    #     add user_id to db 
    # elif len(account_quantity) == len(max_acc_quantity):
    #     send_message(sorry)
    #     return end
    # send_message(enter account)
    # return USERNAME

    user = update.message.from_user
    userId = str(user.id)
    context.user_data['userId'] = userId
    gglib.writeSett(userId, 'userId', userId)
    logger.info(f'User {user.first_name} {user.last_name} id: {userId}')
    await update.message.reply_text('Enter lastfm\'s profile name:')
    return USERNAME

async def username(update, context):
    """Waits for lastfmUser"""

    # if account valid:
    #     save to db
    #     send_message(account saved, settings used...)
    #     return end
    # send_message(account not valid)
    # return MINLISTENS

    reply_keyboard = [['Listened at least twice a day'],['All listened artists']]
    user = update.message.from_user
    userId = str(user.id)
    lastfmUser = update.message.text.lower()
    gglib.writeSett(userId, 'lastfmUser', lastfmUser)
    logger.info(f'User {user.first_name} {user.last_name} username: {lastfmUser}')
    await update.message.reply_text(
        'Would you like to get announced about each listened artist, or only about listened at least twice for a day?',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=True)
        )
    return MINLISTENS


async def minlistens(update, context):
    """Waits for answer which artists are in interest"""
    user = update.message.from_user
    userId = str(user.id)
    minlistensAnswer = update.message.text
    if minlistensAnswer == 'Listened at least twice a day':
        minListens = 2
    elif minlistensAnswer == 'All listened artists':
        minListens = 1
    gglib.writeSett(userId, 'minListens', minListens)
    reply_keyboard = [['Yes', 'No']]
    await update.message.reply_text(
                                gglib.alChar('Ok! Press *Yes* if you want to run daily news about new concerts'),
                                reply_markup=ReplyKeyboardMarkup(
                                                reply_keyboard,
                                                one_time_keyboard=True,
                                                input_field_placeholder='Yes or No?'),
                                parse_mode='MarkdownV2')

    return RUNSEARCH


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
    context.job_queue.run_daily(
                                callback=getEventsJob,
                                time=time.fromisoformat('17:45:00'),
                                chat_id=chat_id,
                                user_id=userId,
                                job_kwargs={'misfire_grace_time':3600*12,
                                            'coalesce':True}
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
    infoText = gglib.getInfoText(userId)
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
    infoText = gglib.getInfoText(userId)

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
    newsText = gglib.getNewsText(userId, command)
    await update.message.reply_text(text=newsText, parse_mode='MarkdownV2', disable_web_page_preview=True)
    logger.info('newsText sent to ')


async def getinfo(update, context):
    getinfostring = str(context.user_data)
    await update.message.reply_text('I know: \n' + getinfostring)

def loadInteractions(application):
    """
    Loads all command handlers on start.
    Args:
        application: application for adding handlers to
    """
    startHandler = CommandHandler('start', start)
    capsHandler = CommandHandler('caps', caps)
    getEventsHandler = CommandHandler('getevents', getEvents)
    showNewsHandler = MessageHandler(filters.Regex('/([0-9]{2,3})$'), showNews)
    getinfoHandler = CommandHandler('getinfo', getinfo)

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('connect', connect)],
        states={
            USERNAME: [MessageHandler(filters.TEXT, username)],
            MINLISTENS: [MessageHandler(filters.Text('Listened at least twice a day') | filters.Text('All listened artists'), minlistens)],
            RUNSEARCH: [MessageHandler(filters.Text('Yes (I know it takes time)'), runsearch),
                        MessageHandler(filters.Text('No'), skiprunsearch)],
                },
        fallbacks=[CommandHandler('cancel', cancel)],
        allow_reentry=True,
        name="ggb_picklefile",
        persistent=True,
                                    )

    application.add_handler(startHandler)
    application.add_handler(capsHandler)
    application.add_handler(getEventsHandler)
    application.add_handler(showNewsHandler)
    application.add_handler(getinfoHandler)
    application.add_handler(conv_handler)
    application.add_error_handler(error)