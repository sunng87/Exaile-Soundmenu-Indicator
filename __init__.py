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

import indicate
import dbus

from mpris2 import Mpris2Adapter

INDICATOR_PLUGIN = None
def enable(exaile):
    mpris2_mgr = Mpris2Manager(exaile)
    mpris2_mgr.acquire()
    init_indicate()

def disable(exaile):
    mpris2_mgr.release()

def init_indicate():
    server = indicate.indicate_server_ref_default()
    server.set_type('music.exaile')
    server.set_desktop_file('/usr/share/applications/exaile.desktop')
    server.show()

class Mpris2Manager(object):
    NAME = 'org.mpris.MediaPlayer2.exaile'
    def __init__(self, exaile):
        self.exaile = exaile
        self.bus = None
        
    def acquire(self):
        if self.bus:
            self.bus.get_bus().request_name(self.NAME)
        else:
            self.bus = dbus.service.BusName(self.NAME, bus=dbus.SessionBus())
        self.adapter = Mpris2Adapter(self.exaile, self.bus)

    def release(self):
        if self.adapter is not None:
            self.adapter.remove_from_connection()
        if self.bus is not None:
            self.bus.get_bus().release_name(self.bus.get_name())
        

