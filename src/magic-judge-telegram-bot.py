import logging
import json

import oracle_sql
import documents
from telegram.ext import (Updater, CommandHandler, InlineQueryHandler, CallbackContext,
                          CallbackQueryHandler, MessageHandler, Filters)
from telegram import (InlineQueryResultArticle, InputTextMessageContent,
                      InlineKeyboardButton, InlineKeyboardMarkup, Update)

from typing import List, Dict, Optional

#logging.basicConfig(
#    level=logging.DEBUG,
#    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')



def preview_card(card):
    mana = ''
    if 'manaCost' in card:
        mana = '\t' + card['manaCost']
    return '{}{}\n{}'.format(
        card['name'],
        mana,
        card['type'])


def start_command(update):
    commands = [
        '/o <card name or search strings> - oracle text for a card',
        '/q <question> - oracle text for cards mentioned in the question',
        '/cr <section> (coming soon)',
        '/ipg <section> (coming soon)',
        '/mtr <section> (coming soon)',
    ]
    update.message.reply_text(
        'How can I help?\n{}'.format(
            '\n'.join(commands)),
        quote=False)


def oracle_impl(update: Update, args: Optional[List[str]]) -> None:
    if not args:
        update.message.reply_text(
            'I need some clues to search for, my master!',
            quote=False)
        return
    words = [word.casefold() for word in args]

    name_candidates = oracle_sql.get_matching_names(words)

    if not name_candidates:
        update.message.reply_text(
            'I searched very thoroughly, but returned empty-handed, my master!',
            quote=False)
        return

    if len(words) == 1 and words[0] in [n.casefold() for n in name_candidates]:
        name_candidates = [words[0].casefold()]

    if len(name_candidates) > 20:
        update.message.reply_text(
            'I need more specific clues, my master! This would return {} names'.format(
                len(name_candidates)), quote=False)
        return

    if len(name_candidates) > 1:
        # TODO: if len(name) < 64 is a quickfix for /o show, which fails to
        # send correct callback data for un... card
        reply_markup = InlineKeyboardMarkup(
            [[InlineKeyboardButton(name, callback_data=name)]
             for name in name_candidates if len(name) < 64])
        update.message.reply_text(
            'Which one?',
            reply_markup=reply_markup,
            quote=False)
        return

    logging.debug("the only candidate: %s", name_candidates)
    card = oracle_sql.get_card(name_candidates[0])
    if not card:
        return

    update.message.reply_text(card.format(), parse_mode='HTML', quote=False)


def oracle_command(update: Update, context: CallbackContext):
    oracle_impl(update, context.args)


def inline_oracle(update: Update, context: CallbackContext) -> None:
    query = update.inline_query.query.casefold()
    if not query:
        return

    if len(query) < 3:
        return

    words = query.split()
    name_candidates = oracle_sql.get_matching_names(words)
    if not name_candidates:
        return

    results = list()
    for word in name_candidates[:3]:
        for oracleName in oracle_sql.get_oracle_names(word):
            card = oracle_sql.get_card(oracleName)
            if not card:
                continue
            results.append(
                InlineQueryResultArticle(
                    id=card.name,
                    title=word,
                    description=preview_card(card),
                    input_message_content=InputTextMessageContent(
                        card.format(),
                        parse_mode='HTML')))
    update.callback_query.message.bot.answerInlineQuery(update.inline_query.id, results)


def callback_name(update: Update, context: CallbackContext) -> None:
    message_id = update.callback_query.message.message_id
    chat_id = update.callback_query.message.chat.id
    name = update.callback_query.data

    names = oracle_sql.get_oracle_names(name)

    if not names:
        update.callback_query.message.bot.answerCallbackQuery(update.callback_query.id)
        return

    update.callback_query.message.bot.editMessageText(chat_id=chat_id, message_id=message_id,
                                                      parse_mode='HTML', text='\n'.join(
            [oracle_sql.get_card(oracleName).format()
             for oracleName in names]))
    update.callback_query.message.bot.answerCallbackQuery(update.callback_query.id)


def text_filter(update: Update, context: CallbackContext) -> None:
    if update.message.chat.type != 'private':
        return
    text = update.message.text
    if len(text) < 30:
        oracle_impl(update, text.split())

def comp_rules_command(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(
        documents.cr_search(context.args),
        parse_mode='HTML', quote=False)


def ask_command(bot, update):
    pass


def dispatcher_setup(dispatcher):
    dispatcher.add_handler(CommandHandler('start', start_command))
    dispatcher.add_handler(CommandHandler('help', start_command))
    dispatcher.add_handler(CommandHandler('o', oracle_command, pass_args=True))
#    dispatcher.add_handler(
#        CommandHandler(
#            'q',
#            question_command,
#            pass_args=True))
    dispatcher.add_handler(
        CommandHandler(
            'cr',
            comp_rules_command,
            pass_args=True))
#    dispatcher.add_handler(CommandHandler('ask', ask_command, pass_args=True))
    dispatcher.add_handler(InlineQueryHandler(inline_oracle))
    dispatcher.add_handler(CallbackQueryHandler(callback_name))
    dispatcher.add_handler(MessageHandler(Filters.text, text_filter))


with open('config.json') as file:
    config = json.load(file)

updater = Updater(config['token'])
dispatcher_setup(updater.dispatcher)
updater.start_polling()
updater.idle()
