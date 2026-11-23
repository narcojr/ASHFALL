"""Builds one self-contained HTML file for the presentation:  python presentation/build.py"""
import base64
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

import server  # noqa: E402
from src import art, campaign  # noqa: E402

ART_DIR = art.ART_DIR


def data_uri(path, mime):
    with open(path, 'rb') as f:
        return 'data:%s;base64,%s' % (mime, base64.b64encode(f.read()).decode())


def read(*parts):
    with open(os.path.join(ROOT, *parts), encoding='utf-8') as f:
        return f.read()


images = {}
for name in sorted(os.listdir(ART_DIR)):
    if name.endswith('.png'):
        images[name[:-4]] = data_uri(os.path.join(ART_DIR, name), 'image/png')

data = {'cfg': server.build_config(), 'levels': {str(n): campaign.build_level(n) for n in (1, 2, 3)}, 'images': images}
css = open(os.path.join(HERE, 'style.css'), encoding='utf-8').read()
css = css.replace('__FONT__', data_uri(os.path.join(ART_DIR, 'ashpixel.ttf'), 'font/ttf'))
css = css.replace('__PANEL__', images['panel']).replace('__BTN__', images['btn'])

html = open(os.path.join(HERE, 'template.html'), encoding='utf-8').read()
boot = ('window.Ash.setConfig(window.DECK.cfg);'
        'window.Ash.sprites.load(window.DECK.cfg.art).then(function(){' + open(os.path.join(HERE, 'deck.js'), encoding='utf-8').read() + '});')
html = (html.replace('/*__CSS__*/', css)
        .replace('/*__DATA__*/', json.dumps(data, separators=(',', ':')))
        .replace('/*__ENGINE__*/', read('static', 'js', 'engine.js'))
        .replace('/*__SPRITES__*/', read('static', 'js', 'sprites.js'))
        .replace('/*__RENDER__*/', read('static', 'js', 'render.js'))
        .replace('/*__DECKJS__*/', boot))
out = os.path.join(HERE, 'ASHFALL_Presentation.html')
with open(out, 'w', encoding='utf-8') as f:
    f.write(html)
print(out, len(html) // 1024, 'KB')
