from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.togglebutton import ToggleButton
from kivy.graphics import Color, RoundedRectangle
from gtts import gTTS
import pygame
import requests
import tempfile


def obtener_buses(paradero_id):
    url = f"https://api.xor.cl/red/bus-stop/{paradero_id}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Error al obtener datos: {e}")
    return None


def reproducir_audio(texto):
    try:
        tts = gTTS(text=texto, lang='es')
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmpfile:
            archivo_audio = tmpfile.name
            tts.save(archivo_audio)
        pygame.mixer.init()
        pygame.mixer.music.load(archivo_audio)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
    except Exception as e:
        print(f"Error al reproducir audio: {e}")


class Tarjeta(BoxLayout):
    def __init__(self, texto, color, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint_y = None
        self.height = 80
        self.padding = 10
        with self.canvas.before:
            Color(*color)
            self.bg = RoundedRectangle(radius=[10])
        self.bind(pos=self.update_bg, size=self.update_bg)
        self.label = Label(text=texto, font_size=18, color=(1, 1, 1, 1))
        self.add_widget(self.label)

    def update_bg(self, *args):
        self.bg.pos = self.pos
        self.bg.size = self.size


class BusParaderoApp(App):
    def build(self):
        self.tema_claro = False
        self.color_fondo = (0.1, 0.1, 0.1, 1)

        self.root = BoxLayout(orientation='vertical', padding=20, spacing=15)

        self.titulo = Label(text="🚌 [b]Próximos Buses[/b]", markup=True, font_size=32, size_hint_y=None, height=60)
        self.root.add_widget(self.titulo)

        self.paradero_input = TextInput(hint_text="Código del paradero (ej: PA433)", multiline=False, size_hint_y=None, height=40)
        self.root.add_widget(self.paradero_input)

        botones = BoxLayout(orientation='horizontal', size_hint_y=None, height=50, spacing=10)
        self.btn_actualizar = Button(text="🔄 Actualizar", background_color=(0.1, 0.5, 1, 1), font_size=16)
        self.btn_actualizar.bind(on_press=self.actualizar)

        self.btn_audio = Button(text="🔊 Decir tiempos", background_color=(1, 0.6, 0, 1), font_size=16)
        self.btn_audio.bind(on_press=self.actualizar_y_hablar)

        self.tema_toggle = ToggleButton(text="🌙 Tema oscuro", state='down', size_hint_x=0.6)
        self.tema_toggle.bind(on_press=self.toggle_tema)

        botones.add_widget(self.btn_actualizar)
        botones.add_widget(self.btn_audio)
        botones.add_widget(self.tema_toggle)
        self.root.add_widget(botones)

        self.scroll = ScrollView()
        self.contenedor = GridLayout(cols=1, spacing=10, size_hint_y=None, padding=(0, 10))
        self.contenedor.bind(minimum_height=self.contenedor.setter('height'))
        self.scroll.add_widget(self.contenedor)
        self.root.add_widget(self.scroll)

        with self.root.canvas.before:
            Color(*self.color_fondo)
            self.rect = RoundedRectangle()
        self.root.bind(size=self._update_background, pos=self._update_background)

        return self.root

    def _update_background(self, *args):
        self.rect.pos = self.root.pos
        self.rect.size = self.root.size

    def toggle_tema(self, instance):
        self.tema_claro = not self.tema_claro
        if self.tema_claro:
            self.tema_toggle.text = "☀️ Tema claro"
            self.color_fondo = (1, 1, 1, 1)
        else:
            self.tema_toggle.text = "🌙 Tema oscuro"
            self.color_fondo = (0.1, 0.1, 0.1, 1)
        with self.root.canvas.before:
            Color(*self.color_fondo)
            self.rect = RoundedRectangle()
        self._update_background()

    def actualizar(self, *args):
        self.contenedor.clear_widgets()
        self.texto_a_decir = ""
        paradero = self.paradero_input.text.strip() or "PA433"
        datos = obtener_buses(paradero)

        if not datos or "services" not in datos:
            self.contenedor.add_widget(Tarjeta("❌ No se pudieron cargar los datos", color=(0.8, 0, 0, 1)))
            return

        for servicio in datos["services"]:
            linea = servicio["id"]
            estado = servicio["status_description"]
            if servicio["valid"] and servicio["buses"]:
                for bus in servicio["buses"]:
                    llegada = f"{bus['min_arrival_time']} - {bus['max_arrival_time']} min"
                    texto = f"🚌 Línea {linea}\n⏳ Llega en {llegada}"
                    self.contenedor.add_widget(Tarjeta(texto, color=(0.2, 0.4, 0.8, 1)))
                    self.texto_a_decir += f"El bus de la línea {linea} llegará entre {bus['min_arrival_time']} y {bus['max_arrival_time']} minutos. "
            else:
                texto = f"🚫 Línea {linea}: {estado}"
                self.contenedor.add_widget(Tarjeta(texto, color=(0.5, 0.2, 0.2, 1)))

    def actualizar_y_hablar(self, *args):
        self.actualizar()
        if self.texto_a_decir:
            reproducir_audio(self.texto_a_decir)
        else:
            reproducir_audio("No hay buses disponibles en este momento.")


if __name__ == '__main__':
    BusParaderoApp().run()
