#!/bin/sh
mkdir -p data
python3 scripts/update_cards.py
curl https://media.wizards.com/2019/downloads/MagicCompRules%2020190503.txt --output cr.txt
python3 scripts/update_cr.py
