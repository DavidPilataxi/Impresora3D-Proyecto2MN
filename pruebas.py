import tkinter as tk
import os
import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from matplotlib.path import Path  # Para verificar si un punto está dentro del polígono
from tkinter import messagebox


def punto_en_poligono(path, punto, tolerancia=1e-2):
    """Verifica si un punto está dentro o en el borde del polígono con un margen de tolerancia."""
    if path.contains_point(punto) or path.contains_points([punto])[0]:
        return True
    for vertice in path.vertices:
        if np.linalg.norm(np.array(punto) - np.array(vertice)) < tolerancia:
            return True
    return False


class Impresora3DSimulada:

    def __init__(self, root):
        self.root = root
        self.root.title("Simulación de Impresora 3D")
        self.root.protocol("WM_DELETE_WINDOW", self.cerrar_programa)
        self.root.resizable(False, False)
        self.centrar_ventana()

        # Inicializar lista de botones antes de cargar los modelos
        self.botones_modelos = []

        # Botones para cargar archivos SVG disponibles
        self.lbl_seleccion = tk.Label(root, text="Seleccionar Modelo SVG:")
        self.lbl_seleccion.pack()
        self.frame_modelos = tk.Frame(root)
        self.frame_modelos.pack()
        self.cargar_botones_modelos()

        # Campos de entrada para resolución
        self.lbl_resolucion_x = tk.Label(root, text="Resolución horizontal:")
        self.lbl_resolucion_x.pack()
        self.entry_resolucion_x = tk.Entry(root)
        self.entry_resolucion_x.pack()

        self.lbl_resolucion_y = tk.Label(root, text="Resolución vertical:")
        self.lbl_resolucion_y.pack()
        self.entry_resolucion_y = tk.Entry(root)
        self.entry_resolucion_y.pack()

        # Cursor para velocidad de impresión
        self.lbl_velocidad = tk.Label(root, text="Velocidad de impresión:")
        self.lbl_velocidad.pack()
        self.slider_velocidad = tk.Scale(root,from_=0,to=100,orient="horizontal")
        self.slider_velocidad.set(50)
        self.slider_velocidad.pack()

        # Botón para iniciar la impresión
        self.btn_imprimir = tk.Button(root,
                                      text="Iniciar Impresión",
                                      command=self.iniciar_impresion)
        self.btn_imprimir.pack()

        # Botón para reiniciar la simulación
        self.btn_reiniciar = tk.Button(root,
                                       text="Reiniciar Simulación",
                                       command=self.reiniciar_simulacion)
        self.btn_reiniciar.pack()

        # Área de visualización
        self.fig, self.ax = plt.subplots(figsize=(6, 6))
        self.canvas = FigureCanvasTkAgg(self.fig, master=root)
        self.canvas.get_tk_widget().pack()

        self.puntos = []
        self.trayectoria = []
        self.index_imprimir = 0
        self.incremento_puntos = 10
        self.botones_modelos = []

    def centrar_ventana(self):
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 12) - (height // 10)
        self.root.geometry(f'+{x}+{y}')

    def cargar_botones_modelos(self):
        """Cargar los modelos SVG disponibles en la interfaz como botones."""
        carpeta_modelos = "models"
        if not os.path.exists(carpeta_modelos):
            os.makedirs(carpeta_modelos)
        archivos_svg = [
            f for f in os.listdir(carpeta_modelos) if f.endswith(".svg")
        ]

        for archivo in archivos_svg:
            btn_modelo = tk.Button(self.frame_modelos,
                                   text=archivo,
                                   command=lambda f=archivo: self.procesar_svg(
                                       os.path.join(carpeta_modelos, f)))
            btn_modelo.pack()
            self.botones_modelos.append(btn_modelo)

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
            self.puntos.append(self.puntos[0])
            self.dibujar_modelo()

    def dibujar_modelo(self):
        self.ax.clear()
        x_vals, y_vals = zip(*self.puntos)
        self.ax.plot(x_vals, y_vals, 'bo-', markersize=4)
        self.ax.set_title("Modelo Cargado")
        self.canvas.draw()

    def generar_trayectoria(self):
        if not self.puntos:
            return
        poligono_path = Path(self.puntos)
        res_x = float(self.entry_resolucion_x.get() or 1)
        res_y = float(self.entry_resolucion_y.get() or 1)

        min_x, max_x = min(p[0]
                           for p in self.puntos), max(p[0]
                                                      for p in self.puntos)
        min_y, max_y = min(p[1]
                           for p in self.puntos), max(p[1]
                                                      for p in self.puntos)

        self.trayectoria = []
        reverse = False
        for x in np.arange(min_x, max_x, res_x):
            y_values = np.arange(min_y, max_y, res_y)
            if reverse:
                y_values = y_values[::-1]
            reverse = not reverse
            for y in y_values:
                if punto_en_poligono(poligono_path, (x, y)):
                    self.trayectoria.append((x, y))

    def iniciar_impresion(self):
        if not self.puntos or not self.entry_resolucion_x.get(
        ) or not self.entry_resolucion_y.get():
            messagebox.showerror(
                "Error", "Falta cargar un modelo o definir la resolución")
            return

        self.btn_imprimir.config(state=tk.DISABLED)
        for btn in self.botones_modelos:
            btn.config(state=tk.DISABLED)
        self.entry_resolucion_x.config(state=tk.DISABLED)
        self.entry_resolucion_y.config(state=tk.DISABLED)
        self.slider_velocidad.config(state=tk.DISABLED)

        self.generar_trayectoria()
        self.index_imprimir = 0
        self.ax.clear()
        self.dibujar_modelo()
        self.ax.set_title("Simulación de Impresión")
        self.imprimir_paso()

    def reiniciar_simulacion(self):
        self.ax.clear()
        self.canvas.draw()
        self.puntos = []
        self.trayectoria = []
        self.btn_imprimir.config(state=tk.NORMAL)
        for btn in self.botones_modelos:
            btn.config(state=tk.NORMAL)
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

    def cerrar_programa(self):
        self.root.quit()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = Impresora3DSimulada(root)
    root.mainloop()
