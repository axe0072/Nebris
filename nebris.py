import sys
import os

# Optimizacija za Windows
if os.name == 'nt':
    # Povećaj prioritet procesa
    try:
        import win32api
        import win32process
        import win32con
        pid = win32api.GetCurrentProcessId()
        handle = win32api.OpenProcess(win32con.PROCESS_ALL_ACCESS, True, pid)
        win32process.SetPriorityClass(handle, win32process.BELOW_NORMAL_PRIORITY_CLASS)
    except ImportError:
        pass

# Optimizacija PyQt
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
os.environ["QT_SCALE_FACTOR"] = "1"
import winreg  
import ctypes
import calendar
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QSystemTrayIcon, QMenu,
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QDoubleSpinBox, QComboBox, QCheckBox, QPushButton,
    QGridLayout, QStyle
)
from PyQt6.QtGui import QIcon, QFont, QAction, QPainter, QColor, QPen
from PyQt6.QtCore import Qt, QSettings, QTimer, QTime, QPropertyAnimation, QRect, QEasingCurve

# --- Windows API za idle time ---
class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [("cbSize", ctypes.c_uint), ("dwTime", ctypes.c_uint)]

def get_idle_duration():
    lii = LASTINPUTINFO()
    lii.cbSize = ctypes.sizeof(LASTINPUTINFO)
    ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lii))
    millis = ctypes.windll.kernel32.GetTickCount() - lii.dwTime
    return millis / 1000.0

# --- Audio detekcija ---
try:
    from pycaw.pycaw import AudioUtilities, IAudioMeterInformation
    from ctypes import POINTER, cast
    from comtypes import CLSCTX_ALL
    AUDIO_DETECTION_AVAILABLE = True
except ImportError:
    AUDIO_DETECTION_AVAILABLE = False
    print("Audio detekcija nije dostupna. Instalirajte pycaw: pip install pycaw")

# --- Jezičke podrške ---
LANGUAGES = {
    "en": {"name": "English", "flag": "🇺🇸", "days": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
           "months": ["January", "February", "March", "April", "May", "June", "July", "August", 
                      "September", "October", "November", "December"]},
    "ru": {"name": "Русский", "flag": "🇷🇺", "days": ["Пон", "Вто", "Сре", "Чет", "Пят", "Суб", "Вос"],
           "months": ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь", "Июль", "Август", 
                      "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"]},
    "tr": {"name": "Türkçe", "flag": "🇹🇷", "days": ["Pzt", "Sal", "Çar", "Per", "Cum", "Cmt", "Paz"],
           "months": ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", 
                      "Eylül", "Ekim", "Kasım", "Aralık"]},
    "es": {"name": "Español", "flag": "🇪🇸", "days": ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"],
           "months": ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", 
                      "Septiembre", "Octubre", "Noviembre", "Diciembre"]},
    "fr": {"name": "Français", "flag": "🇫🇷", "days": ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"],
           "months": ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", 
                      "Septembre", "Octobre", "Novembre", "Décembre"]},
    "sr": {"name": "Српски", "flag": "🇷🇸", "days": ["Пон", "Уто", "Сре", "Чет", "Пет", "Суб", "Нед"],
           "months": ["Јануар", "Фебруар", "Март", "Април", "Мај", "Јун", "Јул", "Август", 
                      "Септембар", "Октобар", "Новембар", "Децембар"]},
    "pt": {"name": "Português", "flag": "🇵🇹", "days": ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"],
           "months": ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", 
                      "Setembro", "Outubro", "Novembro", "Dezembro"]},
    "zh": {"name": "中文", "flag": "🇨🇳", "days": ["周一", "周二", "周三", "周四", "周五", "周六", "周日"],
           "months": ["一月", "二月", "三月", "四月", "五月", "六月", "七月", "八月", 
                      "九月", "十月", "十一月", "十二月"]},
    "de": {"name": "Deutsch", "flag": "🇩🇪", "days": ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"],
           "months": ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", 
                      "September", "Oktober", "November", "Dezember"]},
    "it": {"name": "Italiano", "flag": "🇮🇹", "days": ["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"],
           "months": ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno", "Luglio", "Agosto", 
                      "Settembre", "Ottobre", "Novembre", "Dicembre"]},
    "ja": {"name": "日本語", "flag": "🇯🇵", "days": ["月", "火", "水", "木", "金", "土", "日"],
           "months": ["1月", "2月", "3月", "4月", "5月", "6月", "7月", "8月", 
                      "9月", "10月", "11月", "12月"]},
    "ar": {"name": "العربية", "flag": "🇸🇦", "days": ["الاثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت", "الأحد"],
           "months": ["يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو", "يوليو", "أغسطس", 
                      "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"]}
}

