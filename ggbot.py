import os
import logging
from pathlib import Path
import asyncio
import urllib.parse
from datetime import date, datetime, time
from typing import Dict
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    CallbackContext,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    filters,
    MessageHandler,
)

import lastfm
from lastfm import alChar, addAcc
from db import Db
from db import ArtScrobble, Event, User, UserSettings
from config import Cfg


logger = logging.getLogger('A.C')
logger.setLevel(logging.DEBUG)

db = Db(hard_rewrite=True)
CFG = Cfg()


def loadInteractions(application):
    """
    Loads all command handlers on start.
    Args:
        application: application for adding handlers to
    """
    startHandler = CommandHandler('start', start)
    nolastfmHandler = CommandHandler('nolastfm', nolastfm)
    getEventsHandler = CommandHandler('getevents', getEvents)
    showNewsHandler = MessageHandler(filters.Regex('/([0-9]{2,3})$'), showNews)
    getinfoHandler = CommandHandler('getinfo', getinfo)

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('connect', connect)],
        states={
            USERNAME: [MessageHandler(filters.TEXT, username)],
            RUNSEARCH: [MessageHandler(filters.TEXT, runsearch)],
                },
        fallbacks=[CommandHandler('cancel', cancel)],
        allow_reentry=True,
        name="ggb_picklefile",
        persistent=True,
                                    )

    discon_handler = ConversationHandler(
        entry_points=[CommandHandler('disconnect', disconnect)],
        states={
            DISC_ACC: [MessageHandler(filters.TEXT, disc_acc)]},
        fallbacks=[CommandHandler('cancel', cancel)],
        allow_reentry=True,
        name="ggb_picklefile",
        persistent=False,
                                    )

    application.add_handler(startHandler)
    application.add_handler(discon_handler)
    application.add_handler(nolastfmHandler)
    application.add_handler(getEventsHandler)
    application.add_handler(showNewsHandler)
    application.add_handler(getinfoHandler)
    application.add_handler(conv_handler)
    application.add_error_handler(error)

async def save_user(update) -> None:
    ggbUser = User(
            user_id = update.message.from_user.id,
            username = update.message.from_user.username,
            first_name = update.message.from_user.first_name,
            last_name = update.message.from_user.last_name,
            language_code = update.message.from_user.language_code,
                )
    await db.wsql_users(ggbUser)
    return None

async def start(update, context):
    await save_user(update)
    userId = update.message.from_user.id
    username = update.message.from_user.first_name
    lfmAccs = await db.rsql_lfmuser(userId)
    if not lfmAccs:
        startText = alChar(f"""
        Hello, {username}.\n\n\
\U00002753 To use the bot, make sure you have lastfm account and press /connect\n\n\
\U00002757 If you have no one, press /nolastfm for useful info\n\n\
\U00002764 Detailed info at /help
        """)
    else:
        lfmAccs = ['_' + acc + '_' for acc in lfmAccs]
        startText = alChar(f"""
        {username},\n
you have {len(lfmAccs)} accounts saved: {', '.join(lfmAccs)}.\n\
To add and delete accounts, use /connect and /disconnect.
        """)
    await context.bot.send_message(
        chat_id=userId,
        text=startText,
        parse_mode='MarkdownV2')

async def nolastfm(update, context):
    await save_user(update)
    await context.bot.send_message(
        chat_id=update.message.from_user.id,
        text=alChar(f"""
If you don't have *lastfm account*, just [register](https://www.last.fm/join/) one.\n\
It is free and great service since 2002.\n\
\U00002b07\n\
Add your *music service* like iTunes, Spotify, Yandex.Music, etc. to your new account \
in [settings](https://www.last.fm/settings/applications) of lastfm website.\n\
\U00002b07\n\
Press /connect. Enter account name and forget about the bot.\n\
\U00002705\n\
Bot will send you notification, when it find new concerts.\n
Notes:
• Bot work only with *public accounts* at this moment.\n\
• You can add accounts of your frinds or family members — and, may be, go to event together?
        """),
        parse_mode='MarkdownV2')

async def error(update, context):
    logger.warning('Update "%s" caused error "%s"', update, context.error)

USERNAME, RUNSEARCH = range(2)
DISC_ACC = 0

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
    await save_user(update)
    await update.message.reply_text('Enter lastfm\'s profile name:')
    return USERNAME

async def username(update, context):
    """Waits for lastfmUser"""
    userId = update.message.from_user.id
    lastfmUser = update.message.text.lower()
    text = await addAcc(userId, lastfmUser, db)
    await update.message.reply_text(
        text=alChar(text),
        parse_mode='MarkdownV2'
    )
    if await db.rsql_lfmuser(userId):
        return RUNSEARCH
    else:
        return ConversationHandler.END

async def runsearch(update, context):
    userId = update.message.from_user.id
    chat_id = update.message.chat_id
    remove_job_if_exists(userId, context)
    logger.info(f'Job removed if any.')
    context.job_queue.run_daily(
                                callback=getEventsJob,
                                time=time.fromisoformat(CFG.DEFAULT_NOTICE_TIME),
                                chat_id=chat_id,
                                user_id=userId,
                                job_kwargs={'misfire_grace_time':3600*12,
                                            'coalesce':True}
                                )
    return ConversationHandler.END


async def disconnect(update, context):
    """
    Offer saved accounts to disconnect 
    """
    userId = update.message.from_user.id
    lfmAccs = await db.rsql_lfmuser(userId)
    if lfmAccs:
        lfmAccs.append('Close')
        reply_keyboard = [lfmAccs]
        await update.message.reply_text(
            text='Choose lastfm\'s profile name to disconnect:',
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard,
                one_time_keyboard=True
            ))
        return DISC_ACC
    else:
        await update.message.reply_text('No lastm account saved \U0001F937')
        return ConversationHandler.END


async def disc_acc(update, context):
    """
    Waits for answer which account to delete
    """
    userId = update.message.from_user.id
    accToDisc = update.message.text
    if (accToDisc == '/cancel') or (accToDisc == 'Close'):
        mustDelete = await update.message.reply_text("Ok",reply_markup=ReplyKeyboardRemove())
        context.bot.deleteMessage(message_id = mustDelete.message_id,
                                chat_id = update.message.chat_id)
        return ConversationHandler.END
    rows_affected = await db.dsql_useraccs(userId, accToDisc)
    if rows_affected:
        text = f'Ok! Account _{accToDisc}_ deleted'
    else:
        text = f"Bot had waited for account name to disconnect, but _{accToDisc}_ \
not found. Try /disconnect again"
    await update.message.reply_text(
        text=alChar(text),
        reply_markup=ReplyKeyboardRemove(),
        parse_mode='MarkdownV2')
    return ConversationHandler.END

async def cancel(update, context):
    """Cancels and ends the conversation."""
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    await update.message.reply_text('Bye! I hope we can talk again some day.',
        reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END

async def getEvents(update, context):
    userId = update.message.from_user.id
    infoText = await lastfm.getInfoText(userId, db)
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
    infoText = await lastfm.getInfoText(userId, db)

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
    try:
        shorthand = int(command[1:])
        newsText = await lastfm.getNewsText(userId, shorthand, db)
        await update.message.reply_text(text=newsText, parse_mode='MarkdownV2', disable_web_page_preview=True)
        logger.info('newsText sent to ')
    except:
        await update.message.reply_text("Can't understand command")


async def getinfo(update, context):
    getinfostring = str(context.user_data)
    await update.message.reply_text('I know: \n' + getinfostring)

