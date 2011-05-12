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

import logging
import time
import tempfile
import os

from xl import settings, event
from xl.covers import MANAGER as cover_manager

logger = logging.getLogger(__name__)
ORG_MPRIS_MEDIAPLAYER2="org.mpris.MediaPlayer2"
ORG_MPRIS_MEDIAPLAYER2_PLAYER="org.mpris.MediaPlayer2.Player"
ORG_MPRIS_MEDIAPLAYER2_TRACKLIST="org.mpris.MediaPlayer2.TrackList"
ORG_MPRIS_MEDIAPLAYER2_PLAYLISTS="org.mpris.MediaPlayer2.Playlists"
class Mpris2Adapter(dbus.service.Object):
    """ interface defined by org.mpris.MediaPlayer2"""
    def __init__(self, exaile, bus):
#        super(Mpris2Adapter, self).__init__(self, bus, unicode('/org/mpris/MediaPlayer2'))
        dbus.service.Object.__init__(self, bus, '/org/mpris/MediaPlayer2')
        self.exaile = exaile

        self.cover_cache = {}

    def populate(self, interface, *prop_names):
        props = {}
        for p in prop_names:
            props[p] = getattr(self, p)()
        self.PropertiesChanged(interface, props, [])

    @dbus.service.method(dbus.PROPERTIES_IFACE, in_signature='ss', out_signature='v')
    def Get(self, interface, prop):
        logger.debug('dbus get prop: ' + prop)
        if hasattr(self, prop):
            result = getattr(self, prop)()
            return result
        return None

#    @dbus.service.method(dbus.PROPERTIES_IFACE, in_signature='s', out_signature='a{sv}')
#    def GetAll(self, interface):
#        logger.debug('dbus get all props')
        ## TODO