# UI prevodi po jezicima
UI_TRANSLATIONS = {
    "en": {
        "select_screensaver": "Select screensaver:",
        "select_font": "Select font:",
        "idle_time": "Idle time (min):",
        "disable_audio": "Disable during audio playback",
        "autostart": "Start with Windows",
        "save": "Save",
        "open_settings": "Open settings",
        "exit": "Exit",
        "settings_title": "Screen Saver Settings"
    },
    "ru": {
        "select_screensaver": "Выберите заставку:",
        "select_font": "Выберите шрифт:",
        "idle_time": "Время бездействия (мин):",
        "disable_audio": "Отключить во время воспроизведения звука",
        "autostart": "Запускать с Windows",
        "save": "Сохранить",
        "open_settings": "Открыть настройки",
        "exit": "Выход",
        "settings_title": "Настройки экранной заставки"
    },
    "tr": {
        "select_screensaver": "Ekran koruyucu seçin:",
        "select_font": "Yazı tipi seçin:",
        "idle_time": "Boşta kalma süresi (dak):",
        "disable_audio": "Ses çalma sırasında devre dışı bırak",
        "autostart": "Windows ile başlat",
        "save": "Kaydet",
        "open_settings": "Ayarları aç",
        "exit": "Çıkış",
        "settings_title": "Ekran Koruyucu Ayarları"
    },
    "es": {
        "select_screensaver": "Seleccionar protector de pantalla:",
        "select_font": "Seleccionar fuente:",
        "idle_time": "Tiempo de inactividad (min):",
        "disable_audio": "Desactivar durante la reproducción de audio",
        "autostart": "Iniciar con Windows",
        "save": "Guardar",
        "open_settings": "Abrir configuración",
        "exit": "Salir",
        "settings_title": "Configuración del protector de pantalla"
    },
    "fr": {
        "select_screensaver": "Sélectionner l'économiseur d'écran:",
        "select_font": "Sélectionner la police:",
        "idle_time": "Temps d'inactivité (min):",
        "disable_audio": "Désactiver pendant la lecture audio",
        "autostart": "Démarrer avec Windows",
        "save": "Enregistrer",
        "open_settings": "Ouvrir les paramètres",
        "exit": "Quitter",
        "settings_title": "Paramètres de l'économiseur d'écran"
    },
    "sr": {
        "select_screensaver": "Изабери screen saver:",
        "select_font": "Изабери фонт:",
        "idle_time": "Време неактивности (мин):",
        "disable_audio": "Онемогући током репродукције звука",
        "autostart": "Покрени са Windows-ом",
        "save": "Сачувај",
        "open_settings": "Отвори подешавања",
        "exit": "Изађи",
        "settings_title": "Screen Saver подешавања"
    },
    "pt": {
        "select_screensaver": "Selecionar protetor de tela:",
        "select_font": "Selecionar fonte:",
        "idle_time": "Tempo de inatividade (min):",
        "disable_audio": "Desativar durante reprodução de áudio",
        "autostart": "Iniciar com o Windows",
        "save": "Salvar",
        "open_settings": "Abrir configurações",
        "exit": "Sair",
        "settings_title": "Configurações do Protetor de Tela"
    },
    "zh": {
        "select_screensaver": "选择屏幕保护程序:",
        "select_font": "选择字体:",
        "idle_time": "空闲时间(分钟):",
        "disable_audio": "音频播放时禁用",
        "autostart": "随Windows启动",
        "save": "保存",
        "open_settings": "打开设置",
        "exit": "退出",
        "settings_title": "屏幕保护程序设置"
    },
    "de": {
        "select_screensaver": "Bildschirmschoner auswählen:",
        "select_font": "Schriftart auswählen:",
        "idle_time": "Leerlaufzeit (min):",
        "disable_audio": "Während der Audiowiedergabe deaktivieren",
        "autostart": "Mit Windows starten",
        "save": "Speichern",
        "open_settings": "Einstellungen öffnen",
        "exit": "Beenden",
        "settings_title": "Bildschirmschoner-Einstellungen"
    },
    "it": {
        "select_screensaver": "Seleziona screen saver:",
        "select_font": "Seleziona font:",
        "idle_time": "Tempo di inattività (min):",
        "disable_audio": "Disattiva durante la riproduzione audio",
        "autostart": "Avvia con Windows",
        "save": "Salva",
        "open_settings": "Apri impostazioni",
        "exit": "Esci",
        "settings_title": "Impostazioni Screen Saver"
    },
    "ja": {
        "select_screensaver": "スクリーンセーバーを選択:",
        "select_font": "フォントを選択:",
        "idle_time": "アイドル時間(分):",
        "disable_audio": "オーディオ再生中は無効",
        "autostart": "Windowsとともに起動",
        "save": "保存",
        "open_settings": "設定を開く",
        "exit": "終了",
        "settings_title": "スクリーンセーバー設定"
    },
    "ar": {
        "select_screensaver": "اختر حافظة الشاشة:",
        "select_font": "اختر الخط:",
        "idle_time": "وقت الخمول (دقيقة):",
        "disable_audio": "تعطيل أثناء تشغيل الصوت",
        "autostart": "بدء التشغيل مع Windows",
        "save": "حفظ",
        "open_settings": "فتح الإعدادات",
        "exit": "خروج",
        "settings_title": "إعدادات حافظة الشاشة"
    }
}

