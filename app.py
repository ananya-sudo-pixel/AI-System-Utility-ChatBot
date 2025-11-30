import sys
import psutil
import webbrowser
import subprocess
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTextEdit, QLineEdit, QLabel, QDialog, QGridLayout, QFrame
)
from PyQt5.QtCore import Qt, QTimer, QPointF
from PyQt5.QtGui import QColor, QPainter, QPen, QBrush, QFont, QPainterPath
import math
import time

APP_COMMANDS = {
    "Notepad": "notepad.exe",
    "Paint": "mspaint.exe",
    "Calculator": "calc.exe",
    "File Explorer": "explorer.exe",
    "Copilot": ["msedge.exe", "https://copilot.microsoft.com/"],
    "ChatGPT": ["msedge.exe", "https://chat.openai.com/"],
    "Perplexity": ["msedge.exe", "https://www.perplexity.ai/"]
}

def get_system_info():
    cpu = f"CPU: {psutil.cpu_percent()}% ({psutil.cpu_count()} cores)"
    ram = psutil.virtual_memory()
    ram_info = f"RAM: {ram.percent}% used, {ram.total // (1024 ** 2)} MB total"
    disk = psutil.disk_usage('/')
    disk_info = f"Disk: {disk.percent}% used, {disk.free // (1024 ** 3)} GB free"
    battery = psutil.sensors_battery()
    batt_info = f"Battery: {battery.percent}% {'(Charging)' if battery.power_plugged else '(Discharging)'}" if battery else "Battery: Data unavailable"
    return f"{cpu}\n{ram_info}\n{disk_info}\n{batt_info}"

class SystemInfoDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("System Info")
        self.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0#dce9f9, stop:1#fefefe);")
        self.setFixedSize(380, 160)
        layout = QVBoxLayout()
        self.info_label = QLabel(get_system_info())
        self.info_label.setStyleSheet("font: 13pt 'Segoe UI'; color: #333; padding: 12px;")
        layout.addWidget(self.info_label)
        self.setLayout(layout)

    def update_info(self):
        self.info_label.setText(get_system_info())

class WaveBackground(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.offset = 0.0
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_offset)
        self.timer.start(20)

        self.waves = [
            {"amplitude": 20, "wavelength": 220, "speed": 0.03, "color": QColor(180, 210, 255, 70)},
            {"amplitude": 25, "wavelength": 150, "speed": 0.016, "color": QColor(135, 190, 230, 90)},
            {"amplitude": 30, "wavelength": 300, "speed": 0.01, "color": QColor(200, 230, 255, 60)},
        ]

    def update_offset(self):
        self.offset += 0.02
        if self.offset > 2 * math.pi:
            self.offset -= 2 * math.pi
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        rect = self.rect()
        painter.fillRect(rect, QColor(245, 250, 255))  # soft background base

        for wave in self.waves:
            path = QPainterPath()
            height = rect.height() / 2
            path.moveTo(0, rect.height())

            for x in range(rect.width() + 1):
                angle = (2 * math.pi / wave["wavelength"]) * x + self.offset * wave["speed"]
                y = height + wave["amplitude"] * math.sin(angle)
                path.lineTo(x, y)

            path.lineTo(rect.width(), rect.height())
            path.lineTo(0, rect.height())
            path.closeSubpath()

            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(wave["color"]))
            painter.drawPath(path)

