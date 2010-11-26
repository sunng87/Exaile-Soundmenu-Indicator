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

import dbus
import dbus.service

from xl import settings
from xl.covers import MANAGER as cover_manager

ORG_MPRIS_MEDIAPLAYER2="org.mpris.MediaPlayer2"
ORG_MPRIS_MEDIAPLAYER2_PLAYER="org.mpris.MediaPlayer2.Player"
ORG_MPRIS_MEDIAPLAYER2_TRACKLIST="org.mpris.MediaPlayer2.TrackList"
class Mpris2Adapter(dbus.service.Object):
    """ interface defined by org.mpris.MediaPlayer2"""
    def __init__(self, exaile, bus):
#        super(Mpris2Adapter, self).__init__(self, bus, unicode('/org/mpris/MediaPlayer2'))
        dbus.service.Object.__init__(self, bus, '/org/mpris/MediaPlayer2')
        self.exaile = exaile
        
    @dbus.service.method(ORG_MPRIS_MEDIAPLAYER2)
    def Raise(self):
        pass

    @dbus.service.method(ORG_MPRIS_MEDIAPLAYER2)
    def Quit(self):
        self.exaile.quit()

    @dbus.service.method(ORG_MPRIS_MEDIAPLAYER2, out_signature="b")
    def CanQuit(self):
        return True

    @dbus.service.method(ORG_MPRIS_MEDIAPLAYER2, out_signature="b")
    def CanRaise(self):
        return False

    @dbus.service.method(ORG_MPRIS_MEDIAPLAYER2, out_signature="b")
    def HasTrackList(self):
        return False

    @dbus.service.method(ORG_MPRIS_MEDIAPLAYER2, out_signature="s")
    def Identity(self):
        return "Exaile"
    
    @dbus.service.method(ORG_MPRIS_MEDIAPLAYER2, out_signature="s")
    def DesktopEntry(self):
        return "/usr/share/applications/exaile.desktop"

    @dbus.service.method(ORG_MPRIS_MEDIAPLAYER2_PLAYER)
    def Next(self):
        self.exaile.queue.next()

    @dbus.service.method(ORG_MPRIS_MEDIAPLAYER2_PLAYER)
    def Previous(self):
        self.exaile.queue.prev()

    @dbus.service.method(ORG_MPRIS_MEDIAPLAYER2_PLAYER)
    def Pause(self):
        self.exaile.player.pause()

    @dbus.service.method(ORG_MPRIS_MEDIAPLAYER2_PLAYER)
    def PlayPause(self):
        if not self.exaile.player.is_playing():
            self.exaile.queue.play()
        else:
            self.exaile.player.toggle_pause()

    @dbus.service.method(ORG_MPRIS_MEDIAPLAYER2_PLAYER)
    def Stop(self):
        self.exaile.player.stop()

    @dbus.service.method(ORG_MPRIS_MEDIAPLAYER2_PLAYER)
    def Play(self):
        self.exaile.queue.play()

    @dbus.service.method(ORG_MPRIS_MEDIAPLAYER2_PLAYER, in_signature='x')
    def Seek(self, offset):
        pass

    @dbus.service.method(ORG_MPRIS_MEDIAPLAYER2_PLAYER, in_signature='ox')
    def SetPosition(self, track_id, position):
        pass

    @dbus.service.method(ORG_MPRIS_MEDIAPLAYER2_PLAYER, in_signature='s')
    def OpenUri(self, uri):
        pass

    @dbus.service.method(ORG_MPRIS_MEDIAPLAYER2_PLAYER, out_signature='s')
    def PlaybackStatus(self):
        pass

    @dbus.service.method(ORG_MPRIS_MEDIAPLAYER2_PLAYER, out_signature='s')
    def LoopStatus(self):
        pass

    @dbus.service.method(ORG_MPRIS_MEDIAPLAYER2_PLAYER, out_signature='d')
    def Rate(self):
        pass

    @dbus.service.method(ORG_MPRIS_MEDIAPLAYER2_PLAYER, out_signature='a{sv}')
    def Metadata(self):
        pass

    @dbus.service.method(ORG_MPRIS_MEDIAPLAYER2_PLAYER, out_signature='d')
    def Volume(self):
        pass

    @dbus.service.method(ORG_MPRIS_MEDIAPLAYER2_PLAYER, out_signature='x')
    def Position(self):
        pass

    @dbus.service.method(ORG_MPRIS_MEDIAPLAYER2_PLAYER, out_signature='d')
    def MinimumRate(self):
        pass

    @dbus.service.method(ORG_MPRIS_MEDIAPLAYER2_PLAYER, out_signature='d')
    def MaximumRate(self):
        pass

    @dbus.service.method(ORG_MPRIS_MEDIAPLAYER2_PLAYER, out_signature='b')
    def CanGoNext(self):
        return True

    @dbus.service.method(ORG_MPRIS_MEDIAPLAYER2_PLAYER, out_signature='b')
    def CanGoPrevious(self):
        return True

    @dbus.service.method(ORG_MPRIS_MEDIAPLAYER2_PLAYER, out_signature='b')
    def CanPlay(self):
        return True

    @dbus.service.method(ORG_MPRIS_MEDIAPLAYER2_PLAYER, out_signature='b')
    def CanPause(self):
        return True

    @dbus.service.method(ORG_MPRIS_MEDIAPLAYER2_PLAYER, out_signature='b')
    def CanSeek(self):
        return False

    @dbus.service.method(ORG_MPRIS_MEDIAPLAYER2_PLAYER, out_signature='b')
    def CanControl(self):
        pass

    @dbus.service.method(ORG_MPRIS_MEDIAPLAYER2_PLAYER, out_signature='b')
    def Shuffle(self):
        return settings.get_option('playback/shuffle', False)

    @dbus.service.method(ORG_MPRIS_MEDIAPLAYER2_TRACKLIST, in_signature='ao', out_signature='aa{sv}')
    def GetTracksMetadata(self, track_ids):
        pass
        
    @dbus.service.method(ORG_MPRIS_MEDIAPLAYER2_TRACKLIST, in_signature='sob')
    def AddTrack(self, uri, after_track, set_as_current):
        pass

    @dbus.service.method(ORG_MPRIS_MEDIAPLAYER2_TRACKLIST, in_signature='o')
    def RemoveTrack(self, trackId):
        pass

    @dbus.service.method(ORG_MPRIS_MEDIAPLAYER2_TRACKLIST, in_signature='o')
    def Goto(self, trackId):
        pass

    @dbus.service.method(ORG_MPRIS_MEDIAPLAYER2_TRACKLIST, out_signature='ao')
    def Tracks(self):
        pass

    @dbus.service.method(ORG_MPRIS_MEDIAPLAYER2_TRACKLIST, out_signature='b')
    def CanEditTracks(self):
        return False

def get_metadata(track):
    ## mpris2.0 meta map, defined at http://xmms2.org/wiki/MPRIS_Metadata
    meta = {}
    meta['xesam:title'] = unicode(track.get_tag_raw('title'))
    meta['xesam:album'] = unicode(track.get_tag_raw('album'))
    meta['xesam:artist'] = unicode(track.get_tag_raw('artist'))

    meta['mpris:length'] = int(track.get_tag_raw('__length'))*1000
    cover_urls = cover_manager.find_covers(track)
    if len(cover_urls) > 0:
        meta['mpris:artUrl'] = unicode(cover_urls[0])
    meta['mpris:trackid'] = unicode(track.uri)

    return meta


