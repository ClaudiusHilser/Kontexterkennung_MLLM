from kivy.config import Config
Config.set('graphics', 'density', '1')  # Verhindert übergroße Schrift/Abstände im Vollbild

import os
import socket
import threading
from kivy.app import App
from kivy.clock import Clock
from kivy.factory import Factory
from kivy.lang import Builder
from kivy.properties import NumericProperty
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.core.audio import SoundLoader
from datetime import datetime
from kivy.core.window import Window
from kivy.properties import BooleanProperty
import atexit
import sys


import pytz
import csv

# ------------------- UDP Listener -------------------

class UDPListener:
    def __init__(self, callback, ip="0.0.0.0", port=27299):
        self.ip = ip
        self.port = port
        self.callback = callback
        self.running = False

    def start(self):
        self.running = True
        threading.Thread(target=self._listen, daemon=True).start()

    def stop(self):
        self.running = False

    def _listen(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(0.1)
        try:
            sock.bind((self.ip, self.port))
            print(f"[UDP] Listener aktiv auf {self.ip}:{self.port}")
        except Exception as e:
            print(f"[UDP] Fehler beim Binden: {e}")
            return

        while self.running:
            try:
                data, addr = sock.recvfrom(1024)
                msg = data.decode("utf-8").strip()
                Clock.schedule_once(lambda dt: self.callback(msg))
            except socket.timeout:
                continue
            except Exception as e:
                print(f"[UDP] Fehler: {e}")

# ------------------- Kivy App -------------------

class MyPopupContent(FloatLayout):
    """Base class for all popup contents, providing navigation and data recording."""
    rating = NumericProperty(0)

    def next_step(self):
        """Close the parent Popup and advance the experiment sequence."""
        widget = self
        # Climb up the widget tree until we find the Popup instance
        while widget and not isinstance(widget, Popup):
            widget = widget.parent
        if widget:
            widget.dismiss()
        App.get_running_app().root.next_step()

    def on_submit(self, value):
        """Record a numeric submission and proceed to the next step."""
        App.get_running_app().root.record_input(self.__class__.__name__, value)
        self.next_step()

    def submit_choice(self, choice):
        """Record a choice submission and proceed to the next step."""
        App.get_running_app().root.record_input(self.__class__.__name__, choice)
        self.next_step()




class Popup0_Name(MyPopupContent):
    """Popup for collecting the participant's name."""

    def on_submit(self, value=None):
        """Capture the entered name, record it, and move on."""
        name = self.ids.name_input.text.strip()
        wm = App.get_running_app().root
        wm.username = name
        wm.record_input('Name', name)
        self.next_step()
class Popup_Kontrollgefühl(MyPopupContent):
    def on_submit(self, value):
        App.get_running_app().root.record_input("Kontrollgefühl", value)
        self.next_step()

class Popup_Vorbereitung(MyPopupContent):
    def submit_choice(self, choice):
        App.get_running_app().root.record_input("Vorbereitung", choice)
        self.next_step()



class Popup1_Rechenaufgabe(MyPopupContent):
    """Zeigt zuerst eine Erklärung mit 20s Countdown, danach startet Audio und zeigt Hinweistext. Nach Audio 5s Abschlusstext."""
    seconds = NumericProperty(35)
    show_hint = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._prep_phase = Clock.schedule_interval(self._update_prep_countdown, 1)

    def _update_prep_countdown(self, dt):
        if self.seconds > 0:
            self.seconds -= 1
        else:
            self._prep_phase.cancel()
            self.ids.countdown_label.opacity = 0
            self.ids.hint_label.opacity = 1
            self.start_audio()

    def start_audio(self):
        base = os.path.dirname(os.path.abspath(__file__))
        folder = os.path.join(base, 'Rechenaufgabe')
        files = [f for f in os.listdir(folder) if f.lower().endswith('.mp3')]
        if files:
            path = os.path.join(folder, files[0])
            self.sound = SoundLoader.load(path)
            if self.sound:
                self.sound.bind(on_stop=self.on_audio_end)
                self.sound.play()
            else:
                print(f"[Error] Could not load audio at {path}")
        else:
            print(f"[Warning] No .mp3 found in {folder}")

    def on_audio_end(self, *args):
        self.ids.hint_label.opacity = 0
        self.ids.end_label.opacity = 1
        Clock.schedule_once(lambda dt: self.next_step(), 5)

    def next_step(self):
        if hasattr(self, 'sound') and self.sound:
            self.sound.stop()
        super().next_step()

    def _update_countdown(self, dt):
        if self.seconds > 0:
            self.seconds -= 1
        else:
            self._timer.cancel()
            if hasattr(self, 'sound') and self.sound:
                self.sound.stop()
        return True

class Popup3_Musikintervention(MyPopupContent):
    """Play a 90s relaxation track, show countdown, then auto-advance."""
    # Resolve the two tracks in a platform-independent way
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    MUSIC_DIR = os.path.join(BASE_DIR, 'Entspannungsmusik')
    _tracks = [
        os.path.join(MUSIC_DIR, 'track1.mp3'),
        os.path.join(MUSIC_DIR, 'track2.mp3'),
    ]
    _play_count = 0

    # Countdown timer in seconds
    seconds = NumericProperty(120)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Round-robin choice of track
        Popup3_Musikintervention._play_count += 1
        idx = (Popup3_Musikintervention._play_count - 1) % len(self._tracks)
        track_path = self._tracks[idx]

        # Load and start playback
        self.sound = SoundLoader.load(track_path)
        if self.sound:
            self.sound.play()
        else:
            print(f"[Error] Could not load {track_path}")

        # Schedule the per-second countdown
        self._timer_event = Clock.schedule_interval(self._update_countdown, 1)

    def _update_countdown(self, dt):
        """Decrement the timer; when it hits zero, stop and advance."""
        if self.seconds > 0:
            self.seconds -= 1
        else:
            # stop the scheduler and the sound
            self._timer_event.cancel()
            if hasattr(self, 'sound') and self.sound:
                self.sound.stop()
            # then close and go to next step
            self.next_step()
        return True

class Popup9_ManuelleFahrt(MyPopupContent):
    seconds = NumericProperty(10)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._event = Clock.schedule_interval(self._countdown, 1)

    def _countdown(self, dt):
        if self.seconds > 0:
            self.seconds -= 1
        else:
            self._event.cancel()

            # Popup schließen
            widget = self
            while widget and not isinstance(widget, Popup):
                widget = widget.parent
            if widget:
                widget.dismiss()

            # Einfach weiter im Ablauf
            App.get_running_app().root.next_step()
        return True

class FahrenScreen(Screen):
    pass

class Popup10_HinweisFahren(MyPopupContent):
    """Popup indicating automated driving will resume after 5 seconds."""
    seconds = NumericProperty(5)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._event = Clock.schedule_interval(self._countdown, 1)

    def _countdown(self, dt):
        """Reduce the timer each second; proceed when it hits zero."""
        if self.seconds > 0:
            self.seconds -= 1
        else:
            self._event.cancel()
            self.next_step()
        return True

class Popup_Klima(MyPopupContent):
    temperature = NumericProperty(18)

    def increase_temp(self):
        if self.temperature < 30:
            self.temperature += 1

    def decrease_temp(self):
        if self.temperature > 16:
            self.temperature -= 1

class KlimaScreen(Screen):
    temp = NumericProperty(18)

    def show_success(self):
        wm = App.get_running_app().root
        if (wm.current_clima_task == "clima1" and self.temp == 24) or \
                (wm.current_clima_task == "clima2" and self.temp == 20):
            self.ids.success_label.opacity = 1
            Clock.schedule_once(lambda dt: setattr(wm, 'current', 'infotainment'), 2)
            Clock.schedule_once(lambda dt: App.get_running_app().root.start_next_infotainment_task(), 8)

    def on_pre_enter(self):
        self.ids.success_label.opacity = 0

    def adjust_temp(self, change):
        self.temp += change
        self.ids.temp_label.text = "Aktuelle Temperatur: " + str(self.temp) + " °C"

        wm = App.get_running_app().root
        if wm.current_clima_task == "clima1" and self.temp == 24:
            self.show_success()
        elif wm.current_clima_task == "clima2" and self.temp == 20:
            self.show_success()


class NavigationScreen(Screen):
    def start_navigation(self):
        von = self.ids.input_von.text
        nach = self.ids.input_nach.text
        wm = App.get_running_app().root

        # Erfolg nur, wenn Aufgabe aktiv ist
        if wm.current_navigation_task == "nav1" and von == "Fraunhofer IAO, Stuttgart" and nach == "Universität Stuttgart":
            self.show_success()

        elif wm.current_navigation_task == "nav2" and von == "RWTH Aachen" and nach == "Karlsruher Institut für Technologie (KIT)":
            self.show_success()

    def show_success(self):
        self.ids.success_label.opacity = 1
        Clock.schedule_once(lambda dt: setattr(App.get_running_app().root, 'current', 'infotainment'), 2)
        Clock.schedule_once(lambda dt: App.get_running_app().root.start_next_infotainment_task(), 8)

    def on_pre_enter(self):
        self.ids.success_label.opacity = 0


class FahrzeugdatenScreen(Screen):
    def show_denied(self, message):
        self.ids.info_label.text = message

class LenkradheizungScreen(Popup):
    def show_success(self):
        self.ids.success_label.text = "Die Aufgabe wurde erfolgreich erfüllt"
        self.ids.success_label.opacity = 1
        Clock.schedule_once(lambda dt: setattr(App.get_running_app().root, 'current', 'infotainment'), 2)
        Clock.schedule_once(lambda dt: self.dismiss(), 5)
        Clock.schedule_once(lambda dt: App.get_running_app().root.start_next_infotainment_task(), 8)

    def trigger_ablenkung_popup(self):
        popup_cls = Factory.Popup6_Ablenkung1
        content = popup_cls()
        popup = Popup(
            title='',
            content=content,
            size_hint=(1, 1),
            auto_dismiss=False,
            background_color=(0, 0, 0, 1),
            separator_height=0
        )
        popup.open()


class Popup_StartKlima(MyPopupContent):
    pass


class Popup_StartNavigation(MyPopupContent):
    pass


class Popup_StartReifendruck(MyPopupContent):
    pass


class MainWindow(Screen):
    """Main entry and fallback screen for the experiment."""
    pass


class InfotainmentScreen(Screen):
    """Screen for Scenario 2: interaction with the infotainment system."""
    pass

class Popup2_Stresslevel(MyPopupContent):
    def on_submit(self, value):
        App.get_running_app().root.record_input("Stresslevel", value)
        # Popup schließen
        self.next_step()
        # 5 Sekunden warten → dann Musik starten
        Clock.schedule_once(lambda dt: App.get_running_app().root.next_step(), 5)
class Popup2_2_Stresslevel(MyPopupContent):
    def on_submit(self, value):
        App.get_running_app().root.record_input("Stresslevel", value)
        self.next_step()
class Popup4_Entspannung1(MyPopupContent):
    def on_submit(self, value):
        App.get_running_app().root.record_input("Entspannung1", value)
        self.next_step()
class Popup6_Ablenkung1(MyPopupContent):
    def on_submit(self, value):
        App.get_running_app().root.record_input("Ablenkung", value)
        self.next_step()

class Popup8_StehendesFahrzeug(MyPopupContent):
    def submit_choice(self, choice):
        wm = App.get_running_app().root
        wm.record_input(self.__class__.__name__, choice)
        wm.current = "main"

        # Popup schließen
        widget = self
        while widget and not isinstance(widget, Popup):
            widget = widget.parent
        if widget:
            widget.dismiss()

class Popup_StoppschildHinweis(MyPopupContent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Clock.schedule_once(self.close_and_continue, 5)

    def close_and_continue(self, dt):
        # Popup schließen
        for widget in App.get_running_app().root_window.children:
            if isinstance(widget, Popup):
                widget.dismiss()
        # Weiter im Ablauf
        App.get_running_app().root.next_step()




class KomfortverbraucherScreen(Screen):
    def handle_frontscheibe(self):
        wm = App.get_running_app().root
        if getattr(wm, 'current_front_task', False):
            wm.current_front_task = False  # Aufgabe abgeschlossen
            self.ids.error_label.color = (0, 1, 0, 1)
            self.ids.error_label.text = "Die Aufgabe wurde erfolgreich erfüllt"
            self.ids.error_label.opacity = 1
            Clock.schedule_once(lambda dt: setattr(wm, 'current', 'infotainment'), 2)
            Clock.schedule_once(lambda dt: App.get_running_app().root.start_next_infotainment_task(), 5)
        else:
            self.ids.error_label.color = (1, 0, 0, 1)
            self.ids.error_label.text = "Kein Zugriff auf diese Funktion"
            self.ids.error_label.opacity = 1



class WindowManager(ScreenManager):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.username = None
        self.data = []
        self.sequence = [
            {'type': 'popup', 'name': 'Popup0_Name'},
            {'type': 'screen', 'name': 'main'},
            {'type': 'popup', 'name': 'Popup1_Rechenaufgabe'},
            {'type': 'popup', 'name': 'Popup2_Stresslevel'},
            {'type': 'screen', 'name': 'main'},
            {'type': 'popup', 'name': 'Popup3_Musikintervention'},
            {'type': 'popup', 'name': 'Popup4_Entspannung1'},
            {'type': 'popup', 'name': 'Popup5_Entspannung2'},
            {'type': 'screen', 'name': 'main'},
            {'type': 'screen', 'name': 'infotainment'},
            {'type': 'popup', 'name': 'Popup6_Ablenkung1'},
            {'type': 'popup', 'name': 'Popup7_Warnungswunsch'},
            {'type': 'popup', 'name': 'Popup8_StehendesFahrzeug'},
            {'type': 'screen', 'name': 'main'},
            {'type': 'popup', 'name': 'Popup9_ManuelleFahrt'},
            {'type': 'screen', 'name': 'fahren'},
            {'type': 'popup', 'name': 'Popup_StoppschildHinweis'},
            {'type': 'popup', 'name': 'Popup2_2_Stresslevel'},
            {'type': 'popup', 'name': 'Popup_Vorbereitung'},
            {'type': 'popup', 'name': 'Popup_Kontrollgefühl'},
            {'type': 'popup', 'name': 'Popup11_Abschluss'},
        ]
        self.index = -1
        self.infotainment_timer_set = False
        self.infotainment_sequence = [
            "Popup_StartKlima",
            "Popup_StartNavigation",
            "Popup_StartLenkgrad",
            "Popup_StartNavigation2",
            "Popup_StartKlima2",
            "Popup_StartFrontscheibe"
        ]
        self.infotainment_task_index = 0
        self.infotainment_active = False  # ← Wird erst nach Start aktiviert

    def record_input(self, step, value):
        print(f"[Datenerfassung] Schritt: {step}, Wert: {value}")
        self.data.append({'step': step, 'value': value})

    def next_step(self):
        self.index += 1
        if self.index >= len(self.sequence):
            self.save_results()
            return

        item = self.sequence[self.index]
        if item['type'] == 'screen':
            self.current = item['name']
            if item['name'] == 'infotainment' and not self.infotainment_timer_set:
                # Erklärpopup anzeigen
                self.show_popup("Popup_InfotainmentAufgabenerkl")

                # 10 s später: Erklärpopup schließen, Aufgabe 1 starten, Timer starten
                def start_infotainment_sequence(dt):
                    # Erklärpopup schließen (falls offen)
                    for widget in App.get_running_app().root_window.children[:]:
                        if isinstance(widget, Popup):
                            widget.dismiss()

                    # Erste Aufgabe anzeigen
                    self.start_next_infotainment_task()

                    # Abschluss nach 150s (2,5 min)
                    #self.infotainment_timer = Clock.schedule_once(self.end_infotainment_tasks, 150)

                Clock.schedule_once(start_infotainment_sequence, 15)

                self.infotainment_timer_set = True


        else:
            App.get_running_app().play_popup_sound()  # ← Ton abspielen
            popup_cls = Factory.get(item['name'])
            content = popup_cls()
            popup = Popup(
                title='',
                content=content,
                size_hint=(1, 1),
                auto_dismiss=False,
                background_color=(0, 0, 0, 1),
                separator_height=0
            )
            popup.open()

    def show_popup(self, name):

        # Setze aktuellen Navigations-Aufgabentyp
        # Setze aktuellen Aufgabentyp und bereite den zugehörigen Screen vor
        if name == "Popup_StartNavigation":
            self.current_navigation_task = "nav1"
            screen = self.get_screen("navigation")
            screen.ids.success_label.opacity = 0

        elif name == "Popup_StartNavigation2":
            self.current_navigation_task = "nav2"
            screen = self.get_screen("navigation")
            screen.ids.success_label.opacity = 0

        elif name == "Popup_StartKlima":
            self.current_clima_task = "clima1"
            screen = self.get_screen("klima")
            screen.ids.success_label.opacity = 0

        elif name == "Popup_StartKlima2":
            self.current_clima_task = "clima2"
            screen = self.get_screen("klima")
            screen.ids.success_label.opacity = 0

        elif name == "Popup_StartFrontscheibe":
            self.current_front_task = True

        App.get_running_app().play_popup_sound()  # Ton beim Anzeigen

        popup_cls = Factory.get(name)
        content = popup_cls()
        popup = Popup(
            title='',
            content=content,
            size_hint=(1, 1),
            auto_dismiss=False,
            background_color=(0, 0, 0, 1),
            separator_height=0
        )
        content.parent_widget = popup
        popup.open()

    def jump_to(self, target_name):
        for i, item in enumerate(self.sequence):
            if item['name'] == target_name:
                self.index = i - 1
                print(f"[Jump] Sequence-Index gesetzt auf {self.index + 1} ({target_name})")
                return
        print(f"[Jump] {target_name} nicht in sequence gefunden")

    def start_next_infotainment_task(self):
        self.infotainment_active = True

        if self.infotainment_task_index >= len(self.infotainment_sequence):
            # Alle Aufgaben durch → jetzt Abschluss-Popup nach 5 Sekunden zeigen
            Clock.schedule_once(self.show_infotainment_abschluss_popup, 4)
            return


        popup_name = self.infotainment_sequence[self.infotainment_task_index]
        self.infotainment_task_index += 1
        self.show_popup(popup_name)

    def show_infotainment_abschluss_popup(self, dt):
        popup_cls = Factory.get("Popup_InfotainmentAbschluss")
        content = popup_cls()
        popup = Popup(
            title='',
            content=content,
            size_hint=(1, 1),
            auto_dismiss=False,
            background_color=(0, 0, 0, 1),
            separator_height=0
        )
        popup.open()

        # Popup nach 5s schließen, dann mit Ablauf fortfahren
        def close_and_continue(_):
            popup.dismiss()
            self.next_step()

        Clock.schedule_once(close_and_continue, 5)

    def end_infotainment_tasks(self, dt):
        # Aktives Popup schließen

        for widget in App.get_running_app().root_window.children[:]:
            if isinstance(widget, Popup):
                widget.dismiss()

        # Abschluss anzeigen und merken
        popup_cls = Factory.get("Popup_InfotainmentAbschluss")
        content = popup_cls()
        popup = Popup(
            title='',
            content=content,
            size_hint=(1, 1),
            auto_dismiss=False,
            background_color=(0, 0, 0, 1),
            separator_height=0
        )
        popup.open()

        # Popup nach 5 s schließen und dann weiter
        def close_and_continue(dt):
            popup.dismiss()
            self.next_step()

        Clock.schedule_once(close_and_continue, 5)

        # Abschluss anzeigen
        self.show_popup("Popup_InfotainmentAbschluss")

        # Danach automatisch weiter im Ablauf
        Clock.schedule_once(lambda dt: self.next_step(), 5)

    def save_results(self):
        import csv
        base_dir = os.path.dirname(os.path.realpath(sys.argv[0]))

        user_data_dir = os.path.join(base_dir, 'User_Data')
        os.makedirs(user_data_dir, exist_ok=True)

        filename = f"{self.username or 'Teilnehmer'}.csv"
        filepath = os.path.join(user_data_dir, filename)

        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['step', 'value'])
            writer.writeheader()
            writer.writerows(self.data)

        print(f"Results saved to {filepath}")

    def skip_infotainment_task(self):
        if not self.infotainment_active:
            print("[Info] Aufgabenlauf noch nicht aktiv – kein Überspringen möglich.")
            return
        self.start_next_infotainment_task()


# ------------------- App-Klasse -------------------

class MyMainApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.triggered_signals = set()  # ← wichtig: vor Start des UDP-Listeners
        self.mockup_events = []
        self.base_dir = os.path.dirname(os.path.realpath(sys.argv[0]))
        self.my_user_data_dir = os.path.join(self.base_dir, 'User_Data')
        os.makedirs(self.user_data_dir, exist_ok=True)

    def build(self):
        return Builder.load_file("my.kv")

    def on_start(self):
        #self.root.jump_to("fahren")
        #self.root.next_step()

        self.root.next_step()
        self.udp_listener = UDPListener(self.handle_udp)
        self.udp_listener.start()

    def on_stop(self):
        print("[DEBUG] on_stop aufgerufen")  # Testzeile

        if self.root and hasattr(self.root, 'save_results'):
            print("[DEBUG] Teilnehmerdaten speichern...")
            self.root.save_results()

        if self.mockup_events:
            print(f"[DEBUG] Speichere {len(self.mockup_events)} Mockup-Einträge...")

            base_dir = os.path.dirname(os.path.abspath(__file__))
            user_data_dir = os.path.join(base_dir, 'User_Data')
            os.makedirs(user_data_dir, exist_ok=True)

            username = self.root.username or 'Teilnehmer'
            filepath = os.path.join(user_data_dir, f"{username}_mockup_log.csv")

            try:
                with open(filepath, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=['event', 'timestamp'])
                    writer.writeheader()
                    writer.writerows(self.mockup_events)
                print(f"[Mockup] Log gespeichert unter {filepath}")
            except Exception as e:
                print(f"[Mockup] Fehler beim Speichern: {e}")
        else:
            print("[DEBUG] Keine Mockup-Events vorhanden")

    def handle_udp(self, message):
        print(f"[UDP] Empfangen: {message}")
        wm = self.root

        if message in self.triggered_signals:
            return

        popup_name = None

        if "rechnen" in message:
            popup_name = "Popup1_Rechenaufgabe"
            wm.jump_to(popup_name)
            self.log_mockup_event("Rechnen")
            wm.next_step()

        elif "stoppschild" in message:
            popup_name = "Popup_StoppschildHinweis"
            wm.jump_to(popup_name)
            wm.next_step()
        elif "musik" in message:
            popup_name = "Popup3_Musikintervention"
            wm.jump_to(popup_name)
            self.log_mockup_event("Musikintervention")
            wm.next_step()

        elif "stress" in message:
            popup_name = "Popup2_Stresslevel"
            wm.jump_to(popup_name)
            wm.next_step()
        elif "janein" in message:
            popup_name = "Popup5_Entspannung2"
            wm.jump_to(popup_name)
            wm.next_step()

        elif "baustelle" in message:
            popup_name = "Popup9_ManuelleFahrt"
            wm.jump_to(popup_name)
            self.log_mockup_event("Baustelle")
            wm.next_step()

        elif "abschluss" in message:
            popup_name = "Popup11_Abschluss"
            wm.jump_to(popup_name)
            wm.next_step()

        elif "infotainment" in message:
            wm.jump_to("infotainment")
            self.log_mockup_event("Infotainment")
            # offene Popups schließen
            for widget in App.get_running_app().root_window.children[:]:
                if isinstance(widget, Popup) and widget.title != popup_name:
                    widget.dismiss()
            wm.next_step()
            self.triggered_signals.add(message)
            return

        else:
            return

        self.triggered_signals.add(message)


    def log_mockup_event(self, name):
        tz = pytz.timezone("Europe/Berlin")
        timestamp = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
        self.mockup_events.append({'event': name, 'timestamp': timestamp})
        print(f"[Mockup] {name} gestartet um {timestamp}")

    def play_popup_sound(self):
        base = os.path.dirname(os.path.abspath(__file__))
        sound_path = os.path.join(base, "Earcon_proactive.wav")
        sound = SoundLoader.load(sound_path)
        if sound:
            sound.play()
        else:
            print("[Sound] Fehler beim Laden des PopUp-Tons")


from kivy.core.window import Window  # Ganz oben im File, falls noch nicht vorhanden

if __name__ == '__main__':
    #Window.fullscreen = 'auto'
    #Window.size = (2880, 1920)     # ← nur wirksam, wenn fullscreen=False
   # Window.fullscreen = True       # ← aktiviert echten Vollbildmodus
    MyMainApp().run()

