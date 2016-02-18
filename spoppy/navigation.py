import logging
import shutil
import sys

import click

from . import get_version, menus, responses
from .lifecycle import LifeCycle
from .players import Player

logger = logging.getLogger(__name__)


class Leifur(object):
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.player = Player(self)
        self.lifecycle = LifeCycle(username, password, self.player)
        self.session = None
        logger.debug('Leifur initialized')

    def start(self):
        if self.lifecycle.check_pyspotify_logged_in():
            logger.debug('All tokens are a-OK')
            self.session = self.lifecycle.get_pyspotify_client()
            logger.debug('Starting LifeCycle services')
            self.lifecycle.start_lifecycle_services()
            logger.debug('LifeCycle services started')
            main_menu = menus.MainMenu(self)
            while True:
                self.navigate_to(main_menu)
        else:
            click.echo(
                'Could not log you in, please check your username (%s) '
                'and password are correct' % self.username
            )
            logger.debug('Something went wrong, not logged in...')

    def shutdown(self):
        self.lifecycle.shutdown()

    def navigate_to(self, going):
        logger.debug('navigating to: %s' % going)
        self.session.process_events()
        going.initialize()
        while True:
            logger.debug('clearing screen...')
            click.clear()
            self.print_header()
            self.print_menu(going.get_ui())
            response = going.get_response()
            logger.debug('Got response %s' % response)
            if response == responses.QUIT:
                click.clear()
                click.echo('Thanks, bye!')
                sys.exit(0)
            elif response == responses.UP:
                break
            elif response == responses.NOOP:
                continue
            elif response == responses.PLAYER:
                self.navigate_to(self.player)
            else:
                if callable(response):
                    response = response()
                self.navigate_to(response)
            # This happens when the `going` instance gets control again. We
            # don't want to remember the query and we want to rebuild the
            # menu's options
            # (and possibly something else?)
            going.initialize()

    def print_header(self):
        click.echo('Spoppy v. %s' % get_version())
        click.echo('Hi there %s' % self.username)
        click.echo('')

    def print_menu(self, menu):
        if isinstance(menu, str):
            click.echo(menu)
        elif isinstance(menu, (list, tuple)):
            for item in menu:
                if isinstance(item, (list, tuple)):
                    if len(item) == 2:
                        click.echo(
                            ''.join((
                                item[0],
                                ' ' * (
                                    self.get_ui_width() -
                                    len(item[0]) -
                                    len(item[1])
                                ),
                                item[1]
                            ))
                        )
                    else:
                        click.echo(item[0])
                else:
                    click.echo(item)
            click.echo('')

    def update_progress(self, status, start, perc, end):
        s = '\r[%s] %s[%s]%s' % (
            status,
            start,
            '%s',
            end or ''
        )
        progress_width = self.get_ui_width() - len(s) + 2
        s = s % ('#'*int(perc*progress_width)).ljust(progress_width)

        click.echo(s, nl=False)

    def get_ui_width(self):
        return shutil.get_terminal_size((120, 40)).columns
