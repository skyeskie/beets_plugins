#  Copyright (c) 2020-2023
#  Author: Scott Yeskie
#  License: See LICENSE.txt
import re
from optparse import OptionParser

from beets.dbcore import AndQuery
from beets.dbcore.query import NoneQuery
from beets.library import Library, Item, parse_query_parts
from beets.ui import Subcommand, decargs, input_options
from confuse import Subview

from beetsplug.title_trunc import common
from beetsplug.title_trunc.length_query import OverMaxLengthQuery


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


class TitleTruncCommand(Subcommand):
    config: Subview = None
    lib: Library = None
    query = None
    parser: OptionParser = None

    cfg_force = False
    cfg_length = 50

    def __init__(self, cfg):
        self.config = cfg

        self.parser = OptionParser(
            usage='beet {plg} [options] [QUERY...]'.format(
                plg=common.plg_ns['__PLUGIN_NAME__']
            ))

        self.parser.add_option(
            '-v', '--version',
            action='store_true', dest='version', default=False,
            help=u'show plugin version'
        )

        self.parser.add_option(
            '-f', '--force',
            action='store_true', dest='force', default=self.cfg_force,
            help=u'force analysis of items with short title already set '
        )

        self.parser.add_option(
            '-l', '--length',
            type='int',
            action='store', dest='max_len', default=self.cfg_length,
            help=u'Set length to truncate title'
        )

        super(TitleTruncCommand, self).__init__(
            parser=self.parser,
            name=common.plg_ns['__PLUGIN_NAME__'],
            aliases=[common.plg_ns['__PLUGIN_ALIAS__']] if
            common.plg_ns['__PLUGIN_ALIAS__'] else [],
            help=common.plg_ns['__PLUGIN_SHORT_DESCRIPTION__']
        )

    # def func(self, lib: Library, options, arguments):
    #     self.lib = lib
    #     options = generate_options(
    #         'This is: the end of: (the world) (as we know): (it)',
    #         None, 20
    #     )
    #     sel = select_option(options)
    #     print(sel)

    def func(self, lib: Library, options, arguments):
        print("TT - FUNC")
        self.lib = lib
        self.query = decargs(arguments)

        if options.version:
            self.show_version_information()
            return

        self.cfg_length = options.max_len
        self.cfg_force = options.force
        self.handle_main_task()

    def handle_main_task(self):
        print("MAIN")
        items = self.retrieve_library_items()
        print('{} item(s) found'.format(len(items)))
        if not items:
            "No items selected to process"
            return
        print('Processing items')
        for item in items:
            title = item.get('title')
            self.process_item(item)
            # item.try_write()
            # item.store()

    def retrieve_library_items(self):
        print("RETRIEVE")
        cmd_query = self.query
        parsed_cmd_query, parsed_ordering = parse_query_parts(cmd_query, Item)
        len_query = OverMaxLengthQuery('title', str(self.cfg_length))

        if self.cfg_force:
            full_query = AndQuery([parsed_cmd_query, len_query])
        else:
            full_query = AndQuery([parsed_cmd_query, len_query, NoneQuery('title_short')])
        print(full_query)
        return self.lib.items(full_query, parsed_ordering)

    def process_item(self, item: Item):
        title: str = item.get("title")
        title_short: str = item.get("title_trunc")
        if len(title) <= self.cfg_length:
            return
        if not self.cfg_force and (title_short and len(title_short) <= self.cfg_length):
            return

        sel = select_from_options(
            title,
            title_short, self.cfg_length
        )
        if sel is not None:
            item.set_parse('title_trunc', sel)

    def show_version_information(self):
        self._say("{pt}({pn}) plugin for Beets: v{ver}".format(
            pt=common.plg_ns['__PACKAGE_TITLE__'],
            pn=common.plg_ns['__PACKAGE_NAME__'],
            ver=common.plg_ns['__version__']
        ), log_only=False)

    @staticmethod
    def _say(msg, log_only=True, is_error=False):
        common.say(msg, log_only, is_error)