#        return dbus.types.Dictionary({})

    @dbus.service.signal(dbus.PROPERTIES_IFACE, signature='sa{sv}as')
    def PropertiesChanged(self, interface, updated, invalid):
        #logger.info("fired")
        pass

    @dbus.service.method(ORG_MPRIS_MEDIAPLAYER2)
    def Raise(self):
        self.exaile.gui.main.toggle_visible(True)

    @dbus.service.method(ORG_MPRIS_MEDIAPLAYER2)
    def Quit(self):
        self.exaile.quit()

    def CanQuit(self):
        return True

    def CanRaise(self):
        return True

    def HasTrackList(self):
        return False

    def Identity(self):
        return "Exaile"
    
    def DesktopEntry(self):
        return "exaile"

    def SupportedUriSchemes(self):
        ##TODO
        return ['http', 'https', 'file']

    def SupportedMimeTypes(self):
        ##TODO
        return ['audio/mpeg', 'application/ogg']

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
        if self.exaile.player.is_stopped():
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
        self.exaile.player.seek(offset)

    @dbus.service.method(ORG_MPRIS_MEDIAPLAYER2_PLAYER, in_signature='ox')
    def SetPosition(self, track_id, position):
        pass

    @dbus.service.method(ORG_MPRIS_MEDIAPLAYER2_PLAYER, in_signature='s')
    def OpenUri(self, uri):
        pass

    def PlaybackStatus(self):
        if self.exaile.player.is_playing():
            return 'Playing'
        elif self.exaile.player.is_paused():
            return 'Paused'
        else:
            return 'Stopped'

    def LoopStatus(self):
        playlist = self.exaile.queue.current_playlist
        if playlist.repeat_enabled:
            if playlist.repeat_mode == 'playlist':
                return 'Playlist'
            else:
                return 'Track'
        else:
            return 'None'
        

    def Rate(self):
        pass

    def Metadata(self):
        current_track = self.exaile.player.current
        if current_track is not None:
            return self._get_metadata(current_track)
        else:
            return {}

    def Volume(self):
        pass

    def Position(self):
        pass

    def MinimumRate(self):
        pass

    def MaximumRate(self):
        pass

    def CanGoNext(self):
        track = self.exaile.player.current
        playlist = self.exaile.queue.current_playlist
        return not ((len(playlist)-1) == playlist.index(track))

    def CanGoPrevious(self):
        track = self.exaile.player.current
        playlist = self.exaile.queue.current_playlist
        return not (playlist.index(track) == 0)

    def CanPlay(self):
        return not self.exaile.player.is_playing()

    def CanPause(self):
        return self.exaile.player.is_playing()

    def CanSeek(self):
        return False

    def CanControl(self):
        return True

    def Shuffle(self):
        return settings.get_option('playback/shuffle', False)

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

    def CanEditTracks(self):
        return False

    @dbus.service.method(ORG_MPRIS_MEDIAPLAYER2_PLAYLISTS, in_signature='o')
    def ActivatePlaylist(self, playlist_id):
        playlists = self.exaile.smart_playlists.list_playlists()
        selected_index = int(playlist_id[playlist_id.rindex('/')+1:])
        selected_playlist_name = playlists[selected_index]
        selected_playlist = self.exaile.smart_playlists.get_playlist(selected_playlist_name)
        selected_playlist = selected_playlist.get_playlist(collection=self.exaile.collection)
        self.exaile.gui.main.add_playlist(selected_playlist)
        self.exaile.gui.main.queue.set_current_playlist(selected_playlist)
        self.exaile.player.stop()
        self.exaile.gui.main.queue.play()

    @dbus.service.method(ORG_MPRIS_MEDIAPLAYER2_PLAYLISTS, in_signature='uusb', out_signature='a(oss)')
    def GetPlaylists(self, index, maxcount, order, reverse_order):
        playlists = self.exaile.smart_playlists.list_playlists()
        dbus_playlist = []
        for index,name in enumerate(playlists):
            playlist_tuple=[dbus.types.ObjectPath('/org/exaile/playlists/%d' % index), name, ""]
            playlist_struct = dbus.types.Struct(playlist_tuple, signature="(oss)")
            dbus_playlist.append(playlist_struct)
        array = dbus.types.Array(dbus_playlist, signature="(oss)")
        return array

    def PlaylistCount(self):
        return len(self.exaile.smart_playlists.list_playlists())

    def Orderings(self):
        return "User"

    def ActivePlaylist(self):
        playlist = self.exaile.gui.main.get_selected_playlist().playlist
        valid = True
        playlist_id = dbus.types.ObjectPath("/org/exaile/%s" % "current") ## name is not id in exaile
        display_name = playlist.name
        dbus_playlist = dbus.types.Struct([playlist_id, display_name, ""], signature="(oss)")
        dbus_active_playlist = dbus.types.Struct([valid, dbus_playlist], signature="(b(oss))")
        return dbus_active_playlist

    def _get_metadata(self, track):
        ## mpris2.0 meta map, defined at http://xmms2.org/wiki/MPRIS_Metadata
        meta = {}

        title = track.get_tag_raw('title')[0] if track.get_tag_raw('title') else ""
        meta['xesam:title'] = unicode(title)  
        album = track.get_tag_raw('album')[0] if track.get_tag_raw('album') else ""
        meta['xesam:album'] = unicode(album)
        artist = track.get_tag_raw('artist')[0] if track.get_tag_raw('artist') else ""
        meta['xesam:artist'] = dbus.types.Array([unicode(artist)], signature='s')
    
        meta['mpris:length'] = dbus.types.Int64(int(track.get_tag_raw('__length') or 0)*1000)

        ## this is a workaround, write data to a tmp file and return name
        cover_temp = self._get_cover_url(track)
        if cover_temp is not None:
            meta['mpris:artUrl'] = cover_temp

        meta['mpris:trackid'] = track.get_tag_raw('__loc')
        meta['xesam:url'] = track.get_tag_raw('__loc')
    
        return dbus.types.Dictionary(meta, signature='sv', variant_level=1)

    def _get_cover_url(self, track):
        trackid = track.get_tag_raw('__loc')
        if trackid not in self.cover_cache:
            cover_data = cover_manager.get_cover(track)
            if cover_data is not None:
                dir = os.path.expanduser('~/.cache/exaile')
                cover_temp = tempfile.NamedTemporaryFile(prefix='exaile-soundmenu', dir=dir, delete=False)
                cover_temp.write(cover_data)
                cover_temp.close()
                self.cover_cache[trackid] = "file://"+cover_temp.name
            else:
                return None
        return self.cover_cache[trackid]


