import tkinter as tk
import os
import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from matplotlib.path import Path
from tkinter import messagebox
from tkinter import filedialog
from PIL import Image, ImageTk


def punto_en_poligono(path, punto, tolerancia=1e-2):
    """
    Verifica si un punto está dentro del polígono o en su contorno
    """
    if path.contains_point(punto):
        return True

    vertices = path.vertices
    for i in range(len(vertices) - 1):
        p1 = vertices[i]
        p2 = vertices[i + 1]
        if punto_en_segmento(p1, p2, punto, tolerancia):
            return True
    return False


def punto_en_segmento(p1, p2, p, tolerancia=1e-2):
    """
    Verifica si el punto p está sobre el segmento de línea entre p1 y p2.
    """
    p1 = np.array(p1)
    p2 = np.array(p2)
    p = np.array(p)

    segmento = p2 - p1
    punto_a_p1 = p - p1

    longitud_segmento_sq = np.dot(segmento, segmento)

    if longitud_segmento_sq == 0:
        return np.linalg.norm(punto_a_p1) < tolerancia

    t = np.dot(punto_a_p1, segmento) / longitud_segmento_sq

    if t < 0 or t > 1:
        return False

    proyeccion = p1 + t * segmento
    return np.linalg.norm(p - proyeccion) < tolerancia


