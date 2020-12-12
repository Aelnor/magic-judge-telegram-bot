import sqlite3
import codecs
import logging

from typing import List, Dict, Optional


def quote_identifier(s: str, errors: str = "strict") -> str:
    encodable = s.encode("utf-8", errors).decode("utf-8")

    nul_index = encodable.find("\x00")

    if nul_index >= 0:
        error = UnicodeEncodeError("NUL-terminated utf-8", encodable,
                                   nul_index, nul_index + 1, "NUL not allowed")
        error_handler = codecs.lookup_error(errors)
        replacement, _ = error_handler(error)
        encodable = encodable.replace("\x00", replacement)

    return encodable.replace("\"", "\"\"")


conn = sqlite3.connect('data/mtg.sqlite', check_same_thread=False)


def get_card(name: str) -> Optional[Dict[str, str]]:
    logging.debug("get_card: %s", name)
    t = (name,)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT(name), type, text, manacost, loyalty, power, toughness, layout FROM cards WHERE name LIKE ?", t)
    row = cursor.fetchone()
    if not row:
        logging.debug("No card by name '%s' found, let's try faceName", name)
        cursor.execute("SELECT DISTINCT(faceName), type, text, manacost, loyalty, power, toughness, layout FROM cards WHERE faceName LIKE ?", t)
        row = cursor.fetchone()
        if not row:
            logging.debug("No card by name '%s' found, even with facename", name)
            return None

    result = {
        'name': row[0],
        'type': row[1]
    }

    if row[2]:
        result['text'] = row[2]

    if row[3]:
        result['manaCost'] = row[3]

    if row[4]:
        result['loyalty'] = row[4]

    if row[5] and row[6]:
        result['power'] = row[5]
        result['toughness'] = row[6]

    logging.debug("card '%s' => %s", name, result)
    return result


def get_matching_names(words: List[str]) -> List[str]:
    condition = ''

    for word in words:
        if condition:
            condition = condition + ' AND '

        condition = condition + "name LIKE '%" + quote_identifier(word) + "%'"

    logging.debug("condition is %s", condition)
    query = 'SELECT DISTINCT(name) FROM cards WHERE ' + condition
    cursor = conn.cursor()
    cursor.execute(query)
    return [row[0] for row in cursor.fetchall()]


def get_oracle_names(name: str) -> Optional[list[str]]:
    card = get_card(name)
    if not card:
        return None

    return [card['name']]
