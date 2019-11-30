from urllib.request import Request, urlopen, HTTPError
import json
import sys
import shutil
from pathlib import Path

def save(name, data):
    with open(name, 'w', encoding = 'utf8') as file:
        json.dump(data, file, ensure_ascii = False, indent = 4, sort_keys = True)

def download(url):
    cards = list()
    page = 1
    nonEmpty = True
    while nonEmpty:
        request_url = '{}page={}'.format(url, page)
        print('Loading page {}...'.format(page))
        try:
            req = Request(request_url, headers={'User-Agent': 'Mozilla/5.0'})
            response = json.loads(urlopen(req).read().decode("utf-8"))
            cardsPage = response['cards']
            nonEmpty = bool(cardsPage)
            if nonEmpty:
                cards.extend(cardsPage)
                page += 1
        except HTTPError as e:
            print ('Failed at page {}: {}'.format(page, e.reason))
    return cards

names = {}
oracle = {}
oracle_file_name = 'data/oracle.json'
names_file_name = 'data/names.json'


def download_all():
    print ("downloading the whole card set")
    return download('https://api.magicthegathering.io/v1/cards?')


def download_set(set_name):
    print ("downloading set {}".format(set_name))
    return download('https://api.magicthegathering.io/v1/cards?set={}&'.format(set_name))


def process_cards(cards):
    languages = ['Russian']
    ignore = [
        {'language': 'Russian', 'name': 'Plunder'},
        {'language': 'Russian', 'name': 'Goblin Spelunkers'},
        {'language': 'Russian', 'name': 'Raise Dead'},
    ]
    copy = ['name', 'flavor', 'power', 'toughness', 'colors', 'printings', 'legality', 'manaCost', 'subtypes', 'text', 'layout', 'colorIdentity', 'type', 'types', 'cmc', 'loyalty', 'rulings']
    for card in cards:
        if card['name'] in names:
            if not card['name'] in names[card['name']]:
                names[card['name']].append(card['name'])
            else:
                names[card['name']] = [card['name']]

        if 'foreignNames' in card:
            for translation in card['foreignNames']:
                if translation['name'] and translation['language'] in languages and not {'language': translation['language'], 'name': card['name']} in ignore:
                    if translation['name'] in names:
                        if not card['name'] in names[translation['name']]:
                            print('{} version of "{}": "{}" is named as another card "{}"'.format(translation['language'], card['name'], translation['name'], names[translation['name']]))
                            names[translation['name']].append(card['name'])

                    else:
                        names[translation['name']] = [card['name']]

        if not card['name'] in oracle:
            oracle[card['name']] = {k: card[k] for k in card if k in copy}


def backup_data_files():
    try:
        shutil.copyfile(oracle_file_name, oracle_file_name + ".bak")
        shutil.copyfile(names_file_name, names_file_name + '.bak')
        return True
    except shutil.Error:
        return False


if len(sys.argv) == 2:
    if not Path(oracle_file_name).is_file() or not Path(names_file_name).is_file():
        print("oracle of name files don't exist. Exiting")
        exit()

    if not backup_data_files():
        print("failed to create backup files. Exiting")
        exit()

    with open(names_file_name) as file:
        names = json.load(file)
    with open(oracle_file_name) as file:
        oracle = json.load(file)

    cards = download_set(sys.argv[1])
else:
    cards = download_all()

process_cards(cards)
save('data/names.json', names)
save('data/oracle.json', oracle)
