from __future__ import annotations
import sqlite3
import codecs
import logging

from typing import List, Dict, Optional

class CardCharacteristics:
    name: str = "" 
    card_type: str = ""
    text: Optional[str] = None
    manacost: Optional[str] = None
    loyalty: Optional[str] = None
    power: Optional[str] = None
    toughness: Optional[str] = None

    def __init__(self, row: list[str]) -> None:
        self.name = row[0]
        self.card_type = row[1]
        if row[2]:
            self.text = row[2]

        if row[3]:
            self.manacost = row[3]

        if row[4]:
            self.loyalty = row[4]

        if row[5] and row[6]:
            self.power = row[5]
            self.toughness = row[6]

    def format(self) -> str:
        mana = ''
        if self.manacost:
            mana = '\t' + self.manacost
        text = ''
        if self.text:
            text = '\n' + self.text
        footer = ''
        if self.card_type and "Creature" in self.card_type:
            footer = '\n{}/{}'.format(self.power , self.toughness)
        if self.card_type and "Planeswalker" in self.card_type and self.loyalty:
            footer = '\n{}'.format(self.loyalty)
        return '<b>{}</b>{}\n<i>{}</i>{}{}'.format(
            self.name,
            mana,
            self.card_type,
            text,
            footer)


class Card:
    name: str = "" 
    face: CardCharacteristics
    back: Optional[CardCharacteristics] = None

    def __init__(self, name: str):
        self.name = name

    @classmethod
    def from_normal(cls, row: list[str]) -> Card:
        result = Card(row[0])
        result.face = CardCharacteristics(row)
        return result


    @classmethod
    def from_double_sided(cls, name: str, face_row: List[str], back_row: List[str]) -> Card:
        result = Card(name)
        result.face = CardCharacteristics(face_row)
        result.back = CardCharacteristics(back_row)

        return result

    def format(self) -> str:
        if not self.back:
            return self.face.format()

    
        return "<b>{}</b>\n{}\n//\n{}".format(self.name, self.face.format(), self.back.format())

        
def quote_identifier(s: str, errors: str = "strict") -> str:
    encodable = s.encode("utf-8", errors).decode("utf-8")

    nul_index = encodable.find("\x00")

    if nul_index >= 0:
        error = UnicodeEncodeError("NUL-terminated utf-8", encodable,
                                   nul_index, nul_index + 1, "NUL not allowed")
        error_handler = codecs.lookup_error(errors)
        replacement, _ = error_handler(error)
        encodable = encodable.replace("\x00", replacement)

    return encodable.replace("\"", "\"\"").replace("'", "''")


conn = sqlite3.connect('data/mtg.sqlite', check_same_thread=False)

def fetch_face(name:str) -> Optional[List[str]]:
    t = (name,)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT(faceName), type, text, manacost, loyalty, power, toughness, layout FROM cards WHERE faceName = ?", t)
    return cursor.fetchone()


def get_card(name: str) -> Optional[Card]:
    t = (name,)
    cursor = conn.cursor()
    faces = name.split(" // ")
    if len(faces) == 1:
        cursor.execute("SELECT DISTINCT(name), type, text, manacost, loyalty, power, toughness, layout FROM cards WHERE name LIKE ?", t)
        row = cursor.fetchone()
        if not row:
            return None
        return Card.from_normal(row)

    if len(faces) == 2:
        face_row = fetch_face(faces[0])
        back_row = fetch_face(faces[1])
        if not face_row or not back_row:
           return None 

        return Card.from_double_sided(name, face_row, back_row)

    return None


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

    return [card.name]
