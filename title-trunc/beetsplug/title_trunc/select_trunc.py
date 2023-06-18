#  Copyright (c) 2023
#  Author: Scott Yeskie
#  License: See LICENSE.txt

import re

from beets.ui import input_options


def select_from_options(title: str, title_short: str | None, length: int) -> str | None:
    ellip = '…'
    halflen = (length / 2).__floor__()

    # Todo: move this to configuration
    repl_map = {
        # Include character mapping
        ':': '∶',
        '/': " ⁄ ",
        '*': "∗",
        '?': "？",
        '"': '″',
        '.': '․',
        '|': 'ǀ',
        '<': '‹',
        '>': '›',
        '\\': '⧵',
        # Consolidate symbols
        '—': '–',
        '―': '–',
        '»': '“',
        '«': '“',
        # Shortening
        'No․': '#',
        ' no․': ' #',
        'NO․': '#',
        '# ': '#',
        '...': ellip,
        # Space trimming
        '    ': ' ',
        '   ': ' ',
        '  ': ' ',
    }
    rep_title = title.strip()
    for key, rep in repl_map.items():
        rep_title = rep_title.replace(key, rep)

    if len(rep_title) <= length:
        return rep_title

    # Remove key
    no_key = re.sub(' in [A-G][^∶]+∶', '∶', rep_title)
    if no_key != rep_title:
        print('No key:: {}'.format(no_key))

    separators = ['–', '∶', '⁄', '？', 'ǀ', '⧵']
    more = '․.″\',”’？!&#«»'
    # ″nickname″
    # ․․․ to ellip
    # ( ) ( )

    options = [
        # Ellipsis at end
        rep_title[0:length - 1] + ellip,
        # Split in half and put ellipsis in middle
        ''.join([rep_title[:halflen - 1], ellip, rep_title[-halflen:]]),
    ]
    if title_short:
        options.append(title_short)

    last_colon = rep_title.rfind(':', 0, length)
    print('Last colon: {}'.format(last_colon))
    if last_colon > 1:
        options.append(rep_title[:last_colon])

    first_colon = rep_title.find(':', len(rep_title) - length)
    if first_colon > 0:
        options.append(rep_title[first_colon:])

    rev_threshold = len(rep_title) - length
    first_sep = len(rep_title) + 1  # Find the smallest location >= (len(title) - length)
    last_sep = -1  # Find the largest location <= length
    for sep in separators:
        pos = 0
        while pos < len(rep_title):
            print('Found <{}> at {}'.format(sep, pos))
            pos = rep_title.find(sep, pos)
            if pos == -1:
                break
            if last_sep < pos < length:
                last_sep = pos
            pos += 1
            if rev_threshold < pos < first_sep:
                first_sep = pos
    if first_sep < len(rep_title):
        options.append(rep_title[first_sep:].strip())
    if last_sep > 0:
        options.append(rep_title[:last_sep].strip())

    no_paren = re.sub(r'(\s*)\([^)]*\)(\s*)', '\1\2', rep_title).replace('  ', ' ')
    if no_paren != rep_title and len(no_paren) < length:
        options.append(no_paren)

    paren_groups = re.findall(r'\([^)]+\)', rep_title)
    if len(paren_groups) > 0:
        last_paren = paren_groups[-1]
        shortlen = length - len(last_paren) - 1
        if shortlen > halflen:
            colon_at = rep_title.rfind(':', 0, shortlen)
            if colon_at > 1:
                options.append('{} {}'.format(rep_title[:colon_at], last_paren))

    return user_select(options)


def user_select(options: list[str]) -> str | None:
    if len(options) == 0:
        return None
    if len(options) <= 1:
        return options[0]

    print('Select title abbreviation')
    for i, option in enumerate(options):
        print('{}. {}'.format(i + 1, option)),

    sel = input_options(['Skip'], numrange=(1, len(options)),
                        prompt='(s or #): ')
    print(sel)
    if sel == 's' or sel == 'S':
        return None

    return options[sel - 1]
