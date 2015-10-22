#!/usr/bin/python
# -*- coding: utf-8 -*-
import locale, dialog
import sys, os, os.path

import socket
import zmq
import StringIO
import time
import ConfigParser
import logging
import simplejson
import urllib

"""
Ein Beispiel für einen (ziemlich umständlich bedienbaren) Client auf der Kommandozeile
Verwendung findet die CombaClient-Klasse mit dem zmq-Adapter

Als Implementierungsbeispiele sind die Funktionen des Models und 
diejenigen Funktionen des Controllers, die auf die "show_"-Tasks folgen 

Erstere besorgen sich Daten vom Controller und verarbeiten sie.
Zweitere setzen meist schlichte Kommandos ab
"""

package_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),'..'))

sys.path.insert(0, package_dir)
from python.combaclient import CombaClient
# This is almost always a good thing to do at the beginning of your programs.
locale.setlocale(locale.LC_ALL, '')
HOST, PORT = "localhost", 9999



class View:
    """
    Die Views, mit Python Dialog umgesetzt
    """
    def __init__(self, Dialog_instance):
        """
        Init
        @type Dialog_instance:  object
        @param Dialog_instance: Die Instanz der Dialog Klasse         
        """
        self.dlg = Dialog_instance
        
    def channel_queue(self, data): 
        """
        Zeigt die Tracks eines Channels an
        @type data: dict
        @param data: Infos vom Controller
        """
        track_items = data['track_items'];
        track_name = ''
        if len(track_items):
            (code, tag) = self.dlg.menu(
            "Tracks",
            width=65,
            choices=track_items)
            if code in (self.dlg.DIALOG_CANCEL, self.dlg.DIALOG_ESC):
                track_name = ''
            else:
                track_num = int(tag) 
    
                if track_num > 0 and len(track_items) >= (track_num - 1) :
                    track_name = track_items[track_num - 1][1]
        else:        
            self.dlg.infobox("Keine Tracks geladen")
            code = self.dlg.DIALOG_CANCEL
            tag = ""
            time.sleep(2)
        
        return (code, tag, track_name)     


    def list_channels(self, data):
        """
        Zeigt die Liste der Channels an,
        informiert ob sie aktiv sind
        @type data: dict
        @param data: Infos vom Controller
        @rtype: list
        @return: (code, tag) - Fehlercode und Rückgabewert 
        """
        channel_items = data['channel_items']
        (code, tag) = self.dlg.menu(
                                    "Wähle einen Kanal",
                                    width=65,
                                    choices=channel_items)
             
        return (code, tag)
    
    def change_volume(self, data):
        """
        Zeigt die ausgefuchste Lautstärke-Regelung dieses Programms        
        @type data: dict
        @param data: Infos vom Controller
        @rtype: list
        @return: (code, tag) - Fehlercode und Rückgabewert        
        """        
        channel = data['channel']
        volume = data['volume']
        buttons = []
    
        for i in range(0, 120, 20):
            active = 1 if volume == str(i) else 0
            buttons.append((str(i), "%", active))
    
        (code, tag) = self.dlg.radiolist(
                                         "Lautstärke von Kanal " + channel,
                                         width=65,
                                         choices=buttons)
        return (code, tag)            
    
         
    def channel_actions(self, data):
        """
        Zeigt die Funktionen, die auf einem Channel ausgeführt werden
        Siehe choices         
        @type data: dict
        @param data: Infos vom Controller
        @rtype: list
        @return: (code, tag) - Fehlercode und Rückgabewert
        """        
        channel = data['channel']
        channel_active = data['channel_active']
        
        chann_act = ("1", "Aus") if channel_active else ("1", "Ein")  
        (code, tag) = self.dlg.menu(
                                    "Kanal " + channel,
                                    width=65,
                                    choices=[chann_act,
                                             ("2", "Tracks anzeigen"),
                                             ("3", "Audio laden"),
                                             ("4", "Laufenden Track Abbrechen"),
                                             ("5", "Lautstärke"),
                                             ("6", "Seek"),
                                             ])
        
        return (code, tag)

    
    def channel_seek(self, data):
        """
        Zeigt die Seek-Funktion
        @type data: dict
        @param data: Infos vom Controller
        @rtype: list
        @return: (code, tag) - Fehlercode und Rückgabewert
        """        
        channel = data['channel']        
        buttons = []
    
        for i in range(10, 120, 20):
            active = 10
            buttons.append((str(i), "%", active))
    
        (code, tag) = self.dlg.radiolist(
                                         "Vorspulen auf Kanal " + channel,
                                         width=65,
                                         choices=buttons)

        return (code, tag)            
                

    def track_actions(self, data):
        """
        Zeigt die Aktionen, die mit einem Track ausgeführt werden
        Siehe choices
        @type data: dict
        @param data: Infos vom Controller
        @rtype: list
        @return: (code, tag) - Fehlercode und Rückgabewert
        """        
        channel = data['channel']
        track_name = data['track_name']
        (code, tag) = self.dlg.menu(
                                        "Kanal " + channel + ' - ' + track_name,
                                        width=65,
                                        choices=[("1", "Track löschen"),
                                                 ("2", "Nach oben"),
                                                 ("3", "Nach unten"),
                                                 ("4", "Metadaten anzeigen")
                                                 ])
        
        return (code, tag)            

        
    def open_file(self, data):
        """
        Datei öffnen Dialog        
        @type data: dict
        @param data: Infos vom Controller
        @rtype: string
        @return: gewählter Dateipfad
        """        
        dir = data['dir']
        (code, path) = self.dlg.fselect(dir, 10, 50, title="Open Audio File")
     
        return str(path).strip()

    def metadata(self,data):
        """
        Metadaten eines Tracks ausgeben
        @type data: dict
        @param data: Infos vom Controller
        @rtype: list
        @return: (code, '') - Fehlercode
        """                
        metadata = data['metadata']
        message = 'Daten'
        for key in metadata:
             message = message + '\n' + key + ': '+ metadata[key]
        (code) = self.dlg.msgbox(message, height=50, width=80)
        return (code, '')      
        
    def playlist(self, data): 
        """
        Tracks der Playlist anzeigen
        @type data: dict
        @param data: Infos vom Controller
        @rtype: list
        @return: (code, tag, trackname) - Fehlercode, Rückgabewert des Dialogs und Name des gewählten Tracks
        """                        
        track_items = data['playlist_items'];
        track_name = ''
        if len(track_items):
            (code, tag) = self.dlg.menu(
            "Playlist",
            width=65,
            choices=track_items)
            if code in (self.dlg.DIALOG_CANCEL, self.dlg.DIALOG_ESC):
                track_name = ''
            else:
                track_num = int(tag) 
    
                if track_num > 0 and len(track_items) >= (track_num - 1) :
                    track_name = track_items[track_num - 1][1]
        else:        
            self.dlg.infobox("Keine Tracks geladen")
            code = self.dlg.DIALOG_CANCEL
            tag = ""
            time.sleep(2)
        
        return (code, tag, track_name)     
        
    def main_menu(self, data):
        """
        Hauptmenü
        @type data: dict
        @param data: Infos vom Controller
        @rtype: list
        @return: (code, tag) - Fehlercode und Rückgabewert
        """            
        playlist_active = data['playlist_active']        
        playlist_act = ("Playlist stoppen", "Playlist anhalten") if playlist_active else ("Playlist spielen", "Playlist abspielen") 
        (code, tag) = self.dlg.menu(
                                        "Hauptmenü",
                                        width=120,
                                        choices=[("Kanäle", "Wähle einen Kanal"),
                                                 ("Playlist laden", "Lade eine Playlist vom lokalen Laufwerk"),
                                                 playlist_act,
                                                 ("Playlist anzeigen", "Playlist anzeigen")])

            
        return (code, tag)           


