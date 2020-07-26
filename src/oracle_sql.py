import sqlite3
import codecs

def quote_identifier(s, errors="strict"):
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

def get_card(name):
    t = ( name,)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT(name), type, text, manacost, loyalty, power, toughness FROM cards WHERE name LIKE ?", t)
    row = cursor.fetchone()
    if not row:
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

    return result


def get_matching_names(words):
    condition = ''

    for word in words:
        if condition:
            condition = condition + ' AND '

        condition = condition + "name LIKE '%" + quote_identifier(word) + "%'"

    query = 'SELECT DISTINCT(name) FROM cards WHERE ' + condition
    cursor = conn.cursor()
    cursor.execute(query)
    return [row[0] for row in cursor.fetchall()]


def get_oracle_names(name):
    card = get_card(name)
    if not card:
        return None

    return [card['name']]

