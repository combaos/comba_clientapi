# -*- coding: utf-8 -*-
import sys
import simplejson
import urllib
"""
Die CombaClient Klasse stellt die Tasks zur Verfügung,
die dem Playlout Controller übertragen werden können  
Dies ist im Wesentlichen ein Wrapper
"""
class CombaClient():
    
    def __init__(self, sender):
        """
        Constructor
        @type    sender: object
        @param   sender: Der Communicator Adapter - z-B. zmq
        """
        self.sender = sender

    #------------------------------------------------------------------------------------------#
    def command(self, command):
        """
        Kommando an den Controller absetzen
        und Antwort entgegennehmen
        @type    command: string
        @param   command: Kommando
        @rtype:  string
        @return: Antwort des Controllers
        """
        self.sender.send(command)
        message = self.sender.receive()
        return message
    
    #------------------------------------------------------------------------------------------#
    def skip_channel(self, channel):
        """
        Skipt einen Kanal oder die Playlist
        @type    channel: string
        @param   channel: Kanal
        @rtype:  string
        @return: Antwort des Controllers
        """
        return self.command('channel_skip ' + channel) 

    #------------------------------------------------------------------------------------------#
    def channel_is_active(self, channel='playlist'):
        """
        Ist der Kanal aktiv?
        @type    channel: string
        @param   channel: Kanal
        @rtype:  boolean
        @return: True/False
        """
        state = self._get_channel_state(channel)
        is_active = True if state['selected'] == 'true' else False
        return is_active
                
    #------------------------------------------------------------------------------------------#
    def channel_on(self, channel):
        """
        Kanal einschalten
        @type    channel: string
        @param   channel: Kanal
        @rtype:  string
        @return: Antwort des Controllers
        """
        return self.command('channel_on ' + channel)    

    #------------------------------------------------------------------------------------------#
    def channel_off(self, channel):
        """
        Kanal ausschalten
        @type    channel: string
        @param   channel: Kanal
        @rtype:  string
        @return: Antwort des Controllers
        """
        return self.command('channel_off ' + channel)        

    #------------------------------------------------------------------------------------------#
    def get_channellist(self):
        """
        Channels als Liste ausgeben
        @rtype:  list
        @return: Antwort des Controllers
        """
        return simplejson.loads(self.command('listChannels'))               

    #------------------------------------------------------------------------------------------#
    def get_channelqueue(self, channel):
        """
        Channel Queue ausgeben
        @type    channel: string
        @param   channel: Kanal        
        @rtype:  dict
        @return: Antwort des Controllers
        """        
        return simplejson.loads(self.command('channel_queue ' + channel))

    #------------------------------------------------------------------------------------------#
    def get_channel_volume(self, channel='playlist'):
        """
        Lautstärke des Kanals ausgeben
        @type    channel: string
        @param   channel: Kanal        
        @rtype:  string/boolean
        @return: Volumen von 1-100/False
        """        
        state = self._get_channel_state(channel)
        channels = simplejson.loads(self.command('allData'))
        try: 
            volume = state['volume']                   
        except KeyError:
            return False
        else:
            return volume                                   
        return False

    #------------------------------------------------------------------------------------------#
    def channel_remove_track(self, channel, track_pos):        
        """
        Löscht einen Track aus dem secondary_queue
        @type    channel:   string
        @param   channel:   Kanal        
        @type    track_pos: string/int
        @param   track_pos: Position des zu entfernenden Eintrags
        @rtype:  string
        @return: Antwort des Controllers
        """        
        return self.command('channel_remove ' + channel + ' ' + str(track_pos))

    #------------------------------------------------------------------------------------------#
    def channel_seek(self, channel, duration):
        """
        Spult den laufenen Track des Kanals <duration> Sekunden weiter (falls möglich)
        Beispiel: channel_seek('ch1',60) - 60 Sekunden nach vorne
        @type    channel:   string
        @param   channel:   Kanal        
        @type    duration: string/int
        @param   duration: Dauer in Sekunden
        @rtype:  string
        @return: Antwort des Controllers
        """                        
        return self.command('channel_seek ' + channel + ' ' + str(duration))

    #------------------------------------------------------------------------------------------#
    def channel_track_up(self, channel, track_pos):        
        """
        Einen Track um eine Position nach oben schieben
        @type    channel:   string
        @param   channel:   Kanal        
        @type    track_pos: string
        @param   track_pos: Position des zu verschiebenden Eintrags
        @rtype:  string
        @return: Antwort des Controllers
        """                        
        return self.command('channel_move ' + channel + ' ' + str(track_pos) + ' ' + str(track_pos - 1))    

    #------------------------------------------------------------------------------------------#
    def channel_track_down(self, channel, track_pos):        
        """
        Einen Track um eine Position nach unten schieben
        @type    channel:   string
        @param   channel:   Kanal        
        @type    track_pos: string
        @param   track_pos: Position des zu verschiebenden Eintrags
        @rtype:  string
        @return: Antwort des Controllers
        """                                
        return self.command('channel_move ' + channel + ' ' + str(track_pos) + ' ' + str(track_pos + 1))        

    #------------------------------------------------------------------------------------------#
    def channel_track_insert(self, channel, uri):
        """
        Uri eines Audios in den (secondary) queue einfügen
        @type    channel: string
        @param   channel: Kanal        
        @type    uri:     string
        @param   uri:     uri, z.b. file:///my/audio/song.mp3
        @rtype:  string
        @return: Antwort des Controllers
        """            
        return self.command('channel_insert ' + channel + ' ' + urllib.quote(uri) + ' 0')

    #------------------------------------------------------------------------------------------#
    def channel_set_volume(self, channel, volume):
        """
        Lautstärke setzen (Prozentual von 1 - 100
        @type    channel: string
        @param   channel: Kanal        
        @type    volume: string/int
        @param   volume: Zahl von 1 bis 100
        @rtype:  string
        @return: Antwort des Controllers
        """        
        return self.command('channel_volume ' + channel + ' ' + str(volume))

    #------------------------------------------------------------------------------------------#
    def _get_channel_state(self, channel):
        """
        Private: Status eines Kanals abfragen
        Ausgabe Beispiel: {'ready':'true', 'selected:'false', 'single':'false','volume':'100%','remaining:'0.00'}
        @type    channel: string
        @param   channel: Kanal        
        @rtype:  dict/boolen
        @return: Antwort des Controllers/ False
        """                
        data = simplejson.loads(self.command('allData'))
        
        if not isinstance(data, dict):
            # es wurde kein assoz. Array/dict zurückgegeben
            return False
        
        if data['success'] != 'success':
            # die Abfrage war nicht erfolgreich 
            return False
        
        if not data.has_key('value'):
            # es wurden keine Werte geliefert
            return False

        channels = data['value']
        
        if not isinstance(channels, dict):
            # es wurde kein assoz. Array/dict zurückgegeben
            return False
                
        if channels.has_key(channel):
           chan = channels[channel]
           try:
               state = chan['state']
           except KeyError:
               return False
           else:
               return state
        else:
            return False

    #------------------------------------------------------------------------------------------#
    def playlist_load(self, uri):
        """
        Playlist im XSPF-Format laden
        @type    uri: string
        @param   uri: Uri einer Playlist - z.B. /my/playlists/2014-12-22-12-00.xspf        
        @rtype:  string
        @return: Antwort des Controllers
        """        
        return self.command('playlist_load ' + uri)

    #------------------------------------------------------------------------------------------#
    def playlist_data(self):
        """
        Gibt die aktuelle Playlist als dict zurück                
        @rtype:  dict
        @return: Antwort des Controllers
        """        
        return simplejson.loads(self.command('playlist_data'))
    
    #------------------------------------------------------------------------------------------#
    def playlist_flush(self):
        """
        Leert die Playlist                
        @rtype:  dict
        @return: Antwort des Controllers
        """                
        return self.command('playlist_flush')

    #------------------------------------------------------------------------------------------#
    def playlist_insert(self, uri, pos):
        """
        Audio in Playlist einfügen  
        @type    uri: string
        @param   uri: Uri einer Audiodatei - z.B. /my/audio/song.mp3                
        @rtype:  string
        @return: Antwort des Controllers
        """                
        return self.command('playlist_insert ' + uri + ' ' + pos)

    #------------------------------------------------------------------------------------------#
    def playlist_track_up(self, track_pos):        
        """
        Einen Track der Playlist um eine Position nach oben schieben
        @type    track_pos: string
        @param   track_pos: Position des zu verschiebenden Eintrags
        @rtype:  string
        @return: Antwort des Controllers
        """                                
        return self.command('playlist_move ' + str(track_pos) + ' ' + str(track_pos - 1))    

    #------------------------------------------------------------------------------------------#
    def playlist_track_down(self, track_pos):        
        """
        Einen Track der Playlist um eine Position nach unten schieben
        @type    track_pos: string
        @param   track_pos: Position des zu verschiebenden Eintrags
        @rtype:  string
        @return: Antwort des Controllers
        """                                     
        self.command('playlist_move ' + str(track_pos) + ' ' + str(track_pos + 1))        

    #------------------------------------------------------------------------------------------#
    def playlist_pause(self):
        """
        Playlist anhalten/stoppen
        @rtype:  string
        @return: Antwort des Controllers
        """              
        return self.command('playlist_pause')

    #------------------------------------------------------------------------------------------#
    def playlist_play(self):    
        """
        Playlist starten/abspielen
        @rtype:  string
        @return: Antwort des Controllers
        """              
        return self.command('playlist_play')

    #------------------------------------------------------------------------------------------#
    def playlist_remove_track(self, track_pos):
        """
        Löscht einen Track der Playlist
        Hinweis: Der laufende Track wird nicht berücksichtigt
        @type    track_pos: string/int
        @param   track_pos: Position des zu entfernenden Eintrags
        @rtype:  string
        @return: Antwort des Controllers
        """                
        return self.command('playlist_remove ' + str(track_pos))

    #------------------------------------------------------------------------------------------#
    def playlist_seek(self, duration):
        """
        Spult den laufenden Track der Playlist <duration> Sekunden weiter (falls möglich)
        Beispiel: playlist_seek('ch1',60) - 60 Sekunden nach vorne
        @type    duration: string/int
        @param   duration: Dauer in Sekunden
        @rtype:  string
        @return: Antwort des Controllers
        """                                
        return self.command('playlist_seek ' + str(duration))

    #------------------------------------------------------------------------------------------#
    def playlist_skip(self):     
        """
        Skipt den laufenden Track der Playlist
        @rtype:  string
        @return: Antwort des Controllers
        """        
        return self.command('playlist_skip')

    #------------------------------------------------------------------------------------------#
    def recorder_start(self):
        """
        Recorder starten
        @rtype:  string
        @return: Antwort des Controllers
        """                 
        return self.command('recorder_start')        

    #------------------------------------------------------------------------------------------#
    def recorder_stop(self):
        """
        Recorder stoppen
        @rtype:  string
        @return: Antwort des Controllers
        """                         
        return self.command('recorder_stop')
    
    def recorder_data(self):
        """
        Daten der aktuellen Aufnahme abrufen
        Beispiel: {'file':'/my/audio/2014-12-22-12-00.wav', 'recorded': '25'} - Die Aufnahme der Datei /my/audio/2014-12-22-12-00.wav ist bei 25%  
        @rtype:  dict
        @return: Antwort des Controllers
        """     
        return simplejson.loads(self.command('recorder_data'))           
