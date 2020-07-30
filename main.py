import json

from telegram.ext import Updater
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler, Filters
from telegram import InlineQueryResultArticle, InputTextMessageContent, ParseMode
from telegram.ext import InlineQueryHandler

from markdown_strings import link

import logging
import requests
from requests.utils import requote_uri

COMMAND = 1
INLINE = 2
BOT_USERNAME = '@NudleLyricsBot'

SECRETS = dict()
with open('secrets.txt', 'r') as f:
    SECRETS = json.loads(f.read())

updater = Updater(token=SECRETS['token'], use_context=True)
dispatcher = updater.dispatcher

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)


def request_for_lyrics(artists, title, mode: [INLINE, COMMAND], preview=None):
    if mode == COMMAND:
        url = requote_uri(f'https://api.lyrics.ovh/v1/{artists}/{title}/')
        response = requests.get(url=url).text
        response = json.loads(response)

        if 'lyrics' in response:
            output = f'{artists} - {title}:\n\n' \
                     f'{response["lyrics"]}'

            return output

        return 'Lyrics not found. Double check the spelling. ' \
               'If you used inline suggestions, lyrics are not available :('

    else:
        if preview:
            output = f'{BOT_USERNAME} {artists} - {title}\n\n' \
                     f'{link("preview", preview)}'

        else:
            output = f'{BOT_USERNAME} {artists} - {title}'

        return output


def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Hello There 👋")
    help_message(update, context)


start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)
updater.start_polling()


def help_message(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text=f'Search for lyrics with <Artists> - <Title> syntax'
                                  f' or use {BOT_USERNAME} to search easier and get song\'s preview')


help_message_handler = CommandHandler('help', help_message)
dispatcher.add_handler(help_message_handler)


def lyrics(update, context):
    _input = ''
    artists = ''
    title = ''

    _input = update.effective_message.text

    if not _input:
        return

    if _input.startswith(BOT_USERNAME):
        _input = _input.split('\n\n')[0].replace(BOT_USERNAME, '')

    try:

        artists, title = map(str.strip, _input.split('-')[:2])

    except Exception as e:
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text='Lyrics not found. Double check the spelling.')
        return

    context.bot.send_message(chat_id=update.effective_chat.id,
                             text=request_for_lyrics(artists=artists, title=title, mode=COMMAND),
                             parse_mode=ParseMode.MARKDOWN)


lyrics_handler = MessageHandler(Filters.text & (~Filters.command), lyrics)
dispatcher.add_handler(lyrics_handler)


def inline_message(update, context):
    _input = update.inline_query.query

    if not _input:
        return

    url = requote_uri(f'https://api.lyrics.ovh/suggest/{_input}/')
    response = requests.get(url=url).text
    response = json.loads(response)

    if 'data' in response:
        results = []
        for data in response['data'][:5]:
            title = data['title']
            artists = data['artist']['name']
            picture = data['artist']['picture_small']

            results.append(
                InlineQueryResultArticle(
                    id=f'{data["id"][:3]}-{artists}-{title}',
                    title=f'{artists} - {title}',
                    thumb_url=picture,
                    input_message_content=InputTextMessageContent(
                        request_for_lyrics(artists=artists, title=title, mode=INLINE,
                                           preview=data.pop('preview', None)
                                           )
                    )
                )
            )

        context.bot.answer_inline_query(update.inline_query.id, results, timeout=10000000)


inline_message_handler = InlineQueryHandler(inline_message)
dispatcher.add_handler(inline_message_handler)


def unknown(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I didn't understand that command.")


unknown_handler = MessageHandler(Filters.command, unknown)
dispatcher.add_handler(unknown_handler)

updater.idle()
updater.stop()
