import json

from telegram.ext import Updater
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler, Filters
from telegram import InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import InlineQueryHandler

import logging
import requests
from requests.utils import requote_uri

SECRETS = dict()
with open('secrets.txt', 'r') as f:
    SECRETS = json.loads(f.read())

updater = Updater(token=SECRETS['token'], use_context=True)
dispatcher = updater.dispatcher

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)


def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Hello There 👋")
    help_message(update, context)


start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)
updater.start_polling()


def help_message(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text='Search for lyrics with {Artists} - {Title} syntax.')


help_message_handler = CommandHandler('help', help_message)
dispatcher.add_handler(help_message_handler)


def lyrics(update, context):
    _input = update.effective_message.text

    if not _input:
        return

    artists, title = map(str.strip, _input.split('-')[:2])
    url = requote_uri(f'https://api.lyrics.ovh/v1/{artists}/{title}/')
    response = requests.get(url=url).text
    response = json.loads(response)

    if 'lyrics' in response:
        output = f'{response["lyrics"]}'

        context.bot.send_message(chat_id=update.effective_chat.id, text=output)

    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text='Lyrics not found. Double check the spelling.')


lyrics_handler = MessageHandler(Filters.text & (~Filters.command), lyrics)
dispatcher.add_handler(lyrics_handler)


def inline_lyrics(update, context):
    _input = update.inline_query.query

    if not _input:
        return

    artists, title = map(str.strip, _input.split('-')[:2])
    url = requote_uri(f'https://api.lyrics.ovh/v1/{artists}/{title}/')
    response = requests.get(url=url).text
    response = json.loads(response)

    if 'lyrics' in response:
        output = f'{artists} - {title}\n\n' \
                 f'{response["lyrics"]}'

    else:
        output = f'{artists}, {title}:\n\nLyrics not found. Double check the spelling.'

    results = [InlineQueryResultArticle(
        id=_input,
        title='lyrics',
        input_message_content=InputTextMessageContent(output)
    )]

    context.bot.answer_inline_query(update.inline_query.id, results)


inline_lyrics_handler = InlineQueryHandler(inline_lyrics)
dispatcher.add_handler(inline_lyrics_handler)


def unknown(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I didn't understand that command.")


unknown_handler = MessageHandler(Filters.command, unknown)
dispatcher.add_handler(unknown_handler)