# --- Funkcije za autorun ---
def set_autostart(enabled):
    """Postavlja aplikaciju da se pokreće sa Windowsom ili uklanja iz autostarta"""
    app_name = "ScreenSaverApp"
    app_path = f'"{sys.executable}"' + ' --minimized'
    
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0, winreg.KEY_SET_VALUE
        )
        
        if enabled:
            winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, app_path)
        else:
            try:
                winreg.DeleteValue(key, app_name)
            except FileNotFoundError:
                # Ako ključ ne postoji, ignorišemo
                pass
                
        winreg.CloseKey(key)
        return True
    except Exception as e:
        print(f"Greška pri podešavanju autostarta: {e}")
        return False

def check_autostart():
    """Proverava da li je aplikacija postavljena za autostart"""
    app_name = "ScreenSaverApp"
    
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0, winreg.KEY_READ
        )
        
        try:
            value, _ = winreg.QueryValueEx(key, app_name)
            winreg.CloseKey(key)
            return value == f'"{sys.executable}"' + ' --minimized'
        except FileNotFoundError:
            winreg.CloseKey(key)
            return False
    except Exception:
        return False

# --- Različite verzije screen savera ---
class DigitalClockSaver(QWidget):
    def __init__(self, font_name="Segoe UI", font_size=180, language="en"):
        super().__init__()
        self.font_name = font_name
        self.font_size = font_size
        self.language = language
        self.setupUI()
        self.setCursor(Qt.CursorShape.BlankCursor)

    def setupUI(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.BypassWindowManagerHint
        )
        
        # Koristi QPalette umesto CSS za bolju performansu
        palette = self.palette()
        palette.setColor(self.backgroundRole(), Qt.GlobalColor.black)
        self.setPalette(palette)
        self.setAutoFillBackground(True)
        
        # Prvo postavi layout pa tek onda showFullScreen
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.clock_label = QLabel()
        self.clock_label.setStyleSheet("color: white;")
        self.clock_label.setFont(QFont(self.font_name, self.font_size, QFont.Weight.Bold))
        layout.addWidget(self.clock_label)

        self.showFullScreen()

        # Timer za ažuriranje vremena
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)
        self.update_time()

    def update_time(self):
        """Optimizovano ažuriranje vremena"""
        now = QTime.currentTime()
        self.clock_label.setText(now.toString("HH:mm"))
        
    def keyPressEvent(self, event): self.close()
    def mouseMoveEvent(self, event): self.close()
    def mousePressEvent(self, event): self.close()

