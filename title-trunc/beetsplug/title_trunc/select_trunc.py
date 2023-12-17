#  Copyright (c) 2023
#  Author: Scott Yeskie
#  License: See LICENSE.txt

import re
from collections import namedtuple
from math import floor

from beaupy import select, prompt, Config, DefaultKeys
from beets.library import Library, Album, Item
from beets.ui import colorize
from yakh.key import Keys

ellip = '…'
rep_colon = '∶'

SelOption = namedtuple('SelOption', ['pos', 'title'])


class SelectTrunc:
    def __init__(
            self,
            item: Item,
            library: Library,
            length: int,
            # options: list[SelOption],
            # title: str,
    ):
        self.main_commands = [
            SelOption('A', 'See Album'),
            SelOption('S', 'Skip'),
            SelOption('Q', 'Quit'),
            SelOption(' ', 'Edit'),
        ]

        self.edit_commands = [
            SelOption(' ', '<Blank>')
        ]

        self.separators = ['–', rep_colon, '⁄', '？', 'ǀ', '⧵']

        self.option_index = 0
        self.options = []
        self.library = library
        self.item = item
        self.length = length
        self.halflen = floor(length / 2)

        self.full_title = item.get('title')
        self.title_short = item.get('title_short')

        # Do title replacements
        self.title = self._make_title_substitutions()
        self.title_no_key = self._remove_key_from_title()

    def get_short_title(self) -> str:
        if len(self.title) <= self.length:
            return self.title
        self._generate_options()
        selected = self._user_select_main()
        if selected is None:
            print(colorize('red', 'Skip'))
        else:
            print(colorize('green', selected))
        return selected

    def _generate_options(self):
        no_paren = re.sub(r'(\s*)\([^)]*\)(\s*)', '\1\2', self.title).replace('  ', ' ')
        if no_paren == self.title or len(no_paren) > self.length:
            no_paren = None

        # Existing title
        self.add_option(self.title_short, key=0)
        # Ellipsis at end
        self.add_option(self.title[0:self.length - 1] + ellip)
        # Split in half and put ellipsis in middle
        self.add_option(''.join([self.title[:self.halflen - 1], ellip, self.title[-self.halflen:]]))
        self._add_truncate_at_separator_option(['∶'], self.title)
        self._add_truncate_at_separator_option(self.separators, self.title)
        self.add_option(no_paren)
        self._add_truncate_after_last_colon_leave_paren_option()

    def _add_truncate_at_separator_option(self, separators: list[str], msg: str):
        rev_threshold = len(msg) - self.length
        first_sep = len(msg) + 1  # Find the smallest location >= (len(title) - length)
        last_sep = -1  # Find the largest location <= length
        for sep in separators:
            pos = 0
            while pos < len(msg):
                pos = msg.find(sep, pos)
                if pos == -1:
                    break
                if last_sep < pos < self.length:
                    last_sep = pos
                pos += 1
                if rev_threshold < pos < first_sep:
                    first_sep = pos
        if first_sep < len(msg):
            self.add_option(msg[first_sep:].strip())
        if last_sep > 0:
            self.add_option(msg[:last_sep].strip())

    def _add_truncate_after_last_colon_leave_paren_option(self):
        paren_groups = re.findall(r'\([^)]+\)', self.title)
        if len(paren_groups) == 0:
            return None  # No parenthesis

        last_paren = paren_groups[-1]
        shortlen = self.length - len(last_paren) - 1
        if shortlen <= self.halflen:
            return None  # Parenthesis group over half the length

        colon_at = self.title.rfind(rep_colon, 0, shortlen)
        if colon_at < 1:
            return None  # No colon to replace

        self.add_option('{} {}'.format(self.title[:colon_at], last_paren))

    def add_option(self, text, key=None):
        if not text:
            return
        if not key:
            self.option_index += 1
        self.options.append(
            SelOption(
                key or self.option_index,
                re.sub(
                    r'[\w․.″\',”’？!&#«»]*…[\w․.″\',”’？!&#«»]*',
                    '…',
                    text
                )
            )
        )

    @staticmethod
    def _format_option(option: (int | str, str)) -> str:
        if option[0] == ' ':
            return '   {}'.format(option[1])
        else:
            return '{}. {}'.format(option[0], option[1])

    def _make_title_substitutions(self) -> str:
        repl_map = {  # Todo: move this to configuration
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
        rep_title = self.full_title.strip()
        for key, rep in repl_map.items():
            rep_title = rep_title.replace(key, rep)
        return rep_title

    def _remove_key_from_title(self) -> str:
        return re.sub(' in [A-G][^∶]+∶', '∶', self.title)

    def _user_select_main(self):
        if len(self.options) == 0:
            return None
        if len(self.options) <= 1:
            return self.options[0].title

        self._print_highlight_len(self.title)

        main_result = select(
            options=self.options + self.main_commands,
            preprocessor=self._format_option,
            cursor_style='cyan1',
        )

        match main_result:
            case (_, 'Skip'):
                return None
            case ('A', _):
                album: Album = self.library.get_album(self.item)
                print("\n{}".format(colorize('cyan', album.get('album'))))
                for track in album.items():
                    self._print_highlight_len(track.title, track.track)
                return self._user_select_main()
            case (_, 'Quit'):
                exit(1)
            case ('E', _):
                edit_result = self._user_select_edit()
                if edit_result is not None:
                    return edit_result
            case (_, value):
                return value
            case None:
                return None
            case _:
                exit(2)

    def _user_select_edit(self):
        edit_default = select(
            preprocessor=self._format_option,
            options=[SelOption(0, self.title)]
                    + self.options
                    + self.edit_commands,
            cursor_style='yellow1'
        )

        print(edit_default)
        if edit_default[1] == '<Blank>':
            edit_default = (' ', '')

        result = prompt(
            'Enter truncated title (or Esc) to skip:',
            validator=lambda val: len(val) <= 50,
            initial_value=edit_default[1]
        )
        return result

    # TODO: Modify album
    # 6. Concerto for Piano and Orchestra No․ 2 in B-flat major, Op․ 19∶ III․ Rondo․ Allegro molto
    # 1. Concerto for Piano and Orchestra No․ 1 in C major, Op․ 15∶ I․ Allegro con brio
    # 2. Concerto for Piano and Orchestra No․ 1 in C major, Op․ 15∶ II․ Largo
    # 3. Concerto for Piano and Orchestra No․ 1 in C major, Op․ 15∶ III․ Rondo․ Allegro
    # 4. Concerto for Piano and Orchestra No․ 2 in B-flat major, Op․ 19∶ I․ Allegro con brio
    # 5. Concerto for Piano and Orchestra No․ 2 in B-flat major, Op․ 19∶ II․ Adagio
    # Would want to do a replace "Concerto for Piano and Orchestra" with "Piano Concerto"

    def _print_highlight_len(self, msg: str, track: int | None = None):
        if track:
            track_num = '{: >2}. '.format(track)
        else:
            track_num = ''
        if len(msg) <= self.length:
            track_title = colorize('yellow', msg)
        else:
            msg_trunc = msg[:self.length]
            excess = msg[self.length:]
            track_title = '{}{}'.format(colorize('yellow', msg_trunc), excess)
        print('{}{}'.format(track_num, track_title))

    @staticmethod
    def _prep_keys_main():
        Config.raise_on_interrupt = True
        DefaultKeys.escape = [Keys.ESC, 'S', 's']
        DefaultKeys.interrupt = [Keys.CTRL_C, 'Q', 'q']

    @staticmethod
    def _prep_keys_default():
        DefaultKeys.escape = [Keys.ESC]
        DefaultKeys.interrupt = [Keys.CTRL_C]
