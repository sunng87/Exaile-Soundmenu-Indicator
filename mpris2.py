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
import hashlib
import logging
import time
import os

from xl import settings, event
from xl.covers import MANAGER as cover_manager

logger = logging.getLogger(__name__)

NANOSECOND = 1/0.000000001
MICROSECOND = 1/0.000001

ORG_MPRIS_MEDIAPLAYER2 = "org.mpris.MediaPlayer2"
ORG_MPRIS_MEDIAPLAYER2_PLAYER = "org.mpris.MediaPlayer2.Player"
ORG_MPRIS_MEDIAPLAYER2_TRACKLIST = "org.mpris.MediaPlayer2.TrackList"

MPRIS2_INTROSPECTION = \
"""<node name="/org/mpris/MediaPlayer2">
    <interface name="org.freedesktop.DBus.Introspectable">
        <method name="Introspect">
            <arg direction="out" name="xml_data" type="s"/>
        </method>
    </interface>
    <interface name="org.freedesktop.DBus.Properties">
        <method name="Get">
            <arg direction="in" name="interface_name" type="s"/>
            <arg direction="in" name="property_name" type="s"/>
            <arg direction="out" name="value" type="v"/>
        </method>
        <method name="GetAll">
            <arg direction="in" name="interface_name" type="s"/>
            <arg direction="out" name="properties" type="a{sv}"/>
        </method>
        <method name="Set">
            <arg direction="in" name="interface_name" type="s"/>
            <arg direction="in" name="property_name" type="s"/>
            <arg direction="in" name="value" type="v"/>
        </method>
        <signal name="PropertiesChanged">
            <arg name="interface_name" type="s"/>
            <arg name="changed_properties" type="a{sv}"/>
            <arg name="invalidated_properties" type="as"/>
        </signal>
    </interface>
    <interface name="org.mpris.MediaPlayer2">
        <method name="Raise"/>
        <method name="Quit"/>
        <annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="false"/>
        <property name="CanQuit" type="b" access="read"/>
        <property name="CanRaise" type="b" access="read"/>
        <property name="HasTrackList" type="b" access="read"/>
        <property name="Identity" type="s" access="read"/>
        <property name="DesktopEntry" type="s" access="read"/>
        <property name="SupportedUriSchemes" type="as" access="read"/>
        <property name="SupportedMimeTypes" type="as" access="read"/>
    </interface>
    <interface name="org.mpris.MediaPlayer2.Player">
        <method name="Next"/>
        <method name="Previous"/>
        <method name="Pause"/>
        <method name="PlayPause"/>
        <method name="Stop"/>
        <method name="Play"/>
        <method name="Seek">
            <arg direction="in" name="Offset" type="x"/>
        </method>
        <method name="SetPosition">
            <arg direction="in" name="TrackId" type="o"/>
            <arg direction="in" name="Position" type="x"/>
        </method>
        <method name="OpenUri">
            <arg direction="in" name="Uri" type="s"/>
        </method>
        <signal name="Seeked">
            <arg name="Position" type="x"/>
        </signal>
        <property name="PlaybackStatus" type="s" access="read">
            <annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="true"/>
        </property>
        <property name="LoopStatus" type="s" access="readwrite">
            <annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="true"/>
        </property>
        <property name="Rate" type="d" access="readwrite">
            <annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="true"/>
        </property>
        <property name="Shuffle" type="b" access="readwrite">
            <annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="true"/>
        </property>
        <property name="Metadata" type="a{sv}" access="read">
            <annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="true"/>
        </property>
        <property name="Volume" type="d" access="readwrite">
            <annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="false"/>
        </property>
        <property name="Position" type="x" access="read">
            <annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="false"/>
        </property>
        <property name="MinimumRate" type="d" access="read">
            <annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="true"/>
        </property>
        <property name="MaximumRate" type="d" access="read">
            <annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="true"/>
        </property>
        <property name="CanGoNext" type="b" access="read">
            <annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="true"/>
        </property>
        <property name="CanGoPrevious" type="b" access="read">
            <annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="true"/>
        </property>
        <property name="CanPlay" type="b" access="read">
            <annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="true"/>
        </property>
        <property name="CanPause" type="b" access="read">
            <annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="true"/>
        </property>
        <property name="CanSeek" type="b" access="read">
            <annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="true"/>
        </property>
        <property name="CanControl" type="b" access="read">
            <annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="false"/>
        </property>
    </interface>
</node>"""

class Mpris2Adapter(dbus.service.Object):
    """ interface defined by org.mpris.MediaPlayer2"""

    _properties = [
        # application
        "CanQuit",
        "CanRaise",
        "DesktopEntry",
        "HasTrackList",
        "Identity",
        "SupportedMimeTypes",
        "SupportedUriSchemes",
        # player
        "CanControl",
        "CanGoNext",
        "CanGoPrevious",
        "CanPause",
        "CanPlay",
        "CanSeek",
        "LoopStatus",
        "MaximumRate",
        "MinimumRate",
        "Metadata",
        "PlaybackStatus",
        "Position",
        "Rate",
        "Shuffle",
        "Volume",
    ]

    def __init__(self, exaile, bus):
