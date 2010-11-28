# Copyright (C) 2010 Sun Ning <classicning@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
#
#
# The developers of the Exaile media player hereby grant permission
# for non-GPL compatible GStreamer and Exaile plugins to be used and
# distributed together with GStreamer and Exaile. This permission is
# above and beyond the permissions granted by the GPL license by which
# Exaile is covered. If you modify this code, you may extend this
# exception to your version of the code, but you are not obligated to
# do so. If you do not wish to do so, delete this exception statement
# from your version.
#

import os
import fnmatch

import indicate
import dbus

from mpris2 import Mpris2Adapter

from xl import event

MPRIS2 = None
def enable(exaile):
    if exaile.loading:
        event.add_callback(_enable, "exaile_loaded")
    else:
        _enable(None, exaile, None)

def _enable(nothing, exaile, nothing2):
    global MPRIS2
    MPRIS2 = Mpris2Manager(exaile)
    MPRIS2.acquire()
    init_indicate()
    event.add_callback(_clean_tmp, 'quit_application')

def disable(exaile):
    global MPRIS2
    MPRIS2.release()
    event.remove_callback(_clean_tmp, 'quit_application')

def _clean_tmp(type, exaile, data):
    for tmp in os.listdir('/tmp'):
        if fnmatch.fnmatch(tmp, 'exaile-soundmenu*'):
            os.remove('/tmp/'+tmp)

def init_indicate():
    server = indicate.indicate_server_ref_default()
    server.set_type('music.exaile')
    server.set_desktop_file('/usr/share/applications/exaile.desktop')
    server.show()

DBUS_OBJECT_NAME = 'org.mpris.MediaPlayer2.exaile'
class Mpris2Manager(object):
    def __init__(self, exaile):
        self.exaile = exaile
        self.bus = None
        
    def acquire(self):
        if self.bus:
            self.bus.get_bus().request_name(DBUS_OBJECT_NAME)
        else:
            self.bus = dbus.service.BusName(DBUS_OBJECT_NAME, bus=dbus.SessionBus())
        self.adapter = Mpris2Adapter(self.exaile, self.bus)

    def release(self):
        if self.adapter is not None:
            self.adapter.remove_from_connection()
        if self.bus is not None:
            self.bus.get_bus().release_name(self.bus.get_name())
        

