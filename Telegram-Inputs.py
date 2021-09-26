# -*- coding: utf-8 -*-
import logging
from urllib.request import urlopen
from datetime import datetime, timedelta
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

def start(update, context):
    update.message.reply_text('Hey this is my bot! Lastfm run 6')
  
def echo(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.text)

def error(update, context):
    logger.warning('Update "%s" caused error "%s"', update, context.error)

def presetting(update, context) :
    context.bot.send_message(chat_id=update.effective_chat.id, text='Enter lastfm\'s profile name')
    lastfmUserName = update.message.text
    
def caps(update, context):
    text_caps = ' '.join(context.args).upper()
    context.bot.send_message(chat_id=update.effective_chat.id, text=text_caps)      
       
def main():
    updater = Updater("1956526158:AAHeeFZFzkmQeMIVcS1kCXzCm0zfKmeK53Q", use_context=True)
    dispatcher = updater.dispatcher
    
    startHandler = CommandHandler('start', start)
    presettingHandler = CommandHandler('presetting', start)
    echoHandler = MessageHandler(Filters.text & (~Filters.command), echo)
    capsHandler = CommandHandler('caps', caps)
    
    dispatcher.add_handler(startHandler)   
    dispatcher.add_handler(presettingHandler)
    dispatcher.add_handler(echoHandler) 
    dispatcher.add_handler(capsHandler)

    # log all errors
    dispatcher.add_error_handler(error)
    # Start the Bot
    updater.start_polling()

    updater.idle()

if __name__ == '__main__':
    main()