class ChatBox(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                border-radius: 30px;
                background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1,
                                            stop:0 #e6f0ff, stop:1 #ffffff);
                border: 2px solid #a4c0f0;
                box-shadow: 0 7px 20px 5px rgba(132, 170, 255, 0.3);
            }
            QLabel#header {
                color: #254a81;
                font: 20pt 'Segoe UI'; font-weight: 700;
                margin: 15px 0 10px 0;
                letter-spacing: 1.3px;
            }
            QTextEdit {
                background: #f4f9ff;
                border-radius: 12px;
                border: 1px solid #b2cbff;
                font: 14pt 'Calibri';
                color: #254060;
            }
            QLineEdit {
                background: #eff7ff;
                border-radius: 12px;
                border: 1px solid #a6bee9;
                font: 14pt 'Segoe UI';
                padding: 8px;
                color: #30518e;
            }
            QPushButton {
                font: 15pt 'Segoe UI';
                background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1,
                                            stop:0 #a0bfff, stop:1 #5f81f7);
                color: #f0f3ff;
                margin: 10px 15px 10px 15px;
                border-radius: 24px;
                min-width: 160px;
                min-height: 50px;
                font-weight: 700;
                border: none;
            }
            QPushButton:hover {
                background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1,
                                            stop:0 #738fe7, stop:1 #2e4dad);
            }
        """)
        vlayout = QVBoxLayout()
        vlayout.setContentsMargins(40, 30, 40, 30)
        vlayout.setSpacing(18)

        header = QLabel("AI System Utility Chatbot")
        header.setAlignment(Qt.AlignCenter)
        header.setObjectName("header")
        vlayout.addWidget(header)

        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setFixedHeight(220)
        self.chat_display.setFixedWidth(520)
        vlayout.addWidget(self.chat_display, alignment=Qt.AlignCenter)

        entry_layout = QHBoxLayout()
        entry_layout.setAlignment(Qt.AlignCenter)
        self.chat_entry = QLineEdit()
        self.chat_entry.setFixedWidth(370)
        self.send_btn = QPushButton("Send")
        entry_layout.addWidget(self.chat_entry)
        entry_layout.addWidget(self.send_btn)

        vlayout.addLayout(entry_layout)
        self.setLayout(vlayout)
        self.setMaximumWidth(700)
        self.setMinimumWidth(500)

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI System Utility Chatbot")
        self.setGeometry(400, 120, 980, 700)

        self.bg = WaveBackground(self)
        self.bg.setGeometry(0, 0, 1920, 1080)

        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignCenter)
        main_layout.setSpacing(30)

        self.chat_box = ChatBox(self)
        main_layout.addStretch()
        main_layout.addWidget(self.chat_box, alignment=Qt.AlignCenter)
        main_layout.addSpacing(42)

        apps_grid = QGridLayout()
        apps_grid.setAlignment(Qt.AlignCenter)
        apps = ["Notepad", "Paint", "Calculator", "File Explorer", "Copilot", "ChatGPT", "Perplexity", "System Info"]
        btn_width, btn_height = 160, 60

        for i, app in enumerate(apps):
            btn = QPushButton(app)
            btn.setFixedWidth(btn_width)
            btn.setFixedHeight(btn_height)
            btn.setStyleSheet("""
                QPushButton {
                    border-radius: 28px;
                    background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1,
                                                stop:0 #5a7ef1, stop:1 #1e3fc2);
                    font-weight: 800;
                    font-size: 17px;
                    color: white;
                    margin: 10px;
                    box-shadow: 1px 3px 6px rgba(0, 0, 0, 0.3);
                }
                QPushButton:hover {
                    background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1,
                                                stop:0 #466cd9, stop:1 #15358f);
                }
            """)
            if app == "System Info":
                btn.clicked.connect(self.show_system_info)
            else:
                btn.clicked.connect(lambda checked, n=app: self.launch_app(n))
            apps_grid.addWidget(btn, i // 4, i % 4)

        main_layout.addLayout(apps_grid)
        main_layout.addSpacing(48)
        main_layout.addStretch()

        self.info_dialog = SystemInfoDialog(self)
        self.chat_box.send_btn.clicked.connect(self.process_command)

    def show_system_info(self):
        self.info_dialog.update_info()
        self.info_dialog.exec_()

    def launch_app(self, appname):
        try:
            cmd = APP_COMMANDS.get(appname)
            if cmd:
                if isinstance(cmd, list):
                    try:
                        subprocess.Popen([cmd[0], cmd[1]])
                    except Exception:
                        webbrowser.open(cmd[1])
                    self.post_message(f"Opening {appname} in browser...")
                else:
                    subprocess.Popen(cmd)
                    self.post_message(f"Opening {appname}...")
            else:
                self.post_message(f"App '{appname}' unsupported. (Check code)")
        except Exception as e:
            self.post_message(f"Failed to open {appname}: {e}")

    def process_command(self):
        msg = self.chat_box.chat_entry.text()
        self.chat_box.chat_entry.clear()
        if not msg:
            return
        self.post_message(f"You: {msg}")

        m = msg.lower().strip()
        if m in ["hi", "hello", "hey"]:
            self.post_message("Bot: Hello! How can I help you today?")
        elif m in ["bye", "exit", "goodbye", "close"]:
            self.post_message("Bot: Goodbye! Have a great day!")
            QApplication.quit()
        elif m in ["thanks", "thank you", "thankyou"]:
            self.post_message("Bot: You're welcome!")
        elif any(word in m for word in ["notepad", "note pad"]):
            self.launch_app("Notepad")
        elif "paint" in m:
            self.launch_app("Paint")
        elif "calc" in m or "calculator" in m:
            self.launch_app("Calculator")
        elif "file explorer" in m:
            self.launch_app("File Explorer")
        elif "copilot" in m:
            self.launch_app("Copilot")
        elif "chatgpt" in m:
            self.launch_app("ChatGPT")
        elif "perplexity" in m:
            self.launch_app("Perplexity")
        elif "system" in m or "info" in m or "pc" in m:
            self.show_system_info()
        else:
            self.post_message("Bot: I'm here to help! Try commands like 'open notepad', 'system info', or just say 'hi'.")

    def post_message(self, msg):
        self.chat_box.chat_display.append(msg)

    def resizeEvent(self, event):
        self.bg.setGeometry(self.rect())

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