#        super(Mpris2Adapter, self).__init__(self, bus, unicode('/org/mpris/MediaPlayer2'))
        dbus.service.Object.__init__(self, bus, '/org/mpris/MediaPlayer2')
        self.exaile = exaile

        self.cover_cache = {}

    ## Introspectable methods

    @dbus.service.method("org.freedesktop.DBus.Introspectable")
    def Introspect(self):
        return MPRIS2_INTROSPECTION

    ## Properties methods

    @dbus.service.method(dbus.PROPERTIES_IFACE, in_signature='ss', out_signature='v')
    def Get(self, interface, prop):
        if prop in self._properties:
            return getattr(self, prop)
        else:
            return None

    @dbus.service.method(dbus.PROPERTIES_IFACE, in_signature='s', out_signature='a{sv}')
    def GetAll(self, interface):
        res = {}
        for prop in self._properties:
            res[prop] = getattr(self, prop)
        return res

    @dbus.service.method(dbus.PROPERTIES_IFACE, in_signature='ssv')
    def Set(self, interface, prop, value):
        if prop in self._properties:
            setattr(self, prop, value)

    ## Properties signals

    @dbus.service.signal(dbus.PROPERTIES_IFACE, signature='sa{sv}as')
    def PropertiesChanged(self, interface, updated, invalid):
        pass

    def populate(self, interface, *prop_names):
        props = {}
        for p in prop_names:
            props[p] = getattr(self, p)
        self.PropertiesChanged(interface, props, [])

    ## main methods

    @dbus.service.method(ORG_MPRIS_MEDIAPLAYER2)
    def Quit(self):
        self.exaile.quit()

    @dbus.service.method(ORG_MPRIS_MEDIAPLAYER2)
    def Raise(self):
        self.exaile.gui.main.toggle_visible(True)

    ## main properties

    @property
    def CanQuit(self):
        return True

    @property
    def CanRaise(self):
        return True

    @property
    def HasTrackList(self):
        # TODO: implement TrackList
        return False

    @property
    def Identity(self):
        return "Exaile"

    @property
    def DesktopEntry(self):
        return "exaile"

    @property
    def SupportedUriSchemes(self):
        # TODO: return supported GFile schemes
        return ['file', 'http', 'https']

    @property
    def SupportedMimeTypes(self):
        # TODO: return supported GStreamer types
        return [
            'audio/mpeg',
            'audio/ogg',
            'audio/vorbis',
        ]

    ## Player methods

    @dbus.service.method(ORG_MPRIS_MEDIAPLAYER2_PLAYER)
    def Next(self):
        self.exaile.queue.next()

    @dbus.service.method(ORG_MPRIS_MEDIAPLAYER2_PLAYER, in_signature='s')
    def OpenUri(self, uri):
        self.exaile.gui.open_uri(uri)

    @dbus.service.method(ORG_MPRIS_MEDIAPLAYER2_PLAYER)
    def Pause(self):
        self.exaile.player.pause()

    @dbus.service.method(ORG_MPRIS_MEDIAPLAYER2_PLAYER)
    def Play(self):
        self.exaile.queue.play()

    @dbus.service.method(ORG_MPRIS_MEDIAPLAYER2_PLAYER)
    def PlayPause(self):
        if self.exaile.player.is_stopped():
            self.exaile.queue.play()
        else:
            self.exaile.player.toggle_pause()

    @dbus.service.method(ORG_MPRIS_MEDIAPLAYER2_PLAYER)
    def Previous(self):
        self.exaile.queue.prev()

    @dbus.service.method(ORG_MPRIS_MEDIAPLAYER2_PLAYER, in_signature='x')
    def Seek(self, offset):
        position = self.exaile.player.get_position() / NANOSECOND
        position += offset / MICROSECOND
        self.exaile.player.seek(position)

    @dbus.service.method(ORG_MPRIS_MEDIAPLAYER2_PLAYER, in_signature='ox')
    def SetPosition(self, track_id, position):
        if track_id == self._get_trackid(self.exaile.player.current):
            position /= MICROSECOND
            self.exaile.player.seek(position)
        else:
            # treat request as stale
            pass

    @dbus.service.method(ORG_MPRIS_MEDIAPLAYER2_PLAYER)
    def Stop(self):
        self.exaile.player.stop()

    ## Player properties

    @property
    def CanControl(self):
        return True

    @property
    def CanGoNext(self):
        track = self.exaile.player.current
        playlist = self.exaile.queue.current_playlist
        return not ((len(playlist)-1) == playlist.index(track))

    @property
    def CanGoPrevious(self):
        track = self.exaile.player.current
        playlist = self.exaile.queue.current_playlist
        return not (playlist.index(track) == 0)

    @property
    def CanPause(self):
        return self.exaile.player.is_playing()

    @property
    def CanPlay(self):
        return not self.exaile.player.is_playing()

    @property
    def CanSeek(self):
        return True

    @property
    def LoopStatus(self):
        playlist = self.exaile.queue.current_playlist
        if playlist.repeat_enabled:
            if playlist.repeat_mode == 'playlist':
                return 'Playlist'
            else:
                return 'Track'
        else:
            return 'None'

    @LoopStatus.setter
    def LoopStatus(self, value):
        playlist = self.exaile.queue.current_playlist
        if value == 'Playlist':
            playlist.set_repeat(True, mode='playlist')
            settings.set_option('playback/repeat', True)
            settings.set_option('playback/repeat_mode', 'playlist')
        elif value == 'Track':
            playlist.set_repeat(True, mode='track')
            settings.set_option('playback/repeat', True)
            settings.set_option('playback/repeat_mode', 'track')
        else:
            playlist.set_repeat(False)
            settings.set_option('playback/repeat', False)

    @property
    def MaximumRate(self):
        return 1.0

    @property
    def MinimumRate(self):
        return 1.0

    @property
    def PlaybackStatus(self):
        if self.exaile.player.is_playing():
            return 'Playing'
        elif self.exaile.player.is_paused():
            return 'Paused'
        else:
            return 'Stopped'

    @property
    def Position(self):
        return self.exaile.player.get_position() / NANOSECOND * MICROSECOND

    @property
    def Rate(self):
        return 1.0

    @Rate.setter
    def Rate(self, value):
        # Note: Ignore attempts to set.
        # TODO: Does Exaile support setting rate?
        pass

    @property
    def Metadata(self):
        current_track = self.exaile.player.current
        return self._get_metadata(current_track)

    @property
    def Shuffle(self):
        return settings.get_option('playback/shuffle', False)

    @Shuffle.setter
    def Shuffle(self, value):
        settings.set_option('playback/shuffle', bool(value))

    @property
    def Volume(self):
        # Range: 0.0 ~ 1.0
        return self.exaile.player.get_volume() / 100.0

    @Volume.setter
    def Volume(self, value):
        self.exaile.player.set_volume(value * 100.0)

    ## TrackList methods

    # TODO: implement according to:
    # http://specifications.freedesktop.org/mpris-spec/latest/TrackList_Node.html

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

    ## TrackList properties

    def CanEditTracks(self):
        return False

    ## Helper functions

    def _get_trackid(self, track):
        try:
            idx = self.exaile.queue.current_playlist.index(track)
            return "/org/exaile/Exaile/CurrentPlaylist/Track%d" % (idx+1)
        except ValueError:
            # TODO: find a better response than this
            #       (but on the other hand, this shouldn't happen anyway)
            return "/org/exaile/Exaile/NotInCurrentPlaylist"

    def _parse_trackid(self, trackid):
        if track.startswith("/org/exaile/Exaile/CurrentPlaylist/Track"):
            return int(track[40:])-1
        else:
            return None

    def _get_metadata(self, track):
        meta = {}

        if track is not None:
            ## MPRIS v2 meta map, defined at http://xmms2.org/wiki/MPRIS_Metadata

            meta['mpris:trackid'] = self._get_trackid(track)

            meta['xesam:url'] = track.get_tag_raw('__loc')

            title = track.get_tag_raw('title')
            if title:
                meta['xesam:title'] = title[0]

            artist = track.get_tag_raw('artist')
            if artist:
                meta['xesam:artist'] = dbus.types.Array(artist, signature='s')

            album = track.get_tag_raw('album')
            if album:
                meta['xesam:album'] = album[0]

            genre = track.get_tag_raw('genre')
            if genre:
                meta['xesam:genre'] = dbus.types.Array(genre, signature='s')

            meta['xesam:userRating'] = track.get_rating() / 5.0

            tracklen = track.get_tag_raw('__length')
            if tracklen:
                meta['mpris:length'] = dbus.types.Int64(tracklen * MICROSECOND)

            # this is a workaround, write data to a tmp file and return name
            cover_temp = self._get_cover_url(track)
            if cover_temp:
                meta['mpris:artUrl'] = cover_temp

        return dbus.types.Dictionary(meta, signature='sv', variant_level=1)

    def _get_cover_url(self, track):
        trackid = track.get_tag_raw('__loc')
        trackhash = hashlib.sha1(trackid).hexdigest()
        if trackid not in self.cover_cache:
            cover_data = cover_manager.get_cover(track)
            if cover_data is not None:
                tempdir = os.path.expanduser("~/.cache/exaile")
                tempfile = "%s/cover-%s" % (tempdir, trackhash)
                with open(tempfile, 'wb') as f:
                    f.write(cover_data)
                self.cover_cache[trackid] = "file://%s" % tempfile
            else:
                return None
        return self.cover_cache[trackid]