class Impresora3DSimulada:

    def __init__(self, root):
        self.root = root
        self.root.title("Simulación de Impresora 3D")
        self.root.protocol("WM_DELETE_WINDOW", self.cerrar_programa)
        self.root.resizable(False, False)
        self.centrar_ventana()

        # Fondo degradado
        self.canvas_bg = tk.Canvas(root, width=800, height=600)
        self.canvas_bg.pack(fill="both", expand=True)
        self.canvas_bg.create_rectangle(0,
                                        0,
                                        800,
                                        600,
                                        fill="#FFC0CB",
                                        outline="")

        # Título y logo
        self.frame_titulo = tk.Frame(self.canvas_bg, bg="#FFC0CB")
        self.frame_titulo.pack(pady=10)

        original_logo = Image.open("Img/EPN_logo_big.png")
        resized_logo = original_logo.resize((80, 50), Image.LANCZOS)
        self.logo = ImageTk.PhotoImage(resized_logo)

        self.lbl_logo = tk.Label(self.frame_titulo,
                                 image=self.logo,
                                 bg="#FFC0CB")
        self.lbl_logo.pack(side="left")

        self.lbl_titulo = tk.Label(self.frame_titulo,
                                   text="Impresora 3D",
                                   font=("Tahoma", 20, "bold"),
                                   bg="#FFC0CB")
        self.lbl_titulo.pack(side="left", padx=10)

        # Botones para cargar archivos SVG
        self.lbl_seleccion = tk.Label(self.canvas_bg,
                                      text="Seleccionar Modelo SVG:",
                                      font=("Helvetica", 12, "bold"),
                                      bg="#FFC0CB")
        self.lbl_seleccion.pack()

        self.frame_modelos = tk.Frame(self.canvas_bg, bg="#FFC0CB")
        self.frame_modelos.pack()

        btn_modelo = tk.Button(self.frame_modelos,
                               text="Cargar archivo SVG",
                               font=("Helvetica", 10),
                               bg="#FFFFFF",
                               fg="#000000",
                               command=self.seleccionar_archivo_svg)
        btn_modelo.pack()

        # Campos de entrada para resolución
        self.lbl_resolucion_x = tk.Label(self.canvas_bg,
                                         text="Resolución horizontal:",
                                         font=("Helvetica", 12, "bold"),
                                         bg="#FFC0CB")
        self.lbl_resolucion_x.pack()

        self.entry_resolucion_x = tk.Entry(self.canvas_bg,
                                           font=("Helvetica", 10))
        self.entry_resolucion_x.pack()

        self.lbl_resolucion_y = tk.Label(self.canvas_bg,
                                         text="Resolución vertical:",
                                         font=("Helvetica", 12, "bold"),
                                         bg="#FFC0CB")
        self.lbl_resolucion_y.pack()

        self.entry_resolucion_y = tk.Entry(self.canvas_bg,
                                           font=("Helvetica", 10))
        self.entry_resolucion_y.pack()

        # Control de velocidad
        self.lbl_velocidad = tk.Label(self.canvas_bg,
                                      text="Velocidad de impresión:",
                                      font=("Helvetica", 12, "bold"),
                                      bg="#FFC0CB")
        self.lbl_velocidad.pack()

        self.slider_velocidad = tk.Scale(self.canvas_bg,
                                         from_=1,
                                         to=100,
                                         orient="horizontal",
                                         font=("Helvetica", 10),
                                         bg="#FFFFFF")
        self.slider_velocidad.set(50)
        self.slider_velocidad.pack()

        # Botones de control
        self.btn_imprimir = tk.Button(self.canvas_bg,
                                      text="Iniciar Impresión",
                                      font=("Helvetica", 12),
                                      bg="#FFFFFF",
                                      fg="#000000",
                                      command=self.iniciar_impresion)
        self.btn_imprimir.pack()

        self.btn_reiniciar = tk.Button(self.canvas_bg,
                                       text="Reiniciar Simulación",
                                       font=("Helvetica", 12),
                                       bg="#FFFFFF",
                                       fg="#000000",
                                       command=self.reiniciar_simulacion)
        self.btn_reiniciar.pack()

        # Área de visualización
        self.fig, self.ax = plt.subplots(figsize=(6, 6))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.canvas_bg)
        self.canvas.get_tk_widget().pack()

        # Variables de control
        self.puntos = []
        self.trayectoria = []
        self.index_imprimir = 0
        self.incremento_puntos = 10
        self.poligono_path = None

    def centrar_ventana(self):
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 15) - (height // 10)
        self.root.geometry(f'+{x}+{y}')

    def seleccionar_archivo_svg(self):
        default_dir = os.path.join(os.getcwd(), "models")
        if not os.path.exists(default_dir):
            os.makedirs(default_dir)
        file_path = filedialog.askopenfilename(initialdir=default_dir,
                                               filetypes=[("Archivos SVG",
                                                           "*.svg")])
        if file_path:
            self.procesar_svg(file_path)

    def procesar_svg(self, file_path):
        tree = ET.parse(file_path)
        root = tree.getroot()
        namespace = {"svg": "http://www.w3.org/2000/svg"}

        self.puntos = []
        for polygon in root.findall(".//svg:polygon", namespace):
            points_str = polygon.get("points")
            if points_str:
                coords = list(map(float, points_str.replace(',', ' ').split()))
                self.puntos = [(coords[i], coords[i + 1])
                               for i in range(0, len(coords), 2)]

        if self.puntos:
            if self.puntos[0] != self.puntos[-1]:
                self.puntos.append(self.puntos[0])
            self.poligono_path = Path(self.puntos)
            self.dibujar_modelo()

    def dibujar_modelo(self):
        self.ax.clear()
        x_vals, y_vals = zip(*self.puntos)
        self.ax.plot(x_vals, y_vals, 'bo-', markersize=4)
        self.ax.set_title("Modelo Cargado", fontweight="bold")
        self.canvas.draw()

    def generar_trayectoria(self):
        if not self.puntos or not self.poligono_path:
            return

        try:
            res_x = float(self.entry_resolucion_x.get() or 1)
            res_y = float(self.entry_resolucion_y.get() or 1)
        except ValueError:
            messagebox.showerror("Error",
                                 "Las resoluciones deben ser números válidos")
            return

        min_x = min(p[0] for p in self.puntos)
        max_x = max(p[0] for p in self.puntos)
        min_y = min(p[1] for p in self.puntos)
        max_y = max(p[1] for p in self.puntos)

        self.trayectoria = []
        reverse = False

        for x in np.arange(min_x, max_x + res_x, res_x):
            y_values = np.arange(min_y, max_y + res_y, res_y)
            if reverse:
                y_values = y_values[::-1]

            for y in y_values:
                punto = (x, y)
                if punto_en_poligono(self.poligono_path, punto):
                    self.trayectoria.append(punto)

            reverse = not reverse

    def iniciar_impresion(self):
        if not self.puntos or not self.entry_resolucion_x.get(
        ) or not self.entry_resolucion_y.get():
            messagebox.showerror(
                "Error", "Falta cargar un modelo o definir la resolución")
            return

        # Deshabilitar controles durante la impresión
        self.btn_imprimir.config(state=tk.DISABLED)
        self.entry_resolucion_x.config(state=tk.DISABLED)
        self.entry_resolucion_y.config(state=tk.DISABLED)
        self.slider_velocidad.config(state=tk.DISABLED)

        self.generar_trayectoria()
        self.index_imprimir = 0
        self.ax.clear()
        self.dibujar_modelo()
        self.ax.set_title("Simulación de Impresión", fontweight="bold")
        self.imprimir_paso()

    def reiniciar_simulacion(self):
        self.ax.clear()
        self.canvas.draw()
        self.puntos = []
        self.trayectoria = []
        self.poligono_path = None

        # Habilitar controles
        self.btn_imprimir.config(state=tk.NORMAL)
        self.entry_resolucion_x.config(state=tk.NORMAL)
        self.entry_resolucion_y.config(state=tk.NORMAL)
        self.slider_velocidad.config(state=tk.NORMAL)

    def imprimir_paso(self):
        if self.index_imprimir < len(self.trayectoria):
            incremento = self.incremento_puntos
            x_vals, y_vals = zip(*self.trayectoria[:self.index_imprimir +
                                                   incremento])
            self.ax.plot(x_vals, y_vals, 'r.', markersize=2)
            self.canvas.draw()
            self.index_imprimir += incremento
            velocidad = max(1, self.slider_velocidad.get())
            self.root.after(int(100 / velocidad), self.imprimir_paso)
        else:
            print("Impresión completada.")
            messagebox.showinfo("Información", "Impresión completada.")
            self.btn_imprimir.config(state=tk.NORMAL)
            self.entry_resolucion_x.config(state=tk.NORMAL)
            self.entry_resolucion_y.config(state=tk.NORMAL)
            self.slider_velocidad.config(state=tk.NORMAL)

    def cerrar_programa(self):
        self.root.quit()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = Impresora3DSimulada(root)
    root.mainloop()
