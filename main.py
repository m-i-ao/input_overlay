import tkinter as tk
from win32gui import GetWindowLong, SetWindowLong, SetLayeredWindowAttributes
from win32con import WS_EX_LAYERED, WS_EX_TRANSPARENT, GWL_EXSTYLE
import keyboard
import mouse
import threading

class InputOverlay:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Прозрачная накладка")
        self.root.geometry("400x200")
        self.root.attributes("-topmost", True)  # Окно всегда сверху
        self.root.attributes("-alpha", 0.7)     # Прозрачность (0.0 до 1.0)
        self.root.configure(bg='black')

        # Делаем окно "прозрачным" для кликов
        hwnd = self.root.winfo_id()
        ex_style = GetWindowLong(hwnd, GWL_EXSTYLE)
        SetWindowLong(hwnd, GWL_EXSTYLE, ex_style | WS_EX_LAYERED | WS_EX_TRANSPARENT)
        SetLayeredWindowAttributes(hwnd, 0, int(255 * 0.7), 2)  # Применяем прозрачность

        # Создаем метку для отображения событий ввода
        self.label = tk.Label(
            self.root,
            text="Нажимайте клавиши или двигайте/кликайте мышью...",
            font=("Arial", 12),
            fg="white",
            bg="black",
            wraplength=380
        )
        self.label.pack(pady=10)

        # Храним последние события ввода
        self.input_log = []

        # Запускаем отслеживание ввода в отдельных потоках
        self.running = True
        self.keyboard_thread = threading.Thread(target=self.track_keyboard)
        self.mouse_thread = threading.Thread(target=self.track_mouse)
        self.keyboard_thread.daemon = True
        self.mouse_thread.daemon = True
        self.keyboard_thread.start()
        self.mouse_thread.start()

        # Запускаем цикл обновления
        self.update_label()

    def track_keyboard(self):
        while self.running:
            event = keyboard.read_event(suppress=True)
            if event.event_type == keyboard.KEY_DOWN:
                self.input_log.append(f"Клавиша: {event.name}")
                if len(self.input_log) > 5:  # Ограничиваем лог до 5 записей
                    self.input_log.pop(0)

    def track_mouse(self):
        last_pos = mouse.get_position()
        while self.running:
            # Проверяем движение мыши
            current_pos = mouse.get_position()
            if current_pos != last_pos:
                self.input_log.append(f"Мышь перемещена в: {current_pos}")
                last_pos = current_pos
                if len(self.input_log) > 5:
                    self.input_log.pop(0)

            # Проверяем клики мыши
            for event in mouse.get_events():
                if isinstance(event, mouse.ButtonEvent):
                    if event.event_type == "down":
                        self.input_log.append(f"Клик мыши: {event.button}")
                        if len(self.input_log) > 5:
                            self.input_log.pop(0)

    def update_label(self):
        # Обновляем метку с последними событиями ввода
        self.label.config(text="\n".join(self.input_log))
        self.root.after(100, self.update_label)  # Обновление каждые 100 мс

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