class Model:
    """
    Hier kann man lernen, wie man die Daten verarbeiten kann die vom Controller erhältlich sind    
    """
    def __init__(self, CombaClient_instance):
        """
        Constructor
        @type CombaClient_instance:  object
        @param CombaClient_instance: Die Instanz der ControllerClient Klasse         
        """
        self.client = CombaClient_instance
        self.data = {}        
    
    def set(self, key, value):
        """
        Einfache set-Methode für die vom Model gesetzen Daten
        @type key: string
        @param key: der Key
        @type value: mixed
        @param value: der zu setzende Wert   
        """
        self.data[key] = value
        
    def get(self, key):
        """
        Einfache get-Methode für die vom Model gesetzen Daten
        @type key: string
        @param key: der Key
        @rtype: mixed
        @return: der Rückgabewert   
        """        
        return self.data[key]        
    
    def get_channel_volume(self):
        """
        Lautstärke eines Kanals ermitteln
        @rtype: string
        @return: Lautstärke in Prozent
        """
        # Der Kanal auf dem wir uns gerade bewegen
        channel = self.get('channel')
        # Lautstärke des Kanals vom Controller ermitteln
        volume = self.client.get_channel_volume(channel)
        # Bei der Rückgabe Prozentzeichen entfernen        
        return volume.replace('%','')        

    def get_track_items(self):
        """
        Tracks eines Kanals holen
        @rtype: list
        @return: Liste der Tracks
        """
        # Der Kanal auf dem wir uns gerade bewegen
        channel = self.get('channel')        
        # Channel-Queue vom Controller
        data = self.client.get_channelqueue(channel)
        queue = self._get_data(data)
        # Die Tracks befinden sich in "tracks"
        tracks = queue['tracks']
        track_items = [];
        # Es werden aber nur die Titel und der Index benötigt
        for index, track in  enumerate(tracks):
            # append num,title pair to list. E.g: (1, 'My Song')
            track_items.append((str(index + 1), track['title']))
        
        # Daten im Model festhalten
        self.set('track_items', track_items)     
        return track_items 
   
    def get_track_item(self, num):
        """
        Einen Track aus der track-Liste holen
        @type num: string
        @param num: die Nummer des gesuchten Tracks (als String)   
        @rtype: string
        @return: Name des Tracks
        """
        # Tracks aus den Model-Daten
        track_items = self.get('track_items')            
        track_num = int(num) 
        track_name = ''
        # Gültigkeit prüfen
        if track_num > 0 and len(track_items) >= (track_num - 1) :
            # Den Tracknamen aus der Liste extrahieren
            track_name = track_items[track_num - 1][1]    

        return track_name

    def get_track_item_metadata(self):
        """
        Die Metadaten eines Tracks holen
        @rtype: dict
        @return: Metadaten des Tracks
        """        
        # Der Kanal auf dem wir uns gerade bewegen
        channel = self.get('channel')
        # Die Position auf dem Channel, der Track
        channel_pos = self.get('channel_pos')
        # Channel-Queue holen
        data = self.client.get_channelqueue(channel)
        queue = self._get_data(data)    
        track_items = queue['tracks']
            
        if channel_pos > -1:
            # Die Metadaten des gesuchten Tracks
            metadata = track_items[channel_pos]    
            
        return metadata        
    
    def get_channels(self):
        """
        Die Channels holen und Information darüber, ob sie aktiv/eingeschalten sind  
        @rtype: dict
        @return: Channels und Stati
        """                
        # LIste der Kanäle holen
        data = self.client.get_channellist()
        channels = self._get_data(data)
        # Infos in channel_items einlesen             
        channel_items = []
        for item in channels:
            # Status an oder aus gibts im channel queue
            data = self.client.get_channelqueue(item)
            queue = self._get_data(data)
            # Wenn ['state']['selected'] true ist, dann ist an
            status = ('on' if queue['state']['selected'] == 'true' else 'off')
            channel_items.append((item, status))

        return channel_items 
    
    def get_playlist_items(self):
        """
        Tracks der Playlist holen
        @see get_track_items
        @rtype: list
        @return: Liste der Tracks
        """
        data = self.client.playlist_data()
        tracks = self._get_data(data)
        
        track_items = [];
        for index, track in  enumerate(tracks):
            # append num,title pair to list. E.g: (1, 'My Song')
            track_items.append((str(index + 1), track['title']))
        
        self.set('track_items', track_items)     
        return track_items
    
    def get_playlist_item_metadata(self):
        """
        Die Metadaten eines Tracks der Playlistholen
        @see get_track_item_metadata
        @rtype: dict
        @return: Metadaten des Tracks
        """                
        channel_pos = self.get('channel_pos')
        data = self.client.playlist_data()
        tracks = self._get_data(data)        
        track = tracks[channel_pos]    
        return track                   
   
    def get_playlist(self):
        """
        Alle Metadaten  der Playlist holen
        @rtype: dict
        @return: Metadaten des Tracks
        """            
        # Daten vom Controller holen
        data = self.client.playlist_data()
        return self._get_data(data)    
    
        
    def _get_data(self, result):
        """
        Fehlerbehandlung
        Der Controller gibt Auskunft über den Erfolg eines Kommandos:
        {"code": "0100", "success": "success", "section": "main", "value": => das ist der Wert, den wir haben möchten        
        @type     result: dict
        @param    result: Ein dict objekt
        """        
        try:
            if result['success'] == 'success':
                if result.has_key('value'):
                    return  result['value']
                else:
                    return True
            else:
                return False
        except:
            return False                