class FlipClockSaver(QWidget):
    def __init__(self, font_name="Segoe UI", language="en"):
        super().__init__()
        self.font_name = font_name
        self.language = language
        self.setupUI()
        self.setCursor(Qt.CursorShape.BlankCursor)

    def setupUI(self):
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | 
                           Qt.WindowType.WindowStaysOnTopHint |
                           Qt.WindowType.BypassWindowManagerHint)
        self.showFullScreen()
        self.setStyleSheet("background-color: black;")
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.clock_container = QWidget()
        clock_layout = QHBoxLayout(self.clock_container)
        clock_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        clock_layout.setSpacing(10)
        
        self.hour1_label = QLabel()
        self.hour2_label = QLabel()
        self.colon_label = QLabel(":")
        self.minute1_label = QLabel()
        self.minute2_label = QLabel()
        
        for label in [self.hour1_label, self.hour2_label, self.minute1_label, self.minute2_label]:
            label.setStyleSheet("""
                background-color: #1a1a1a;
                color: white;
                border-radius: 15px;
                padding: 30px;
            """)
            label.setFont(QFont(self.font_name, 120, QFont.Weight.Bold))
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setFixedSize(180, 220)
            clock_layout.addWidget(label)
        
        self.colon_label.setStyleSheet("color: white; background-color: transparent;")
        self.colon_label.setFont(QFont(self.font_name, 80, QFont.Weight.Bold))
        self.colon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.colon_label.setFixedSize(50, 220)
        clock_layout.addWidget(self.colon_label)
        
        layout.addWidget(self.clock_container)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)
        self.update_time()

    def update_time(self):
        now = datetime.now()
        time_str = now.strftime("%H:%M")
        hours = time_str[:2]
        minutes = time_str[3:]
        
        self.hour1_label.setText(hours[0])
        self.hour2_label.setText(hours[1])
        self.minute1_label.setText(minutes[0])
        self.minute2_label.setText(minutes[1])

    def keyPressEvent(self, event): self.close()
    def mouseMoveEvent(self, event): self.close()
    def mousePressEvent(self, event): self.close()

class ClockDateSaver(DigitalClockSaver):
    def __init__(self, font_name="Segoe UI", font_size=150, language="en"):
        super().__init__(font_name, font_size, language)
        
    def setupUI(self):
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | 
                           Qt.WindowType.WindowStaysOnTopHint |
                           Qt.WindowType.BypassWindowManagerHint)
        self.showFullScreen()
        self.setStyleSheet("background-color: black;")
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.clock_label = QLabel()
        self.clock_label.setFont(QFont(self.font_name, self.font_size, QFont.Weight.Bold))
        self.clock_label.setStyleSheet("color: white;")
        layout.addWidget(self.clock_label)

        self.date_label = QLabel()
        self.date_label.setFont(QFont("Segoe UI", 40))
        self.date_label.setStyleSheet("color: white;")
        layout.addWidget(self.date_label)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)
        self.update_time()

    def update_time(self):
        now = datetime.now()
        self.clock_label.setText(now.strftime("%H:%M"))
        
        lang_data = LANGUAGES.get(self.language, LANGUAGES["en"])
        day_name = lang_data["days"][now.weekday()]
        month_name = lang_data["months"][now.month - 1]
        self.date_label.setText(f"{day_name} {now.day} {month_name}")

