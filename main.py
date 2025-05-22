import tkinter as tk
from PIL import Image, ImageTk
from win32gui import GetWindowLong, SetWindowLong, SetLayeredWindowAttributes
from win32con import WS_EX_LAYERED, WS_EX_TRANSPARENT, GWL_EXSTYLE
import keyboard
import mouse
import threading
import screeninfo

class InputOverlay:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Прозрачная накладка")
        self.root.geometry("800x300")  # Размер окна под длинный коврик
        self.root.attributes("-topmost", True)  # Окно всегда сверху
        self.root.attributes("-alpha", 0.8)  # Прозрачность
        self.root.configure(bg='black')

        # Делаем окно прозрачным для кликов
        hwnd = self.root.winfo_id()
        ex_style = GetWindowLong(hwnd, GWL_EXSTYLE)
        SetWindowLong(hwnd, GWL_EXSTYLE, ex_style | WS_EX_LAYERED | WS_EX_TRANSPARENT)
        SetLayeredWindowAttributes(hwnd, 0, int(255 * 0.8), 2)

        # Получаем размеры экрана
        screen = screeninfo.get_monitors()[0]
        self.screen_width = screen.width
        self.screen_height = screen.height

        # Создаем канвас для отображения элементов
        self.canvas = tk.Canvas(self.root, width=800, height=300, bg='black', highlightthickness=0)
        self.canvas.pack()

        # Заглушка для коврика (замените на PNG)
        self.mousepad = self.canvas.create_rectangle(50, 100, 750, 250, fill='gray', outline='')

        # Заглушка для персонажа (замените на PNG)
        self.character = self.canvas.create_oval(50, 50, 100, 100, fill='blue', outline='')

        # Заглушка для клавиатуры (замените на PNG)
        self.keyboard_img = self.canvas.create_rectangle(150, 150, 350, 200, fill='white', outline='')
        self.key_highlight = None  # Для подсветки клавиш

        # Заглушка для мыши (замените на PNG)
        self.mouse_img = self.canvas.create_oval(400, 175, 420, 195, fill='red', outline='')

        # Храним последние нажатые клавиши
        self.pressed_keys = []
        self.running = True

        # Запускаем отслеживание ввода
        self.keyboard_thread = threading.Thread(target=self.track_keyboard)
        self.mouse_thread = threading.Thread(target=self.track_mouse)
        self.keyboard_thread.daemon = True
        self.mouse_thread.daemon = True
        self.keyboard_thread.start()
        self.mouse_thread.start()

        # Запускаем обновление
        self.update_display()

    def track_keyboard(self):
        while self.running:
            event = keyboard.read_event(suppress=True)
            if event.event_type == keyboard.KEY_DOWN:
                if event.name not in self.pressed_keys:
                    self.pressed_keys.append(event.name)
                    if len(self.pressed_keys) > 3:  # Ограничим 3 клавиши
                        self.pressed_keys.pop(0)
            elif event.event_type == keyboard.KEY_UP:
                if event.name in self.pressed_keys:
                    self.pressed_keys.remove(event.name)

    def track_mouse(self):
        while self.running:
            pos = mouse.get_position()
            # Масштабируем позицию мыши на экране к координатам коврика (50,100 - 750,250)
            x = 50 + (pos[0] / self.screen_width) * (750 - 50)
            y = 100 + (pos[1] / self.screen_height) * (250 - 100)
            self.canvas.coords(self.mouse_img, x-10, y-10, x+10, y+10)
            for event in mouse.get_events():
                if isinstance(event, mouse.ButtonEvent) and event.event_type == "down":
                    self.pressed_keys.append(f"Клик: {event.button}")
                    if len(self.pressed_keys) > 3:
                        self.pressed_keys.pop(0)

    def update_display(self):
        # Обновляем подсветку клавиш
        if self.key_highlight:
            self.canvas.delete(self.key_highlight)
        if self.pressed_keys:
            # Подсвечиваем область клавиатуры при нажатии
            self.key_highlight = self.canvas.create_rectangle(150, 150, 350, 200, fill='yellow', outline='')
            self.canvas.tag_lower(self.key_highlight, self.keyboard_img)
            self.canvas.itemconfig(self.keyboard_img, fill='white')  # Возвращаем цвет после подсветки
        self.canvas.create_text(250, 125, text=" | ".join(self.pressed_keys), fill='white', font=("Arial", 12))
        self.root.after(100, self.update_display)

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