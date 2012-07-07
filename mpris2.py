# vim: ts=4:sw=4:et:
#
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

from xl import event, settings, xdg
from xl.player import PLAYER, QUEUE
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
        logger.info("populate: %s" % repr(prop_names))
        props = {}
        for p in prop_names:
            if type(p) is tuple:
                # NOTE: This is a hack to fix the early-populate problem described
                #       in the comments of on_playback_start()
                p, v = p
                props[p] = v
            else:
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
        QUEUE.next()

    @dbus.service.method(ORG_MPRIS_MEDIAPLAYER2_PLAYER, in_signature='s')
    def OpenUri(self, uri):
        self.exaile.gui.open_uri(uri)

    @dbus.service.method(ORG_MPRIS_MEDIAPLAYER2_PLAYER)
    def Pause(self):
        PLAYER.pause()

    @dbus.service.method(ORG_MPRIS_MEDIAPLAYER2_PLAYER)
    def Play(self):
        QUEUE.play()

    @dbus.service.method(ORG_MPRIS_MEDIAPLAYER2_PLAYER)
    def PlayPause(self):
        if PLAYER.is_stopped():
            QUEUE.play()
        else:
            PLAYER.toggle_pause()

    @dbus.service.method(ORG_MPRIS_MEDIAPLAYER2_PLAYER)
    def Previous(self):
        QUEUE.prev()

    @dbus.service.method(ORG_MPRIS_MEDIAPLAYER2_PLAYER, in_signature='x')
    def Seek(self, offset):
        position = PLAYER.get_position() / NANOSECOND
        position += offset / MICROSECOND
        PLAYER.seek(position)

    @dbus.service.method(ORG_MPRIS_MEDIAPLAYER2_PLAYER, in_signature='ox')
    def SetPosition(self, track_id, position):
        if track_id == self._get_trackid(PLAYER.current):
            position /= MICROSECOND
            PLAYER.seek(position)
        else:
            # treat request as stale
            pass

    @dbus.service.method(ORG_MPRIS_MEDIAPLAYER2_PLAYER)
    def Stop(self):
        PLAYER.stop()

    ## Player properties

    @property
    def CanControl(self):
        return True

    @property
    def CanGoNext(self):
        if self.LoopStatus == 'None':
            track = PLAYER.current
            playlist = QUEUE.current_playlist
            try:
                return not ((len(playlist)-1) == playlist.index(track))
            except ValueError:
                return False
        else:
            return True

    @property
    def CanGoPrevious(self):
        if self.LoopStatus == 'None':
            track = PLAYER.current
            playlist = QUEUE.current_playlist
            try:
                return playlist.index(track) > 0
            except ValueError:
                return False
        else:
            return True

    @property
    def CanPause(self):
        # MPRIS -- return true even if currently paused
        return (PLAYER.current is not None)

    @property
    def CanPlay(self):
        # MPRIS -- return true even if currently playing
        return len(QUEUE.current_playlist) > 0

    @property
    def CanSeek(self):
        return True

    @property
    def LoopStatus(self):
        playlist = QUEUE.current_playlist
        if hasattr(playlist, "repeat_enabled"):
            # <= 0.3.2
            mode = playlist.repeat_mode
            enabled = playlist.repeat_enabled
            logger.debug("LoopStatus get: old, %r, %r" % (enabled, mode))
        else:
            # >= 0.3.3
            mode = playlist.repeat_mode
            enabled = (mode != 'disabled')
            logger.debug("LoopStatus get: new, %r, %r" % (enabled, mode))

        if enabled:
            if mode == 'playlist':
                # <= 0.3.2
                return 'Playlist'
            elif mode == 'all':
                # >= 0.3.3
                return 'Playlist'
            else:
                return 'Track'
        else:
            return 'None'

    @LoopStatus.setter
    def LoopStatus(self, value):
        playlist = QUEUE.current_playlist
        if hasattr(playlist, "set_repeat"):
            # <= 0.3.2
            if value == 'Playlist':
                enabled, mode = True, 'playlist'
            elif value == 'Track':
                enabled, mode = True, 'track'
            else:
                enabled, mode = False, 'none'
            logger.debug("LoopStatus set: old, %r, %r" % (enabled, mode))
            playlist.set_repeat(enabled, mode)
            settings.set_option('playback/repeat', enabled)
            if enabled:
                settings.set_option('playback/repeat_mode', mode)
        else:
            # >= 0.3.3
            if value == 'Playlist':
                mode = 'all'
            elif value == 'Track':
                mode = 'track'
            else:
                mode = 'disabled'
            logger.debug("LoopStatus set: new, %r" % mode)
            playlist.repeat_mode = mode

    @property
    def MaximumRate(self):
        return 1.0

    @property
    def MinimumRate(self):
        return 1.0

    @property
    def PlaybackStatus(self):
        if PLAYER.is_playing():
            return 'Playing'
        elif PLAYER.is_paused():
            return 'Paused'
        else:
            return 'Stopped'

    @property
    def Position(self):
        pos = PLAYER.get_position() / NANOSECOND * MICROSECOND
        return dbus.Int64(pos)

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
        current_track = PLAYER.current
        return self._get_metadata(current_track)

    @property
    def Shuffle(self):
        playlist = QUEUE.current_playlist
        if hasattr(playlist, 'shuffle_mode'):
            # >= 0.3.3
            mode = (playlist.shuffle_mode != 'disabled')
            logger.debug("Shuffle get: new, %r" % mode)
        else:
            # <= 0.3.2
            mode = settings.get_option('playback/shuffle', False)
            logger.debug("Shuffle get: old, %r" % mode)
        return mode

    @Shuffle.setter
    def Shuffle(self, value):
        playlist = QUEUE.current_playlist
        if hasattr(playlist, 'shuffle_mode'):
            # >= 0.3.3
            logger.debug("Shuffle set: new, %r" % value)
            if value:
                # TODO: This should toggle on/off like it did in 0.3.2, without
                #       resetting the mode to 'track' if it was 'album' previously.
                if self.Shuffle:
                    # Ensure the current mode is kept for 'on' -> 'on' changes.
                    return
                playlist.shuffle_mode = 'track'
            else:
                playlist.shuffle_mode = 'disabled'
        else:
            # <= 0.3.2
            logger.debug("Shuffle set: old, %r" % value)
            settings.set_option('playback/shuffle', bool(value))

    @property
    def Volume(self):
        # Range: 0.0 ~ 1.0
        return PLAYER.get_volume() / 100.0

    @Volume.setter
    def Volume(self, value):
        PLAYER.set_volume(value * 100.0)

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
            idx = QUEUE.current_playlist.index(track)
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

            meta['mpris:trackid'] = dbus.ObjectPath(self._get_trackid(track))

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
                tempfile = os.path.join(xdg.get_cache_dir(), "cover-%s" % trackhash)
                try:
                    with open(tempfile, 'wb') as f:
                        f.write(cover_data)
                except BaseException as ex:
                    logger.error("Unable to export cover: %r" % ex)
                    return None
                self.cover_cache[trackid] = "file://%s" % tempfile
            else:
                return None
        return self.cover_cache[trackid]
