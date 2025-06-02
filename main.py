import tkinter as tk
from PIL import Image, ImageTk
from win32gui import GetWindowLong, SetWindowLong, SetLayeredWindowAttributes
from win32con import WS_EX_LAYERED, WS_EX_TRANSPARENT, GWL_EXSTYLE
import keyboard
import mouse
import threading
import screeninfo
import os
import json
import time

class InputOverlay:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Прозрачная накладка")
        self.root.geometry("1000x400")  # Большее окно для коврика и интерфейса
        self.root.attributes("-topmost", True)  # Окно всегда сверху
        self.root.attributes("-alpha", 0.8)  # Начальная прозрачность
        self.root.configure(bg='black')  # Черный фон для хромакея

        # Делаем окно прозрачным для кликов
        hwnd = self.root.winfo_id()
        ex_style = GetWindowLong(hwnd, GWL_EXSTYLE)
        SetWindowLong(hwnd, GWL_EXSTYLE, ex_style | WS_EX_LAYERED | WS_EX_TRANSPARENT)
        SetLayeredWindowAttributes(hwnd, 0, int(255 * 0.8), 2)

        # Получаем размеры экрана
        screen = screeninfo.get_monitors()[0]
        self.screen_width = screen.width
        self.screen_height = screen.height

        # Папка для пользовательских моделей
        self.models_dir = "models"
        os.makedirs(self.models_dir, exist_ok=True)

        # Загружаем изображения (замените на ваши PNG)
        try:
            self.mousepad_img = ImageTk.PhotoImage(Image.open(os.path.join(self.models_dir, "mousepad.png")).resize((800, 200)))
            self.character_img = ImageTk.PhotoImage(Image.open(os.path.join(self.models_dir, "character.png")).resize((150, 150)))
            self.keyboard_img = ImageTk.PhotoImage(Image.open(os.path.join(self.models_dir, "keyboard.png")).resize((300, 100)))
            self.mouse_img = ImageTk.PhotoImage(Image.open(os.path.join(self.models_dir, "mouse.png")).resize((30, 30)))
        except FileNotFoundError:
            self.mousepad_img = None
            self.character_img = None
            self.keyboard_img = None
            self.mouse_img = None

        # Создаем канвас
        self.canvas = tk.Canvas(self.root, width=1000, height=400, bg='black', highlightthickness=0)
        self.canvas.pack()

        # Коврик
        if self.mousepad_img:
            self.mousepad = self.canvas.create_image(100, 150, image=self.mousepad_img, anchor='nw')
        else:
            self.mousepad = self.canvas.create_rectangle(100, 150, 900, 350, fill='gray', outline='')

        # Персонаж
        if self.character_img:
            self.character = self.canvas.create_image(50, 50, image=self.character_img, anchor='nw')
        else:
            self.character = self.canvas.create_oval(50, 50, 150, 150, fill='blue', outline='')

        # Клавиатура
        if self.keyboard_img:
            self.keyboard = self.canvas.create_image(200, 250, image=self.keyboard_img, anchor='nw')
        else:
            self.keyboard = self.canvas.create_rectangle(200, 250, 500, 350, fill='white', outline='')
        self.key_highlight = None

        # Мышь
        if self.mouse_img:
            self.mouse = self.canvas.create_image(500, 250, image=self.mouse_img, anchor='center')
        else:
            self.mouse = self.canvas.create_oval(490, 240, 510, 260, fill='red', outline='')

        # Панель управления
        self.control_frame = tk.Frame(self.root, bg='black')
        self.control_frame.pack(side=tk.TOP, fill=tk.X)
        tk.Button(self.control_frame, text="Закрыть", command=self.stop, bg='red', fg='white').pack(side=tk.LEFT, padx=5)
        tk.Button(self.control_frame, text="Сохранить пресет", command=self.save_preset, bg='blue', fg='white').pack(side=tk.LEFT, padx=5)
        tk.Button(self.control_frame, text="Загрузить пресет", command=self.load_preset, bg='blue', fg='white').pack(side=tk.LEFT, padx=5)
        self.alpha_scale = tk.Scale(self.control_frame, from_=0.1, to=1.0, resolution=0.1, orient=tk.HORIZONTAL, label="Прозрачность", bg='black', fg='white', command=self.update_alpha)
        self.alpha_scale.set(0.8)
        self.alpha_scale.pack(side=tk.LEFT, padx=5)

        # Отображение KPS
        self.kps_label = tk.Label(self.control_frame, text="KPS: 0", bg='black', fg='white', font=("Arial", 12))
        self.kps_label.pack(side=tk.LEFT, padx=5)

        # Храним данные
        self.pressed_keys = []
        self.key_count = 0
        self.last_kps_time = time.time()
        self.running = True
        self.presets_file = "presets.json"

        # Запускаем отслеживание
        self.keyboard_thread = threading.Thread(target=self.track_keyboard)
        self.mouse_thread = threading.Thread(target=self.track_mouse)
        self.keyboard_thread.daemon = True
        self.mouse_thread.daemon = True
        self.keyboard_thread.start()
        self.mouse_thread.start()

        # Запускаем обновление
        self.update_display()

    def update_alpha(self, value):
        self.root.attributes("-alpha", float(value))
        hwnd = self.root.winfo_id()
        SetLayeredWindowAttributes(hwnd, 0, int(255 * float(value)), 2)

    def save_preset(self):
        preset = {
            "alpha": self.alpha_scale.get(),
            "window_pos": (self.root.winfo_x(), self.root.winfo_y()),
            "window_size": (self.root.winfo_width(), self.root.winfo_height())
        }
        try:
            with open(self.presets_file, 'w') as f:
                json.dump(preset, f)
        except Exception as e:
            print(f"Ошибка сохранения пресета: {e}")

    def load_preset(self):
        try:
            with open(self.presets_file, 'r') as f:
                preset = json.load(f)
            self.alpha_scale.set(preset["alpha"])
            self.root.geometry(f"{int(preset['window_size'][0])}x{int(preset['window_size'][1])}+{int(preset['window_pos'][0])}+{int(preset['window_pos'][1])}")
            self.update_alpha(preset["alpha"])
        except Exception as e:
            print(f"Ошибка загрузки пресета: {e}")

    def track_keyboard(self):
        while self.running:
            event = keyboard.read_event(suppress=True)
            if event.event_type == keyboard.KEY_DOWN:
                if event.name not in self.pressed_keys:
                    self.pressed_keys.append(event.name)
                    self.key_count += 1
                    if len(self.pressed_keys) > 5:
                        self.pressed_keys.pop(0)
            elif event.event_type == keyboard.KEY_UP:
                if event.name in self.pressed_keys:
                    self.pressed_keys.remove(event.name)

    def track_mouse(self):
        while self.running:
            pos = mouse.get_position()
            # Масштабируем координаты мыши к коврику (100,150 - 900,350)
            x = 100 + (pos[0] / self.screen_width) * (900 - 100)
            y = 150 + (pos[1] / self.screen_height) * (350 - 150)
            self.canvas.coords(self.mouse, x, y)
            for event in mouse.get_events():
                if isinstance(event, mouse.ButtonEvent) and event.event_type == "down":
                    self.pressed_keys.append(f"Клик: {event.button}")
                    if len(self.pressed_keys) > 5:
                        self.pressed_keys.pop(0)

    def update_display(self):
        # Обновляем подсветку клавиш
        if self.key_highlight:
            self.canvas.delete(self.key_highlight)
        if self.pressed_keys:
            self.key_highlight = self.canvas.create_rectangle(200, 250, 500, 350, fill='yellow', outline='')
            self.canvas.tag_lower(self.key_highlight, self.keyboard)
        self.canvas.create_text(350, 225, text=" | ".join(self.pressed_keys), fill='white', font=("Arial", 12))

        # Обновляем KPS
        current_time = time.time()
        if current_time - self.last_kps_time >= 1.0:
            kps = self.key_count
            self.key_count = 0
            self.last_kps_time = current_time
            self.kps_label.config(text=f"KPS: {kps}")

        self.root.after(50, self.update_display)

    def run(self):
        self.root.mainloop()

    def stop(self):
        self.running = False
        self.root.quit()

if __name__ == "__main__":
    overlay = InputOverlay()
    try:
        overlay.run()
    except KeyboardInterrupt:
        overlay.stop()