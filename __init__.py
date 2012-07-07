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

try:
    import indicate
except ImportError:
    pass
import dbus
import gtk

from mpris2 import Mpris2Adapter
from mpris2 import ORG_MPRIS_MEDIAPLAYER2
from mpris2 import ORG_MPRIS_MEDIAPLAYER2_PLAYER
from mpris2 import ORG_MPRIS_MEDIAPLAYER2_TRACKLIST

from xl import event, settings
from xl.player import PLAYER

MPRIS2 = None
_WINDOW_STATE_HANDLER = None
def enable(exaile):
    if exaile.loading:
        event.add_callback(_enable, "exaile_loaded")
    else:
        _enable(None, exaile, None)

def _enable(nothing, exaile, nothing2):
    global MPRIS2
    MPRIS2 = Mpris2Manager(exaile)
    MPRIS2.acquire()
    MPRIS2.register_events()
    init_indicate()
    event.add_callback(_clean_tmp, 'quit_application')
#    _WINDOW_STATE_HANDLER = exaile.gui.main.window.connect("window_state_event", _destroy_window_and_tray, exaile)
    _WINDOW_STATE_HANDLER = exaile.gui.main.window.connect("delete-event", _delete_event, exaile)
    patch_tray_icon(exaile)

def patch_tray_icon(exaile):    
    ### currently this function still not work 
    settings.set_option('gui/minimize_to_tray', False)
    exaile.gui.main.controller.tray_icon = DummyTrayIcon()
    settings.set_option('gui/use_tray', False)

class DummyTrayIcon(object):
    def destroy(self):
        pass

def disable(exaile):
    global MPRIS2
    MPRIS2.unregister_events()
    MPRIS2.release()
    event.remove_callback(_clean_tmp, 'quit_application')
    if _WINDOW_STATE_HANDLER is not None:
        exaile.gui.main.window.disconnect(_WINDOW_STATE_HANDLER)

def _delete_event(window, event, exaile):
    """ window behavior on closing, according to sound menu spec:
        https://wiki.ubuntu.com/SoundMenu
        """
    if exaile.player.is_playing():
        window.hide()
    else:
        exaile.gui.main.quit()
    return True

def _destroy_window_and_tray(window, event, exaile):
    if event.changed_mask & gtk.gdk.WINDOW_STATE_ICONIFIED:
        window.hide()
        window.deiconify()

def _clean_tmp(type, exaile, data):
    tmpdir = os.path.expanduser('~/.cache/exaile/')
    for tmp in os.listdir(tmpdir):
        if fnmatch.fnmatch(tmp, 'exaile-soundmenu*'):
            os.remove(os.path.join(tmpdir, tmp))

def init_indicate():
    ## for Maverick registration
    try:
        server = indicate.indicate_server_ref_default()
        server.set_type('music.exaile')
        server.set_desktop_file('/usr/share/applications/exaile.desktop')
        server.show()
    except:
        pass

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
        ### for Natty registration
        self.adapter.populate(ORG_MPRIS_MEDIAPLAYER2, 'DesktopEntry')

    def register_events(self):
        event.add_callback(self.on_playback_start, 'playback_track_start')
        event.add_callback(self.on_playback_start, 'playback_player_start')
        event.add_callback(self.on_playback_end, 'playback_track_end')
        event.add_callback(self.on_playback_pause, 'playback_player_pause')
        event.add_callback(self.on_playback_pause, 'playback_toggle_pause')
        event.add_callback(self.on_tags_update, 'track_tags_changed')
        event.add_callback(self.on_option_change, 'option_set')
        # TODO: need a "seeked" callback

    def release(self):
        if self.adapter is not None:
            self.adapter.remove_from_connection()
        if self.bus is not None:
            self.bus.get_bus().release_name(self.bus.get_name())

    def unregister_events(self):
        event.remove_callback(self.on_playback_start, 'playback_track_start')
        event.remove_callback(self.on_playback_start, 'playback_player_start')
        event.remove_callback(self.on_playback_end, 'playback_track_end')
        event.remove_callback(self.on_playback_pause, 'playback_player_pause')
        event.remove_callback(self.on_playback_pause, 'playback_toggle_pause')
        event.remove_callback(self.on_tags_update, 'track_tags_changed')
        event.remove_callback(self.on_option_change, 'option_set')

    def on_playback_start(self, evt, exaile, data):
        self.adapter.populate(ORG_MPRIS_MEDIAPLAYER2_PLAYER,
                'PlaybackStatus', 'Metadata', 'CanGoNext', 'CanGoPrevious',
                'CanPause', 'CanPlay')

    def on_playback_end(self, evt, exaile, data):
        self.adapter.populate(ORG_MPRIS_MEDIAPLAYER2_PLAYER,
                'PlaybackStatus', 'Metadata', 'CanGoNext', 'CanGoPrevious',
                'CanPause', 'CanPlay')

    def on_playback_pause(self, evt, exaile, data):
        self.adapter.populate(ORG_MPRIS_MEDIAPLAYER2_PLAYER,
                'PlaybackStatus', 'CanPause', 'CanPlay')

    def on_tags_update(self, evt, track, data):
        if track == PLAYER.current:
            self.adapter.populate(ORG_MPRIS_MEDIAPLAYER2_PLAYER, 'Metadata')

    def on_option_change(self, evt, settings_manager, data):
        if data == 'playback/repeat':
            self.adapter.populate(ORG_MPRIS_MEDIAPLAYER2_PLAYER, 'LoopStatus')
        elif data == 'playback/shuffle':
            self.adapter.populate(ORG_MPRIS_MEDIAPLAYER2_PLAYER, 'Shuffle')
        elif data == 'player/volume':
            self.adapter.populate(ORG_MPRIS_MEDIAPLAYER2_PLAYER, 'Volume')
