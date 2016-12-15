# -*- coding: utf-8 -*-
# This file is part of beets.
# Copyright 2017, Tigran Kostandyan.
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.

"""Uploads files to Google Play Music"""

from __future__ import print_function
import os.path

from beets.plugins import BeetsPlugin
from beets import ui
from beets import config
from beets.ui import Subcommand
from gmusicapi import Musicmanager, Mobileclient
import gmusicapi.clients


# Checks for OAuth2 credentials, if they don't exist - performs authorization
m = Musicmanager()
if os.path.isfile(gmusicapi.clients.OAUTH_FILEPATH):
    m.login()
else:
    m.perform_oauth()


class Gmusic(BeetsPlugin):
    def __init__(self):
        super(Gmusic, self).__init__()

    def commands(self):
        gupload = Subcommand('gmusic-upload',
                             help=u'upload your tracks to Google Play Music')

        search = Subcommand('gmusic-songs',
                            help=u'list of songs in Google Play Music library'
                            )
        search.parser.add_option('-t', '--track', dest='track',
                                 action='store_true',
                                 help='Search by track name')
        search.parser.add_option('-a', '--artist', dest='artist',
                                 action='store_true',
                                 help='Search by artist')
        gupload.func = self.upload
        search.func = self.search
        return [gupload, search]

    def upload(self, lib, opts, args):
        items = lib.items(ui.decargs(args))
        files = [x.path.decode('utf-8') for x in items]
        ui.print_('Uploading your files...')
        m.upload(filepaths=files)
        ui.print_('Your files were successfully added to library')

    def search(self, lib, opts, args):
        email = config['gmusic']['email'].as_str()
        password = config['gmusic']['password'].as_str()
        # Since Musicmanager doesn't support library management
        # we need to use mobileclient interface
        mobile = Mobileclient()
        try:
            mobile.login(email, password, Mobileclient.FROM_MAC_ADDRESS)
            files = mobile.get_all_songs()
        except:
            ui.print_('Error occured. Please check your email and password')
        if not args:
            for i, file in enumerate(files, start=1):
                print(i, ui.colorize('blue', file['artist']),
                      file['title'], ui.colorize('red', file['album']))
        else:
            if opts.track:
                print(*self.match(files, args, 'title'))
            else:
                print(*self.match(files, args, 'artist'))

    @staticmethod
    def match(files, args, search_by):
        for file in files:
            if ' '.join(args) in file[search_by]:
                return file['artist'], file['title'], file['album']