class ClockCalendarSaver(QWidget):
    def __init__(self, font_name="Segoe UI", font_size=100, language="en"):
        super().__init__()
        self.font_name = font_name
        self.font_size = font_size
        self.language = language
        self.setupUI()
        self.setCursor(Qt.CursorShape.BlankCursor)

    def setupUI(self):
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | 
                           Qt.WindowType.WindowStaysOnTopHint |
                           Qt.WindowType.BypassWindowManagerHint)
        self.showFullScreen()
        self.setStyleSheet("background-color: black;")
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(40)

        self.clock_label = QLabel()
        self.clock_label.setFont(QFont(self.font_name, self.font_size, QFont.Weight.Bold))
        self.clock_label.setStyleSheet("color: white;")
        layout.addWidget(self.clock_label)

        self.calendar_widget = QWidget()
        self.calendar_layout = QGridLayout(self.calendar_widget)
        self.calendar_layout.setHorizontalSpacing(15)
        self.calendar_layout.setVerticalSpacing(10)
        self.calendar_widget.setFixedSize(450, 300)
        self.calendar_widget.setStyleSheet("""
            QWidget {
                background-color: rgba(0, 0, 0, 150);
                border-radius: 15px;
                border: 1px solid #333333;
            }
        """)
        layout.addWidget(self.calendar_widget)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)
        self.update_time()

    def update_time(self):
        now = datetime.now()
        self.clock_label.setText(now.strftime("%H:%M"))
        self.render_calendar(now.year, now.month, now.day)

    def render_calendar(self, year, month, current_day):
        for i in reversed(range(self.calendar_layout.count())): 
            widget = self.calendar_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        
        lang_data = LANGUAGES.get(self.language, LANGUAGES["en"])
        days = lang_data["days"]
        for i, day in enumerate(days):
            label = QLabel(day)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
            if i == 6:  # Nedelja/Subota
                label.setStyleSheet("color: red;")
            else:
                label.setStyleSheet("color: white;")
            self.calendar_layout.addWidget(label, 0, i)
        
        cal = calendar.monthcalendar(year, month)
        today = datetime.now().day
        
        for week_num, week in enumerate(cal):
            for day_num, day in enumerate(week):
                if day != 0:
                    day_label = QLabel(str(day))
                    day_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    day_label.setFont(QFont("Segoe UI", 14))
                    
                    if day == today:
                        day_label.setStyleSheet("""
                            QLabel {
                                background-color: #333333;
                                color: white;
                                border-radius: 15px;
                                padding: 5px;
                            }
                        """)
                    elif day_num == 6:  # Nedelja/Subota
                        day_label.setStyleSheet("color: red;")
                    else:
                        day_label.setStyleSheet("color: white;")
                    
                    self.calendar_layout.addWidget(day_label, week_num + 1, day_num)

    def keyPressEvent(self, event): self.close()
    def mouseMoveEvent(self, event): self.close()
    def mousePressEvent(self, event): self.close()

