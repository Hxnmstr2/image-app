import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from PIL import Image, ImageTk, ImageDraw
import cv2
import numpy as np
import os

class ImageApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Обработка изображения")
        self.root.geometry("1000x800")

        self.current_image = None
        self.current_channel = tk.StringVar(value="RGB")
        self.cap = None
        self.camera_image_path = "temp_camera.jpg"
        self.display_scale = 1.0 

        self.create_widgets()

    def create_widgets(self):
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=10)

        # Кнопки действий
        tk.Button(button_frame, text="Загрузить изображение", command=self.load_image).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Сделать фото с камеры", command=self.capture_from_camera).pack(side=tk.LEFT, padx=5)

        processing_frame = tk.Frame(self.root)
        processing_frame.pack(pady=5)
        
        tk.Button(processing_frame, text="Обрезать", command=self.crop_image).pack(side=tk.LEFT, padx=5)
        tk.Button(processing_frame, text="Добавить границу", command=self.add_border).pack(side=tk.LEFT, padx=5)
        tk.Button(processing_frame, text="Нарисовать линию", command=self.draw_line).pack(side=tk.LEFT, padx=5)

        # Выбор канала
        channel_frame = tk.Frame(self.root)
        channel_frame.pack(pady=5)
        tk.Label(channel_frame, text="Выберите канал:").pack(side=tk.LEFT)
        tk.OptionMenu(channel_frame, self.current_channel, "RGB", "R", "G", "B", command=self.show_channel).pack(
            side=tk.LEFT, padx=5
        )

        # Метка для отображения изображения
        self.image_label = tk.Label(self.root)
        self.image_label.pack()

        # Отображение координат
        self.coordinates_label = tk.Label(self.root, text="Координаты: ")
        self.coordinates_label.pack(pady=5)
        self.image_label.bind("<Motion>", self.show_coordinates)

    def load_image(self):
        file_types = [("Изображения", "*.png *.jpg *.jpeg")]
        filename = filedialog.askopenfilename(filetypes=file_types)

        if filename:
            try:
                self.current_image = Image.open(filename).convert("RGB")
                self.show_image()
                messagebox.showinfo("Успех", "Изображение успешно загружено")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось загрузить изображение: {str(e)}")

    def capture_from_camera(self):
        self.cap = cv2.VideoCapture(0)
        
        if not self.cap.isOpened():
            msg = "Не удалось подключиться к веб-камере.\n\nВозможные решения:\n"
            msg += "1. Проверьте подключение камеры\n"
            msg += "2. Убедитесь, что другая программа не использует камеру\n"
            msg += "3. Проверьте разрешения в настройках безопасности системы"
            messagebox.showerror("Ошибка камеры", msg)
            return
        
        ret, frame = self.cap.read()
        if ret:
            cv2.imwrite(self.camera_image_path, frame)
            try:
                self.current_image = Image.open(self.camera_image_path).convert("RGB")
                self.show_image()
                messagebox.showinfo("Успех", "Фото успешно сделано")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось обработать снимок с камеры: {str(e)}")

        self.cap.release()
        self.cap = None

    def show_image(self):
        if self.current_image:
            display_image = self.current_image.copy()
            display_image.thumbnail((700, 500))
            self.tk_image = ImageTk.PhotoImage(display_image)
            self.image_label.config(image=self.tk_image)
            self.display_scale = min(700/self.current_image.width, 500/self.current_image.height)

    def show_channel(self, _=None):
        if not self.current_image:
            messagebox.showwarning("Предупреждение", "Сначала загрузите изображение или сделайте фото")
            return
        
        img_array = np.array(self.current_image)
        channel = self.current_channel.get()
        
        if channel == "R":
            result = np.zeros_like(img_array)
            result[:, :, 0] = img_array[:, :, 0]
        elif channel == "G":
            result = np.zeros_like(img_array)
            result[:, :, 1] = img_array[:, :, 1]
        elif channel == "B":
            result = np.zeros_like(img_array)
            result[:, :, 2] = img_array[:, :, 2]
        else:
            result = img_array
        
        result_image = Image.fromarray(result)
        result_image.thumbnail((700, 500))
        self.tk_image = ImageTk.PhotoImage(result_image)
        self.image_label.config(image=self.tk_image)

    def crop_image(self):
        if not self.current_image:
            messagebox.showwarning("Предупреждение", "Сначала загрузите изображение")
            return
        
        coords = []
        labels = ["X1", "Y1", "X2", "Y2"]
        
        for label in labels:
            value = simpledialog.askinteger("Обрезка", f"Введите {label}:")
            if value is None:
                return
            coords.append(value)
        
        x1, y1, x2, y2 = coords
        
        try:
            width, height = self.current_image.size
            if x1 >= x2 or y1 >= y2 or x2 > width or y2 > height:
                raise ValueError("Некорректные координаты")
            
            self.current_image = self.current_image.crop((x1, y1, x2, y2))
            self.show_image()
            messagebox.showinfo("Успех", "Изображение обрезано")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def add_border(self):
        if not self.current_image:
            messagebox.showwarning("Предупреждение", "Сначала загрузите изображение")
            return
        
        border_size = simpledialog.askinteger("Граница", "Введите размер границы (px):")
        if border_size is None:
            return
        
        try:
            if border_size <= 0:
                raise ValueError("Размер должен быть положительным")
            
            new_image = Image.new("RGB", 
                (self.current_image.width + 2*border_size, 
                 self.current_image.height + 2*border_size),
                (0, 0, 0)) 
            
            new_image.paste(self.current_image, (border_size, border_size))
            self.current_image = new_image
            self.show_image()
            messagebox.showinfo("Успех", "Граница добавлена")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def draw_line(self):
        if not self.current_image:
            messagebox.showwarning("Предупреждение", "Сначала загрузите изображение")
            return
        
        line_params = []
        labels = ["X1", "Y1", "X2", "Y2", "Толщина"]
        
        for label in labels:
            value = simpledialog.askinteger("Линия", f"Введите {label}:")
            if value is None:
                return
            line_params.append(value)
        
        x1, y1, x2, y2, thickness = line_params
        
        try:
            if thickness <= 0:
                raise ValueError("Толщина должна быть положительной")
            
            draw = ImageDraw.Draw(self.current_image)
            draw.line([(x1, y1), (x2, y2)], fill=(0, 255, 0), width=thickness)
            self.show_image()
            messagebox.showinfo("Успех", "Линия нарисована")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def show_coordinates(self, event):
        if self.current_image:

            original_x = int(event.x / self.display_scale)
            original_y = int(event.y / self.display_scale)
            self.coordinates_label.config(text=f"Координаты: X={original_x}, Y={original_y}")

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageApp(root)
    root.mainloop()
    
    if os.path.exists(app.camera_image_path):
        os.remove(app.camera_image_path)