"""
Der (Client-)Controller wird so gestartet:
 adapter = ClientZMQAdapter('localhost', 9099)
 controller = Controller(CombaClient(adapter))         
 controller.run()
controller.run führt immer den jeweilig aktuellen self.task aus, zu Beginn self.show_mainmenu()

Ein show-Task holt ggf. daten vom Model und ruft ein view auf:
 data=self.model.<model func>()
 response = self.view.<view func>(data)
 self.handle(response)

self.handle(code, tag) verarbeitet die Rückgabe des Views, 
wobei 
* code ein Fehlercode der Python-Dialog ist (z.B. self.dlg.DIALOG_OK)
* tag der Rückgabe-Wert für eine Usereingabe ist
Durch viele unübersichtliche ifs elife und else wird festgestellt, welches Kommando ggf. ausgeführt
und welches View als nächstes angezeigt wird...
... gelegentlich wird noch notiert, auf welchem Kanal, auf welchem Track der User gerade agiert
... und dann geht das Ganze von vorn los

Das ist so natürlich nicht zur Nachahmung empfohlen ;-)  
"""        

class Controller:    
    
    def __init__(self, CombaClient_instance):
        """
        Constructor
        @type CombaClient_instance:  object
        @param CombaClient_instance: Die Instanz der ControllerClient Klasse
        """
        # Die Instanz der CombaClient Klasse, die Kommandos an den CombaController bereitstellt
        self.client = CombaClient_instance
        # Python Dialog
        self.dlg = dialog.Dialog(dialog="dialog")
        self.dlg.add_persistent_args(["--backtitle", "Comba Client"])
        self.dlg.add_persistent_args(["--cancel-label", "Zurück"])
        # Unser Model braucht ebenfalls die Instanz von CombaClient
        self.model = Model(self.client)
        # DIe Views
        self.view = View(self.dlg)
        # Am Anfang immer das Hauptmenü anzeigen
        self.task = 'show_mainmenu'
        # Einige Variablen initiieren
        self.channel = ''
        self.channel_pos = 0
        self.channel_active = False

    
    def handle(self, params):
        """
        Anfragen entgegennehmen und ausführen
        Diese Funktion ist nicht ausführlich kommentiert,
        da sie ohnehin nicht zur Nachahmung empfohlen wird
        @type params: list
        @param: params: Liste, die code und tag enthält   
        @rtype: string
        @return: Name der auszuführenden Controller-Funktion 
        """
        code = params[0]
        tag = params[1]        
        
        if self.task == 'show_mainmenu':
            if code in (self.dlg.DIALOG_CANCEL, self.dlg.DIALOG_ESC):
               msg = "Möchstest du das Programm abbrechen?"
               # "No" or "ESC" will bring the user back to the demo.
               # DIALOG_ERROR is propagated as an exception and caught in main().
               # So we only need to handle OK here.
               if self.dlg.yesno(msg) == self.dlg.DIALOG_OK:
                   sys.exit(0)
                   return 0
            elif tag == "Kanäle":
                self.task = 'show_channels'
            elif tag == 'Playlist laden':
                self.cmd_load_playlist()
                self.task = 'show_mainmenu'
            elif tag == 'Playlist spielen':
                self.cmd_play_playlist()
                self.task = 'show_mainmenu'    
            elif tag == 'Playlist stoppen':
                self.cmd_stop_playlist()
                self.task = 'show_mainmenu'                
            elif tag == 'Playlist anzeigen':
                self.channel = 'playlist'
                self.task = 'show_playlist'
        elif self.task == "show_playlist":
            if code in (self.dlg.DIALOG_CANCEL, self.dlg.DIALOG_ESC):
                self.task = 'show_mainmenu'
            else:
                self.channel_pos = int(tag) - 1
                self.task = 'show_playlist_actions'      
        elif self.task == 'show_playlist_actions': 
            if code in (self.dlg.DIALOG_CANCEL, self.dlg.DIALOG_ESC):
                self.task = 'show_mainmenu'                        
            else:
                if tag == "1":
                    self.cmd_channel_removetrack()
                    self.task = 'show_playlist' 
                elif tag == "2":
                    self.cmd_track_up()
                    self.task = 'show_playlist'
                elif tag == "3":
                    self.cmd_track_down()                
                    self.task = 'show_playlist'    
                elif tag == "4":
                    self.show_metadata()                                     
                    self.task = 'show_playlist'                                  
        elif self.task == "show_channels":
            if code in (self.dlg.DIALOG_CANCEL, self.dlg.DIALOG_ESC):
                self.task = 'show_mainmenu'
            else:
                self.channel = tag
                self.task = 'show_channel_actions'       
        elif self.task == "show_channelqueue":
            if code in (self.dlg.DIALOG_CANCEL, self.dlg.DIALOG_ESC):
                self.task = 'show_channel_actions'
            else:
                self.channel_pos = int(tag) - 1
                self.task = 'show_track_actions' 
        elif self.task == 'show_track_actions': 
            if code in (self.dlg.DIALOG_CANCEL, self.dlg.DIALOG_ESC):
                self.task = 'show_channelqueue'                        
            else:
                if tag == "1":
                    self.cmd_channel_removetrack()
                    self.task = 'show_channelqueue' 
                elif tag == "2":
                    self.cmd_track_up()
                    self.task = 'show_channelqueue'
                elif tag == "3":
                    self.cmd_track_down()                
                    self.task = 'show_channelqueue'    
                elif tag == "4":
                    self.show_metadata()                                     
                    self.task = 'show_channelqueue'                    
        elif self.task == 'show_change_volume': 
            if code in (self.dlg.DIALOG_CANCEL, self.dlg.DIALOG_ESC):
                self.task = 'show_channel_actions'                            
            else:            
                self.cmd_channel_set_volume(tag)                     
                self.task = 'show_change_volume'                                  
        elif self.task == 'show_seek_channel': 
            if code in (self.dlg.DIALOG_CANCEL, self.dlg.DIALOG_ESC):
                self.task = 'show_channel_actions'                            
            else:            
                self.cmd_channel_seek_track(tag)                     
                self.task = 'show_seek_channel'                
        elif self.task == 'show_channel_actions': 
            if code in (self.dlg.DIALOG_CANCEL, self.dlg.DIALOG_ESC):
                self.task = 'show_channels'                            
            else:
                
                self.channel_active = self.client.channel_is_active(self.channel)
                self.channel_volume = self.client.get_channel_volume(self.channel).replace('%', '')
                if tag == "1":                    
                    self.cmd_switch_channel()                    
                    self.task = 'show_channels'              
                elif tag == "2":                
                    self.task = 'show_channelqueue'
                elif tag == "3":                
                    self.cmd_channel_insert()                
                    self.task = 'show_channelqueue'        
                elif tag == "4":                
                    self.cmd_skip_channeltrack()
                    self.task = 'show_channel_actions'     
                elif tag == "5":                                
                    self.task = 'show_change_volume'                
                elif tag == "6":                                
                    self.task = 'show_seek_channel'                    
                
        return self.task  
        
        
        
    def run(self):
        """
        Loop bis der User das Programm beendet
        """
        while 1:            
            self.execute(self.task)
                    
    def execute(self, task):
        """
        Einen Task ausführen
        @type task:  string 
        @param task: Name der auszuführenden Controller-Funktion 
        """        
        exec"a=self." + task + '()'
        
    def show_mainmenu(self):    
        """
        Hauptmenü anzeigen
        """
        data = {}
        data['playlist_active'] = self.client.channel_is_active('playlist')
        response = self.view.main_menu(data)
        self.handle(response)
        
    def show_playlist(self):
        """
        Playlist anzeigen
        """        
        data = {}        
        data['channel'] = self.channel
        data['playlist_items'] = self.model.get_playlist_items()
        response = self.view.playlist(data)
        self.handle(response)
    
    def show_playlist_actions(self):
        """
        Playlist-Menü anzeigen
        """                            
        data = {}
        data['track_name']  = self.model.get_track_item(self.channel_pos)                
        data['channel'] = 'playlist'
        response = self.view.track_actions(data)
        self.handle(response) 
                
    def show_channels(self):
        """
        Channel-Übersichts-Menü anzeigen
        """                  
        data = {}
        data['channel_items'] = self.model.get_channels()
        response = self.view.list_channels(data)
        self.handle(response)
        
    def show_channel_actions(self):
        """
        Channel-Menü anzeigen
        """                        
        data = {}
        data['channel'] = self.channel
        data['channel_active'] = self.client.channel_is_active(self.channel)
        response = self.view.channel_actions(data)
        self.handle(response)        
    
    def show_channelqueue(self):
        """
        Track-Übersichts-Menü innerhalb eines Kanals anzeigen
        """                                
        data = {}
        self.model.set('channel', self.channel)
        data['channel'] = self.channel
        data['track_items'] = self.model.get_track_items()
        response = self.view.channel_queue(data)
        self.handle(response)
    
    def show_seek_channel(self):              
        """
        Die Seek-Funktion anzeigen
        """                                
        data = {}                
        data['channel'] = self.channel
        response = self.view.channel_seek(data)
        self.handle(response)

    def show_track_actions(self):
        """
        Track-Menü anzeigen
        """                    
        data = {}
        data['track_name']  = self.model.get_track_item(self.channel_pos)                
        data['channel'] = self.channel
        response = self.view.track_actions(data)
        self.handle(response)

    def show_change_volume(self):
        """
        Die Lautstärkefunktion anzeigen
        """                                      
        data = {}
        self.model.set('channel', self.channel)
        volume = self.model.get_channel_volume()
        data['volume'] = volume
        data['channel'] = self.channel
        response = self.view.change_volume(data)
        self.handle(response)
    
    def show_metadata(self):
        """
        Die Metadaten eines Tracks anzeigen
        """                                    
        if self.channel == 'playlist':
            self.model.set('channel_pos', self.channel_pos)
            medatada = self.model.get_playlist_item_metadata()
        else:                
            self.model.set('channel', self.channel)
            self.model.set('channel_pos', self.channel_pos)
            medatada = self.model.get_track_item_metadata()
        data = {}
        data['metadata'] = medatada 
        self.view.metadata(data)
        
    """
    Kommandos an den Controller:
    """    
    def cmd_load_playlist(self):
        """
        Playlist auswählen und Playlist laden an den CombaController senden
        @rtype:  string
        @return: Rückgabe des CombaControllers
        """
        self.channel = 'playlist'
        data = {}
        result = ''
        data['dir'] = '/var/audio/playlists/'       
        file = self.view.open_file(data)
        if os.path.isfile(file):
            result = self.client.playlist_load(file) 
        return result        
        
    def cmd_play_playlist(self):
        """
        Playlist starten
        @rtype:  string
        @return: Rückgabe des CombaControllers
        """
        return self.client.playlist_play()
    
    def cmd_stop_playlist(self):
        """
        Playlist stoppen
        @rtype:  string
        @return: Rückgabe des CombaControllers
        """
        return self.client.playlist_pause()

    def cmd_channel_insert(self):    
        """
        Audio auswählen und einem Kanal als Track hinzufügen 
        @rtype:  string
        @return: Rückgabe des CombaControllers
        """
        data = {}
        result = ''
        data['dir'] = '/var/audio/jingles/'       
        file = self.view.open_file(data)
        if os.path.isfile(file):
            result = self.client.channel_track_insert(self.channel, file) 
        return result    
    
    def cmd_switch_channel(self):
        """
        Kanal von An auf Aus bzw. von Aus auf An umschalten 
        @rtype:  string
        @return: Rückgabe des CombaControllers
        """                                
        if self.channel_active:
            self.client.channel_off(self.channel)
        else:
            self.client.channel_on(self.channel)
    
    def cmd_channel_set_volume(self,volume):
        """
        Lautstärke eines Kanals setzen 
        @rtype:  string
        @return: Rückgabe des CombaControllers
        """                
        self.client.channel_set_volume(self.channel, volume)
        return self.model.set('channel_volume', volume)


    def cmd_channel_seek_track(self, duration):        
        """
        Im aktuell laufenden Track vorspulen 
        @rtype:  string
        @return: Rückgabe des CombaControllers
        """                
        self.client.channel_seek(self.channel, duration)
        
            
    def cmd_channel_removetrack(self):
        """
        Track aus dem Channel löschen  
        @rtype:  string
        @return: Rückgabe des CombaControllers
        """  
        if self.channel_pos == 0:
            self.cmd_skip_channeltrack()    
        else:
            if self.channel == 'playlist':
                self.client.playlist_remove_track(self.channel_pos)
            else:        
                self.client.channel_remove_track(self.channel, self.channel_pos)

    def cmd_skip_channeltrack(self):
        """
        Aktuell laufenden Track skippen  
        @rtype:  string
        @return: Rückgabe des CombaControllers
        """        
        if self.channel == 'playlist':
            self.client.playlist_skip()
        else:
            self.client.skip_channel(self.channel)    
            
    def cmd_track_up(self):           
        """
        Einen Track um eine Position nach oben verschieben  
        @rtype:  string
        @return: Rückgabe des CombaControllers
        """        
        if self.channel == 'playlist':
            self.client.playlist_track_up(self.channel_pos)
        else:
            if self.channel_pos == 1:
                return
            self.client.channel_track_up(self.channel, self.channel_pos)

    def cmd_track_down(self):        
        """
        Einen Track um eine Position nach unten verschieben  
        @rtype:  string
        @return: Rückgabe des CombaControllers
        """        
        if self.channel == 'playlist':
            self.client.playlist_track_down(self.channel_pos)
        else:
            if self.channel_pos < 1:
                return
            self.client.channel_track_down(self.channel, self.channel_pos)
                        

def main():
     """This runs the controller.
     """
     ##from combalib.adapter.client.tcpadapter import ClientTCPAdapter
     from python.adapter.client.zmqadapter import ClientZMQAdapter
     try:
         ##controller = Controller(CombaClient(ClientTCPAdapter(HOST, PORT)))
         adapter = ClientZMQAdapter('localhost', 9099)
         controller = Controller(CombaClient(adapter))         
     except dialog.error, exc_instance:
         sys.stderr.write("Error:\n\n%s\n" % exc_instance.complete_message())
         sys.exit(1)
     controller.run()    
     sys.exit(0)
  
if __name__ == "__main__": main()
        