# --- Settings window ---
class SettingsWindow(QMainWindow):
    def __init__(self, parent_app=None):
        super().__init__()
        self.parent_app = parent_app
        self.settings = QSettings("MojaFirma", "ScreenSaverApp")
        self.current_language = self.settings.value("language", "en")
        self.setWindowTitle(UI_TRANSLATIONS[self.current_language]["settings_title"])
        self.setFixedSize(400, 450)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        layout.addWidget(QLabel(UI_TRANSLATIONS[self.current_language]["select_screensaver"]))
        self.saver_box = QComboBox()
        self.saver_box.addItems(["Digitalni sat", "Flip Clock", "Sat + datum", "Sat + kalendar"])
        layout.addWidget(self.saver_box)

        layout.addWidget(QLabel(UI_TRANSLATIONS[self.current_language]["select_font"]))
        self.font_box = QComboBox()
        self.font_box.addItems(["Segoe UI", "Segoe UI Bold", "Runtoe", "Linetical", "Ultra Champion"])
        layout.addWidget(self.font_box)

        layout.addWidget(QLabel(UI_TRANSLATIONS[self.current_language]["idle_time"]))
        self.timeout_spin = QDoubleSpinBox()
        self.timeout_spin.setRange(0.1, 60.0)
        self.timeout_spin.setSingleStep(0.1)
        layout.addWidget(self.timeout_spin)

        self.audio_check = QCheckBox(UI_TRANSLATIONS[self.current_language]["disable_audio"])
        layout.addWidget(self.audio_check)

        self.autorun_check = QCheckBox(UI_TRANSLATIONS[self.current_language]["autostart"])
        layout.addWidget(self.autorun_check)

        layout.addWidget(QLabel("Select language:"))
        self.language_box = QComboBox()
        for lang_code, lang_data in LANGUAGES.items():
            self.language_box.addItem(f"{lang_data['flag']} {lang_data['name']}", lang_code)
        layout.addWidget(self.language_box)

        save_btn = QPushButton(UI_TRANSLATIONS[self.current_language]["save"])
        save_btn.clicked.connect(self.save_settings)
        layout.addWidget(save_btn)

        self.load_settings_values()
        
        # Postavi ikonicu aplikacije u title bar
        icon = QIcon("ikonica.ico")
        if not icon.isNull():
            self.setWindowIcon(icon)
            
        # Postavi ime aplikacije
        self.setWindowTitle("Nebris")

    def load_settings_values(self):
        """Učitava postavke u UI polja"""
        self.saver_box.setCurrentText(self.settings.value("saver", "Digitalni sat"))
        self.font_box.setCurrentText(self.settings.value("font", "Segoe UI"))
        self.timeout_spin.setValue(float(self.settings.value("timeout", 5)))
        self.audio_check.setChecked(self.settings.value("audio_block", "true") == "true")
        
        # Proveri Windows registry za trenutno stanje autostarta
        autorun_enabled = check_autostart()
        self.autorun_check.setChecked(autorun_enabled)
        
        # Postavi jezik
        current_lang = self.settings.value("language", "en")
        index = self.language_box.findData(current_lang)
        if index >= 0:
            self.language_box.setCurrentIndex(index)

    def save_settings(self):
        """Čuva postavke iz UI polja"""
        self.settings.setValue("saver", self.saver_box.currentText())
        self.settings.setValue("font", self.font_box.currentText())
        self.settings.setValue("timeout", self.timeout_spin.value())
        self.settings.setValue("audio_block", "true" if self.audio_check.isChecked() else "false")
        self.settings.setValue("language", self.language_box.currentData())
        
        # Podesi autostart u Windows registry
        set_autostart(self.autorun_check.isChecked())
        self.settings.setValue("autorun", "true" if self.autorun_check.isChecked() else "false")
        
        if self.parent_app:
            self.parent_app.load_settings()
            self.parent_app.update_ui_language()

    def closeEvent(self, event):
        self.hide()
        event.ignore()

