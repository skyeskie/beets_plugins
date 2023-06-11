#  Copyright (c) 2020-2023
#  Author: Scott Yeskie
#  License: See LICENSE.txt

from optparse import OptionParser

from beets.dbcore import AndQuery
from beets.dbcore.query import NoneQuery
from beets.library import Library, Item, parse_query_parts
from beets.ui import Subcommand, decargs
from confuse import Subview

from beetsplug.title_trunc import common
from beetsplug.title_trunc.length_query import MaxLengthQuery


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

    def func(self, lib: Library, options, arguments):
        self.lib = lib
        self.query = decargs(arguments)

        if options.version:
            self.show_version_information()
            return

        self.cfg_length = options.max_len
        self.handle_main_task()

    def handle_main_task(self):
        items = self.retrieve_library_items()
        if not items:
            "No items selected to process"
            return

        for item in items:
            self.process_item(item)
            item.try_write()
            item.store()

    def retrieve_library_items(self):
        cmd_query = self.query
        parsed_cmd_query, parsed_ordering = parse_query_parts(cmd_query, Item)
        len_query = MaxLengthQuery('title', str(self.cfg_length))

        if self.cfg_force:
            full_query = AndQuery([parsed_cmd_query, len_query])
        else:
            full_query = AndQuery([parsed_cmd_query, len_query, NoneQuery('title_short')])

        return self.lib.items(full_query, parsed_ordering)

    def process_item(self, item: Item):
        title = item.get("title")
        title_short = item.get("title_short")

        # Generate options
        # - Truncate with ""
        # - Collapse middle
        # - Remove before/after :
        # - Remove in ( )
        # - Remove after : except in ( )
        # - Existing short title (if present)

        # User selects option

        # Set attribute on output
        # Writing handled in [main]
        return self.cfg_length

    def show_version_information(self):
        self._say("{pt}({pn}) plugin for Beets: v{ver}".format(
            pt=common.plg_ns['__PACKAGE_TITLE__'],
            pn=common.plg_ns['__PACKAGE_NAME__'],
            ver=common.plg_ns['__version__']
        ), log_only=False)

    @staticmethod
    def _say(msg, log_only=True, is_error=False):
        common.say(msg, log_only, is_error)
