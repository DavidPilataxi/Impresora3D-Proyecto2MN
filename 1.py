import tkinter as tk
from tkinter import filedialog
import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np


class Impresora3DSimulada:

    def __init__(self, root):
        self.root = root
        self.root.title("Simulación de Impresora 3D")
        self.root.protocol("WM_DELETE_WINDOW",
                           self.cerrar_programa)  # Manejo de cierre de ventana
        self.root.resizable(False, False)  # Bloquear redimensionamiento
        self.centrar_ventana()  # Centrar la ventana en la pantalla

        # Botón para cargar el archivo SVG
        self.btn_cargar = tk.Button(root,
                                    text="Cargar Modelo SVG",
                                    command=self.cargar_archivo)
        self.btn_cargar.pack()

        # Campos de entrada para resolución y velocidad
        self.lbl_resolucion = tk.Label(root, text="Resolución de impresión:")
        self.lbl_resolucion.pack()
        self.entry_resolucion = tk.Entry(root)
        self.entry_resolucion.pack()

        self.lbl_velocidad = tk.Label(root, text="Velocidad de impresión:")
        self.lbl_velocidad.pack()
        self.entry_velocidad = tk.Entry(root)
        self.entry_velocidad.pack()

        # Botón para iniciar la impresión
        self.btn_imprimir = tk.Button(root,
                                      text="Iniciar Impresión",
                                      command=self.iniciar_impresion)
        self.btn_imprimir.pack()

        # Área de visualización
        self.fig, self.ax = plt.subplots(figsize=(6, 6))
        self.canvas = FigureCanvasTkAgg(self.fig, master=root)
        self.canvas.get_tk_widget().pack()

        self.puntos = []
        self.trayectoria = []
        self.index_imprimir = 0
        self.incremento_puntos = 10  # Número de puntos a agregar en cada iteración

    def centrar_ventana(self):
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 4) - (
            height // 4)  # Elevar aún más la ventana
        self.root.geometry(f'+{x}+{y}')

    def cargar_archivo(self):
        file_path = filedialog.askopenfilename(
            initialdir="models",
            title="Seleccionar archivo SVG",
            filetypes=(("Archivos SVG", "*.svg"), ("Todos los archivos",
                                                   "*.*")))
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
            self.puntos.append(self.puntos[0])  # Asegurar cierre del polígono
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

        min_x = min(p[0] for p in self.puntos)
        max_x = max(p[0] for p in self.puntos)
        min_y = min(p[1] for p in self.puntos)
        max_y = max(p[1] for p in self.puntos)
        resolucion = float(self.entry_resolucion.get() or 1)

        self.trayectoria = []
        for x in np.arange(min_x, max_x, resolucion):  # Escaneo vertical
            intersecciones = []
            for i in range(len(self.puntos) - 1):
                x1, y1 = self.puntos[i]
                x2, y2 = self.puntos[i + 1]
                if (x1 <= x <= x2) or (x2 <= x <=
                                       x1):  # Intersección con la línea
                    if x1 != x2:
                        y_inter = y1 + (x - x1) * (y2 - y1) / (x2 - x1)
                        intersecciones.append(y_inter)

            intersecciones.sort()
            for i in range(0, len(intersecciones), 2):
                if i + 1 < len(intersecciones):
                    y_vals = np.arange(intersecciones[i],
                                       intersecciones[i + 1], resolucion)
                    for y in y_vals:
                        self.trayectoria.append((x, y))

    def iniciar_impresion(self):
        self.generar_trayectoria()
        self.index_imprimir = 0
        self.ax.clear()
        self.dibujar_modelo()
        self.ax.set_title("Simulación de Impresión")
        self.imprimir_paso()

    def imprimir_paso(self):
        if self.index_imprimir < len(self.trayectoria):
            incremento = self.incremento_puntos  # Número de puntos por iteración
            x_vals, y_vals = zip(*self.trayectoria[:self.index_imprimir +
                                                   incremento])
            self.ax.plot(x_vals, y_vals, 'r.', markersize=2)
            self.canvas.draw()
            self.index_imprimir += incremento
            velocidad = max(1, int(self.entry_velocidad.get() or 1))
            self.root.after(int(100 / velocidad),
                            self.imprimir_paso)  # Reducir delay mínimo
        else:
            print("Impresión completada.")

    def cerrar_programa(self):
        print("Cerrando programa...")
        self.root.quit()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = Impresora3DSimulada(root)
    root.mainloop()