# --- Main app ---
class ScreenSaverApp(QApplication):
    def __init__(self, argv):
        super().__init__(argv)
        self.setQuitOnLastWindowClosed(False)
        
        # Proveri da li je aplikacija pokrenuta sa --minimized argumentom
        self.start_minimized = "--minimized" in argv
        
        # Koristi lightweight QSettings
        self.settings = QSettings("MojaFirma", "ScreenSaverApp")
        
        # Učitaj postavke
        self.load_settings()
        
        # Setup audio metar samo ako je potrebno
        self.audio_meter = None
        if AUDIO_DETECTION_AVAILABLE and self.audio_block:
            self.setup_audio_meter()
        
        # Postavi timer za proveru idle vremena
        self.check_timer = QTimer()
        self.check_timer.timeout.connect(self.check_idle)
        self.check_timer.start(2000)
        
        self.screensaver = None
        self.settings_window = None
        
        # Kreiraj tray icon (premešteno posle definisanja svih metoda)
        self.setup_tray()
        
        # Ako je startovan minimized, ne prikazuj settings prozor
        if self.start_minimized:
            print("Aplikacija startovana u pozadinskom režimu")
        else:
            self.show_settings()

    def update_ui_language(self):
        """Ažurira UI jezik za sve otvorene prozore"""
        if self.settings_window:
            self.settings_window.close()
            self.settings_window = None
            
        # Ukloni staru tray ikonicu pre nego što napraviš novu
        if hasattr(self, 'tray_icon'):
            self.tray_icon.hide()
            self.tray_icon.deleteLater()
            del self.tray_icon
            
        if hasattr(self, 'tray_icon_menu'):
            self.tray_icon_menu.deleteLater()
            del self.tray_icon_menu
            
        self.setup_tray()

    def show_settings(self):
        """Optimizovano prikazivanje settings prozora"""
        if not self.settings_window:
            self.settings_window = SettingsWindow(self)
        
        # Učitaj trenutna podešavanja u settings prozor
        self.settings_window.load_settings_values()
        self.settings_window.show()
        self.settings_window.activateWindow()

    def setup_tray(self):
        """Optimizovani setup system tray ikone"""
        icon = QIcon("ikonica.ico")
        if icon.isNull():
            icon = self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
        
        self.tray_icon = QSystemTrayIcon(icon, self)
        
        # Lightweight kontekstni meni
        self.tray_icon_menu = QMenu()
        current_lang = self.settings.value("language", "en")
        translations = UI_TRANSLATIONS.get(current_lang, UI_TRANSLATIONS["en"])
        
        open_action = QAction(translations["open_settings"], self)
        quit_action = QAction(translations["exit"], self)
        open_action.triggered.connect(self.show_settings)
        quit_action.triggered.connect(self.cleanup_and_quit)
        self.tray_icon_menu.addAction(open_action)
        self.tray_icon_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(self.tray_icon_menu)
        self.tray_icon.show()

    def load_settings(self):
        """Efikasno učitavanje postavki"""
        self.saver_type = self.settings.value("saver", "Digitalni sat")
        self.font_name = self.settings.value("font", "Segoe UI")
        self.timeout = float(self.settings.value("timeout", 5)) * 60  # Konvertuj u sekunde
        self.audio_block = self.settings.value("audio_block", "true") == "true"
        self.language = self.settings.value("language", "en")
        
        # Proveri Windows registry za trenutno stanje autostarta
        self.autorun = check_autostart()

    def cleanup_and_quit(self):
        """Čišćenje pre izlaska"""
        # Ukloni tray ikonicu
        if hasattr(self, 'tray_icon'):
            self.tray_icon.hide()
            self.tray_icon.deleteLater()
            
        if hasattr(self, 'tray_icon_menu'):
            self.tray_icon_menu.deleteLater()
        
        # Ostali deo metode ostaje isti
        if self.screensaver:
            self.screensaver.deleteLater()
            self.screensaver = None
        
        if self.audio_meter:
            self.audio_meter = None
            
        self.quit()

    def check_idle(self):
        """Optimizovana provera idle vremena"""
        if self.is_audio_playing():
            return
            
        idle_time = get_idle_duration()
        
        if idle_time >= self.timeout:
            if not self.screensaver or not self.screensaver.isVisible():
                self.launch_screensaver()
        elif self.screensaver and self.screensaver.isVisible():
            self.screensaver.close()
            self.screensaver.deleteLater()
            self.screensaver = None

    def launch_screensaver(self):
        """Optimizovano pokretanje screensaver-a"""
        # Koristi istu instancu ako je moguće
        if self.screensaver and self.screensaver.isVisible():
            return
            
        if self.screensaver:
            self.screensaver.deleteLater()
            
        if self.saver_type == "Digitalni sat":
            self.screensaver = DigitalClockSaver(self.font_name, 180, self.language)
        elif self.saver_type == "Flip Clock":
            self.screensaver = FlipClockSaver(self.font_name, self.language)
        elif self.saver_type == "Sat + datum":
            self.screensaver = ClockDateSaver(self.font_name, 150, self.language)
        elif self.saver_type == "Sat + kalendar":
            self.screensaver = ClockCalendarSaver(self.font_name, 100, self.language)
            
        self.screensaver.showFullScreen()

    def setup_audio_meter(self):
        """Optimizovani setup audio metra"""
        if not AUDIO_DETECTION_AVAILABLE:
            return
            
        try:
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(
                IAudioMeterInformation._iid_, CLSCTX_ALL, None)
            self.audio_meter = cast(interface, POINTER(IAudioMeterInformation))
        except Exception as e:
            print(f"Greška pri inicijalizaciji audio metra: {e}")
            self.audio_meter = None

    def is_audio_playing(self):
        """Optimizovana provera audio playback-a"""
        if not self.audio_block or not self.audio_meter:
            return False
            
        try:
            # Povećana preciznost detekcije
            peak_value = self.audio_meter.GetPeakValue()
            return peak_value > 0.01  # Smanjen prag za bolju detekciju
        except Exception as e:
            print(f"Greška pri audio detekciji: {e}")
            return False

# --- Main ---
if __name__ == "__main__":
    app = ScreenSaverApp(sys.argv)
    sys.exit(app.exec())
