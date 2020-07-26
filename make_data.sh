#!/bin/sh
mkdir -p data
#python3 scripts/update_cards.py
curl https://media.wizards.com/2020/downloads/MagicCompRules%2020200703.txt --output cr.txt
curl https://mtgjson.com/api/v5/AllPrintings.sqlite --output data/mtg.sqlite
python3 scripts/update_cr.py

