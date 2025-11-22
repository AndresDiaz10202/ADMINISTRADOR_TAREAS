"""
main.py - Administrador de Tareas Multiplataforma Optimizado
Requiere: pip install customtkinter psutil
Compatible: Windows, Linux, macOS
"""

import customtkinter as ctk
from tkinter import messagebox, filedialog
from system_monitor import SystemMonitor, ProcessInfo
import platform
import psutil
import time
import json
import csv
from datetime import datetime
from typing import List, Dict

# Configuración de tema
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class TaskManagerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
    
        # Monitor del sistema
        self.monitor = SystemMonitor(update_interval=10.0)  # 10 SEGUNDOS
        
        # Configuración de la ventana
        os_name = platform.system()
        self.title(f"⚡ Administrador de Tareas - {os_name}")
        self.geometry("1200x700")
        self.minsize(900, 600)
        
        # Variables de control
        self.selected_pid = None
        self.sort_column = "cpu"
        self.sort_reverse = True
        self._last_display_update = 0
        self._search_debounce_id = None  # Para debouncing de búsqueda

        # Historial para gráficos (últimos 30 valores)
        self.cpu_history = []
        self.ram_history = []
        self.max_history = 30

        # Control de auto-actualización
        self.auto_refresh_enabled = True
        
        # Grid principal
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Crear interfaz
        self._create_sidebar()
        self._create_header()
        self._create_process_table()
        self._create_control_panel()
        
        # Mostrar info del sistema
        self._display_system_info()
        
        # Registrar callback y iniciar monitor
        self.monitor.register_callback(self._on_monitor_update)
        self.monitor.start()
        
        # Protocolo de cierre
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

        # Detectar cuando la ventana está minimizada
        self.bind("<Unmap>", self._on_minimize)
        self.bind("<Map>", self._on_restore)
        self.is_minimized = False

        # Atajos de teclado
        self._setup_keyboard_shortcuts()

    def _on_minimize(self, event):
        """Pausar actualizaciones cuando se minimiza"""
        self.is_minimized = True

    def _on_restore(self, event):
        """Reanudar actualizaciones"""
        self.is_minimized = False

    def _setup_keyboard_shortcuts(self):
        """Configurar atajos de teclado"""
        # Ctrl+F - Enfocar búsqueda
        self.bind("<Control-f>", lambda e: self.search_entry.focus())
        self.bind("<Control-F>", lambda e: self.search_entry.focus())

        # Delete - Terminar proceso seleccionado
        self.bind("<Delete>", lambda e: self._kill_selected())

        # F5 - Actualizar manualmente
        self.bind("<F5>", lambda e: self._manual_refresh())

        # Escape - Limpiar selección y búsqueda
        self.bind("<Escape>", lambda e: self._clear_selection_and_search())

        # Ctrl+E - Exportar datos
        self.bind("<Control-e>", lambda e: self._export_data())
        self.bind("<Control-E>", lambda e: self._export_data())

        # Ctrl+Q - Salir
        self.bind("<Control-q>", lambda e: self._on_closing())
        self.bind("<Control-Q>", lambda e: self._on_closing())

    def _clear_selection_and_search(self):
        """Limpiar selección y búsqueda"""
        self.selected_pid = None
        self.search_var.set("")
        self.status_label.configure(text="✓ Selección limpiada")
        self._update_process_display()

    def _toggle_theme(self):
        """Cambiar entre tema oscuro y claro"""
        if self.theme_switch.get() == "dark":
            ctk.set_appearance_mode("dark")
            self.theme_switch.configure(text="🌙 Tema Oscuro")
        else:
            ctk.set_appearance_mode("light")
            self.theme_switch.configure(text="☀️ Tema Claro")

    def _toggle_auto_refresh(self):
        """Activar/desactivar auto-actualización"""
        self.auto_refresh_enabled = self.auto_refresh_switch.get()
        if self.auto_refresh_enabled:
            self.status_label.configure(text="✓ Auto-actualización activada")
        else:
            self.status_label.configure(text="⏸️ Auto-actualización pausada")

    def _update_ui_from_stats(self, stats: Dict):
        """Actualizar UI con las estadísticas (ejecutado en thread principal)"""
        # NO actualizar si está minimizada
        if self.is_minimized:
            return

        # Actualizar métricas siempre (sidebar)
        cpu = stats['cpu_percent']
        ram = stats['ram_percent']

        self.cpu_label.configure(text=f"CPU: {cpu:.1f}%")
        self.cpu_progress.set(cpu / 100)

        self.ram_label.configure(text=f"RAM: {ram:.1f}%")
        self.ram_progress.set(ram / 100)

        self.process_count_label.configure(text=f"Procesos: {stats['process_count']}")

        # Actualizar historial y gráficos
        self._update_history_graphs(cpu, ram)

        # Solo actualizar lista si auto-refresh está activado
        if self.auto_refresh_enabled:
            self._update_process_display()

    def _create_sidebar(self):
        """Panel lateral con métricas"""
        self.sidebar = ctk.CTkFrame(self, width=250, corner_radius=0)
        self.sidebar.grid(row=0, column=0, rowspan=3, sticky="nsew")
        self.sidebar.grid_rowconfigure(12, weight=1)
        
        # Logo con emoji de SO
        os_emoji = {
            'Windows': '🪟',
            'Linux': '🐧', 
            'Darwin': '🍎'
        }.get(platform.system(), '💻')
        
        self.logo_label = ctk.CTkLabel(
            self.sidebar,
            text=f"{os_emoji} Monitor",
            font=ctk.CTkFont(size=22, weight="bold")
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        
        self.subtitle = ctk.CTkLabel(
            self.sidebar,
            text=f"Sistema: {platform.system()}",
            font=ctk.CTkFont(size=12)
        )
        self.subtitle.grid(row=1, column=0, padx=20, pady=(0, 30))
        
        # CPU
        self.cpu_label = ctk.CTkLabel(
            self.sidebar,
            text="CPU: 0%",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.cpu_label.grid(row=2, column=0, padx=20, pady=(10, 5))
        
        self.cpu_progress = ctk.CTkProgressBar(self.sidebar, width=210)
        self.cpu_progress.grid(row=3, column=0, padx=20, pady=(0, 5))
        self.cpu_progress.set(0)

        # Gráfico de historial CPU mejorado
        cpu_graph_container = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        cpu_graph_container.grid(row=4, column=0, padx=20, pady=(0, 10), sticky="ew")

        ctk.CTkLabel(
            cpu_graph_container,
            text="Historial CPU",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        ).pack()

        self.cpu_graph_frame = ctk.CTkFrame(cpu_graph_container, height=60, fg_color="#0f172a", corner_radius=8)
        self.cpu_graph_frame.pack(fill="x", pady=(2, 0))
        self.cpu_bars = []

        # RAM
        self.ram_label = ctk.CTkLabel(
            self.sidebar,
            text="RAM: 0%",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.ram_label.grid(row=5, column=0, padx=20, pady=(10, 5))

        self.ram_progress = ctk.CTkProgressBar(self.sidebar, width=210)
        self.ram_progress.grid(row=6, column=0, padx=20, pady=(0, 5))
        self.ram_progress.set(0)

        # Gráfico de historial RAM mejorado
        ram_graph_container = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        ram_graph_container.grid(row=7, column=0, padx=20, pady=(0, 20), sticky="ew")

        ctk.CTkLabel(
            ram_graph_container,
            text="Historial RAM",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        ).pack()

        self.ram_graph_frame = ctk.CTkFrame(ram_graph_container, height=60, fg_color="#0f172a", corner_radius=8)
        self.ram_graph_frame.pack(fill="x", pady=(2, 0))
        self.ram_bars = []
        
        # Contador de procesos
        self.process_count_label = ctk.CTkLabel(
            self.sidebar,
            text="Procesos: 0",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.process_count_label.grid(row=8, column=0, padx=20, pady=10)

        # Botón actualizar
        self.refresh_btn = ctk.CTkButton(
            self.sidebar,
            text="🔄 Actualizar",
            command=self._manual_refresh,
            fg_color="#2563eb",
            hover_color="#1d4ed8"
        )
        self.refresh_btn.grid(row=9, column=0, padx=20, pady=10)

        # Toggle de tema
        self.theme_switch = ctk.CTkSwitch(
            self.sidebar,
            text="🌙 Tema Oscuro",
            command=self._toggle_theme,
            onvalue="dark",
            offvalue="light"
        )
        self.theme_switch.grid(row=10, column=0, padx=20, pady=(10, 5))
        self.theme_switch.select()  # Dark por defecto

        # Toggle de auto-actualización
        self.auto_refresh_switch = ctk.CTkSwitch(
            self.sidebar,
            text="⚡ Auto-actualizar",
            command=self._toggle_auto_refresh
        )
        self.auto_refresh_switch.grid(row=11, column=0, padx=20, pady=(5, 10))
        self.auto_refresh_switch.select()  # Activado por defecto

        # Info del sistema (placeholder)
        self.sys_info = ctk.CTkLabel(
            self.sidebar,
            text="Cargando...",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        self.sys_info.grid(row=13, column=0, padx=20, pady=(0, 20))
    
    def _display_system_info(self):
        """Mostrar información del sistema"""
        info = self.monitor.get_system_info()
        text = (
            f"CPU: {info['cpu_logical']} núcleos\n"
            f"RAM: {SystemMonitor.format_bytes(info['ram_total'])}\n"
            f"SO: {info['os']}"
        )
        self.sys_info.configure(text=text)
    
    def _create_header(self):
        """Crear encabezado con búsqueda"""
        self.header = ctk.CTkFrame(self, fg_color="transparent")
        self.header.grid(row=0, column=1, sticky="ew", padx=20, pady=20)
        self.header.grid_columnconfigure(1, weight=1)
        
        title = ctk.CTkLabel(
            self.header,
            text="Lista de Procesos",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title.grid(row=0, column=0, sticky="w")
        
        # Barra de búsqueda
        self.search_var = ctk.StringVar()
        self.search_var.trace("w", lambda *args: self._on_search_changed())

        self.search_entry = ctk.CTkEntry(
            self.header,
            placeholder_text="🔍 Buscar proceso...",
            width=300,
            height=35,
            textvariable=self.search_var
        )
        self.search_entry.grid(row=0, column=1, sticky="e", padx=10)
    
    def _create_process_table(self):
        """Crear tabla de procesos"""
        self.table_frame = ctk.CTkFrame(self)
        self.table_frame.grid(row=1, column=1, sticky="nsew", padx=20, pady=(0, 20))
        self.table_frame.grid_columnconfigure(0, weight=1)
        self.table_frame.grid_rowconfigure(1, weight=1)

        # ANCHOS para cada columna - Aprovechando todo el espacio
        self.column_widths = {
            'proceso': 350,  # Más ancho para nombres largos
            'pid': 100,
            'cpu': 100,
            'memoria': 120,
            'ram': 120
        }

        # Encabezados
        headers_frame = ctk.CTkFrame(self.table_frame)
        headers_frame.grid(row=0, column=0, sticky="ew", padx=2, pady=2)

        headers = [
            ("Proceso", "name", self.column_widths['proceso']),
            ("PID", "pid", self.column_widths['pid']),
            ("CPU %", "cpu", self.column_widths['cpu']),
            ("Memoria (MB)", "memory", self.column_widths['memoria']),
            ("% RAM", "memory_percent", self.column_widths['ram'])
        ]

        for i, (text, col, width) in enumerate(headers):
            btn = ctk.CTkButton(
                headers_frame,
                text=text,
                command=lambda c=col: self._sort_by_column(c),
                fg_color="#1e293b",
                hover_color="#334155",
                height=35,
                width=width
            )
            btn.grid(row=0, column=i, padx=2)
            
        
        # Lista scrollable
        self.scrollable_frame = ctk.CTkScrollableFrame(
            self.table_frame,
            fg_color="#1e293b"
        )
        self.scrollable_frame.grid(row=1, column=0, sticky="nsew", padx=2, pady=2)
        self.scrollable_frame.grid_columnconfigure(0, weight=1)
        
        self.process_widgets = []
    
    def _create_control_panel(self):
        """Panel de control"""
        self.control_panel = ctk.CTkFrame(self)
        self.control_panel.grid(row=2, column=1, sticky="ew", padx=20, pady=(0, 20))
        self.control_panel.grid_columnconfigure(1, weight=1)
        
        # PID manual
        pid_label = ctk.CTkLabel(
            self.control_panel,
            text="PID (ID del proceso):",
            font=ctk.CTkFont(size=14)
        )
        pid_label.grid(row=0, column=0, padx=10, pady=10)
        
        self.pid_entry = ctk.CTkEntry(
            self.control_panel,
            placeholder_text="Número",
            width=120
        )
        self.pid_entry.grid(row=0, column=1, sticky="w", padx=10, pady=10)
        
        # Botones
        self.kill_pid_btn = ctk.CTkButton(
            self.control_panel,
            text="❌ Terminar PID",
            command=self._kill_by_pid,
            fg_color="#dc2626",
            hover_color="#b91c1c",
            width=150
        )
        self.kill_pid_btn.grid(row=0, column=2, padx=10, pady=10)
        
        self.kill_selected_btn = ctk.CTkButton(
            self.control_panel,
            text="🗑️ Terminar Seleccionado",
            command=self._kill_selected,
            fg_color="#ea580c",
            hover_color="#c2410c",
            width=180
        )
        self.kill_selected_btn.grid(row=0, column=3, padx=10, pady=10)
        
        # Estado
        self.status_label = ctk.CTkLabel(
            self.control_panel,
            text="✓ Sistema listo",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.status_label.grid(row=0, column=4, sticky="e", padx=20, pady=10)
    
    def _on_monitor_update(self, stats: Dict):
        """Callback cuando el monitor actualiza (ejecutado en thread del monitor)"""
        # Programar actualización en el thread principal de Tkinter
        self.after(0, self._update_ui_from_stats, stats)

    def _update_history_graphs(self, cpu: float, ram: float):
        """Actualizar gráficos de historial de CPU y RAM"""
        # Agregar al historial
        self.cpu_history.append(cpu)
        self.ram_history.append(ram)

        # Mantener solo los últimos N valores
        if len(self.cpu_history) > self.max_history:
            self.cpu_history.pop(0)
        if len(self.ram_history) > self.max_history:
            self.ram_history.pop(0)

        # Actualizar gráfico CPU
        self._draw_mini_graph(self.cpu_graph_frame, self.cpu_history, "#3b82f6")

        # Actualizar gráfico RAM
        self._draw_mini_graph(self.ram_graph_frame, self.ram_history, "#10b981")

    def _draw_mini_graph(self, frame: ctk.CTkFrame, data: List[float], color: str):
        """Dibujar gráfico mejorado con líneas de referencia"""
        # Limpiar frame
        for widget in frame.winfo_children():
            widget.destroy()

        if not data:
            return

        # Canvas para dibujar
        import tkinter as tk
        canvas = tk.Canvas(
            frame,
            bg='#0f172a',
            highlightthickness=0,
            height=60
        )
        canvas.pack(fill="both", expand=True, padx=5, pady=5)

        # Esperar a que el canvas se renderice para obtener sus dimensiones
        frame.update_idletasks()
        width = canvas.winfo_width()
        height = canvas.winfo_height()

        if width <= 1 or height <= 1:
            width = 200
            height = 50

        # Líneas de referencia (25%, 50%, 75%)
        for percent in [25, 50, 75]:
            y = height - (height * percent / 100)
            canvas.create_line(0, y, width, y, fill='#1e293b', width=1, dash=(2, 2))

        # Dibujar datos como área rellena
        if len(data) > 1:
            points = []
            bar_width = width / len(data)

            for i, value in enumerate(data):
                x = i * bar_width
                y = height - (height * min(value, 100) / 100)
                points.extend([x, y])

            # Completar el polígono
            points.extend([width, height, 0, height])

            # Área rellena con transparencia
            canvas.create_polygon(
                points,
                fill=color,
                outline=color,
                width=2,
                smooth=True
            )

        # Valor actual (último valor) con texto grande
        if data:
            current_value = data[-1]
            canvas.create_text(
                width - 10,
                10,
                text=f"{current_value:.1f}%",
                fill=color,
                font=('Arial', 10, 'bold'),
                anchor='ne'
            )

    def _on_search_changed(self):
        """Manejar cambio en búsqueda con debouncing"""
        # Cancelar actualización pendiente
        if self._search_debounce_id is not None:
            self.after_cancel(self._search_debounce_id)

        # Programar nueva actualización después de 300ms
        self._search_debounce_id = self.after(300, self._update_process_display)

    def _update_process_display(self):
        """Actualizar visualización de procesos - OPTIMIZADO"""
        # NO actualizar si está minimizada
        if self.is_minimized:
            return
        
        # THROTTLE: No actualizar más de cada 2 segundos
        current_time = time.time()
        if hasattr(self, '_last_display_update'):
            if current_time - self._last_display_update < 2.0:
                return
        self._last_display_update = current_time
        
        search_text = self.search_var.get()
        processes = self.monitor.get_processes(
            sort_by=self.sort_column,
            reverse=self.sort_reverse,
            limit=40,
            filter_text=search_text
        )
        
        # Si cambió el número de procesos O el filtro, recrear
        if len(processes) != len(self.process_widgets):
            self._recreate_process_list(processes)
        else:
            # Solo actualizar texto (MUCHO más rápido)
            self._update_process_text(processes)

    def _update_process_text(self, processes):
        """Solo actualizar el texto de widgets existentes"""
        total_ram = psutil.virtual_memory().total
        
        for i, (proc, widget) in enumerate(zip(processes, self.process_widgets)):
            if not widget.winfo_exists():
                continue
                
            labels = [w for w in widget.winfo_children() if isinstance(w, ctk.CTkLabel)]
            if len(labels) >= 5:
                ram_percent = (proc.memory / total_ram) * 100 if total_ram > 0 else 0
                
                # Actualizar textos
                labels[0].configure(text=proc.name[:40])
                labels[1].configure(text=str(proc.pid))
                
                # CPU con color
                cpu_color = "#10b981" if proc.cpu < 10 else "#ef4444" if proc.cpu > 50 else "#f59e0b"
                labels[2].configure(text=f"{proc.cpu:.1f}%", text_color=cpu_color)
                
                # Memoria en MB (sin "MB")
                mem_mb = proc.memory / (1024 ** 2)
                labels[3].configure(text=f"{mem_mb:.1f}")
                
                # RAM % con color
                if ram_percent > 0 and ram_percent < 0.01:
                    ram_percent = 0.01
                ram_color = "#10b981" if ram_percent < 1 else "#f59e0b" if ram_percent < 5 else "#ef4444"
                text_ram = f"{ram_percent:.3f}%" if ram_percent < 1 else f"{ram_percent:.2f}%"
                labels[4].configure(text=text_ram, text_color=ram_color)
            
            # Resaltar seleccionado
            if proc.pid == self.selected_pid:
                widget.configure(border_width=2, border_color="#3b82f6")
            else:
                widget.configure(border_width=0)

    def _recreate_process_list(self, processes):
        """Recrear lista completa (solo cuando es necesario)"""
        for widget in self.process_widgets:
            widget.destroy()
        self.process_widgets.clear()
        
        for i, proc in enumerate(processes):
            self._create_process_row(proc, i)
    
    def _create_process_row(self, proc: ProcessInfo, index: int):
        """Crear fila de proceso"""
        proc_frame = ctk.CTkFrame(
            self.scrollable_frame,
            fg_color="#2d3748" if index % 2 == 0 else "#1e293b",
            height=40
        )
        proc_frame.grid(row=index, column=0, sticky="ew", pady=1)

        # Configurar grid del frame con los mismos anchos que los headers
        proc_frame.grid_columnconfigure(0, minsize=self.column_widths['proceso'], weight=0)
        proc_frame.grid_columnconfigure(1, minsize=self.column_widths['pid'], weight=0)
        proc_frame.grid_columnconfigure(2, minsize=self.column_widths['cpu'], weight=0)
        proc_frame.grid_columnconfigure(3, minsize=self.column_widths['memoria'], weight=0)
        proc_frame.grid_columnconfigure(4, minsize=self.column_widths['ram'], weight=0)
        proc_frame.grid_propagate(False)

        proc_frame.bind("<Button-1>", lambda e, p=proc.pid: self._select_process(p))
        proc_frame.bind("<Double-Button-1>", lambda e, p=proc: self._show_process_details(p))

        total_ram = psutil.virtual_memory().total
        # Calcular porcentaje real
        ram_percent = (proc.memory / total_ram) * 100 if total_ram > 0 else 0
        # Si es menor a 0.01%, mostrar al menos 0.01% (para que no sea 0.00%)
        if ram_percent > 0 and ram_percent < 0.01:
            ram_percent = 0.01

        # COLUMNA 0 - NOMBRE (izquierda) - ANCHO FIJO
        name_label = ctk.CTkLabel(
            proc_frame,
            text=proc.name[:35],  # Truncar si es muy largo
            anchor="w",
            font=ctk.CTkFont(size=11),
            width=self.column_widths['proceso']
        )
        name_label.grid(row=0, column=0, sticky="w", padx=5)
        name_label.bind("<Button-1>", lambda e, p=proc.pid: self._select_process(p))
        name_label.bind("<Double-Button-1>", lambda e, p=proc: self._show_process_details(p))

        # COLUMNA 1 - PID (centrado) - ANCHO FIJO
        pid_label = ctk.CTkLabel(
            proc_frame,
            text=str(proc.pid),
            font=ctk.CTkFont(size=11),
            anchor="center",
            width=self.column_widths['pid']
        )
        pid_label.grid(row=0, column=1, sticky="ew", padx=2)
        pid_label.bind("<Button-1>", lambda e, p=proc.pid: self._select_process(p))
        pid_label.bind("<Double-Button-1>", lambda e, p=proc: self._show_process_details(p))

        # COLUMNA 2 - CPU (centrado) - ANCHO FIJO
        cpu_color = "#10b981" if proc.cpu < 10 else "#ef4444" if proc.cpu > 50 else "#f59e0b"
        cpu_label = ctk.CTkLabel(
            proc_frame,
            text=f"{proc.cpu:.1f}%",
            text_color=cpu_color,
            font=ctk.CTkFont(size=11),
            anchor="center",
            width=self.column_widths['cpu']
        )
        cpu_label.grid(row=0, column=2, sticky="ew", padx=2)
        cpu_label.bind("<Button-1>", lambda e, p=proc.pid: self._select_process(p))
        cpu_label.bind("<Double-Button-1>", lambda e, p=proc: self._show_process_details(p))

        # COLUMNA 3 - MEMORIA MB (centrado) - ANCHO FIJO
        mem_mb = proc.memory / (1024 ** 2)
        mem_label = ctk.CTkLabel(
            proc_frame,
            text=f"{mem_mb:.1f}",
            font=ctk.CTkFont(size=11),
            anchor="center",
            width=self.column_widths['memoria']
        )
        mem_label.grid(row=0, column=3, sticky="ew", padx=2)
        mem_label.bind("<Button-1>", lambda e, p=proc.pid: self._select_process(p))
        mem_label.bind("<Double-Button-1>", lambda e, p=proc: self._show_process_details(p))

        # COLUMNA 4 - RAM % (centrado) - ANCHO FIJO
        ram_color = "#10b981" if ram_percent < 1 else "#f59e0b" if ram_percent < 5 else "#ef4444"
        ram_percent_label = ctk.CTkLabel(
            proc_frame,
            text=f"{ram_percent:.3f}%" if ram_percent < 1 else f"{ram_percent:.2f}%",
            text_color=ram_color,
            font=ctk.CTkFont(size=11),
            anchor="center",
            width=self.column_widths['ram']
        )
        ram_percent_label.grid(row=0, column=4, sticky="ew", padx=2)
        ram_percent_label.bind("<Button-1>", lambda e, p=proc.pid: self._select_process(p))
        ram_percent_label.bind("<Double-Button-1>", lambda e, p=proc: self._show_process_details(p))
        
        self.process_widgets.append(proc_frame)
        
        if proc.pid == self.selected_pid:
            proc_frame.configure(border_width=2, border_color="#3b82f6")        
    
    def _select_process(self, pid: int):
        """Seleccionar proceso"""
        self.selected_pid = pid
        self.status_label.configure(text=f"Seleccionado: PID {pid}")
        self._update_process_display()

    def _show_process_details(self, proc: ProcessInfo):
        """Mostrar detalles completos del proceso en una ventana emergente"""
        try:
            # Obtener proceso de psutil para más detalles
            process = psutil.Process(proc.pid)

            # Crear ventana emergente
            details_window = ctk.CTkToplevel(self)
            details_window.title(f"Detalles del Proceso - {proc.name}")
            details_window.geometry("500x600")
            details_window.resizable(False, False)

            # Hacer que la ventana sea modal
            details_window.transient(self)
            details_window.grab_set()

            # Frame principal con scroll
            scroll_frame = ctk.CTkScrollableFrame(details_window, width=460, height=550)
            scroll_frame.pack(fill="both", expand=True, padx=20, pady=20)

            # Título
            title = ctk.CTkLabel(
                scroll_frame,
                text=f"📋 {proc.name}",
                font=ctk.CTkFont(size=18, weight="bold")
            )
            title.pack(pady=(0, 20))

            # Información básica
            info_data = [
                ("PID", str(proc.pid)),
                ("Nombre", proc.name),
                ("Estado", proc.status),
                ("CPU %", f"{proc.cpu:.2f}%"),
                ("Memoria", f"{proc.memory / (1024**2):.2f} MB"),
                ("% RAM", f"{(proc.memory / psutil.virtual_memory().total) * 100:.3f}%"),
            ]

            # Intentar obtener más información
            try:
                info_data.append(("Usuario", process.username()))
            except:
                info_data.append(("Usuario", "N/A"))

            try:
                info_data.append(("Línea de comando", " ".join(process.cmdline()[:3]) + "..."))
            except:
                info_data.append(("Línea de comando", "N/A"))

            try:
                info_data.append(("Ruta ejecutable", process.exe()))
            except:
                info_data.append(("Ruta ejecutable", "N/A"))

            try:
                info_data.append(("Directorio de trabajo", process.cwd()))
            except:
                info_data.append(("Directorio de trabajo", "N/A"))

            try:
                create_time = datetime.fromtimestamp(process.create_time())
                info_data.append(("Hora de inicio", create_time.strftime("%Y-%m-%d %H:%M:%S")))
            except:
                info_data.append(("Hora de inicio", "N/A"))

            try:
                info_data.append(("Hilos", str(process.num_threads())))
            except:
                info_data.append(("Hilos", "N/A"))

            # Mostrar información en formato tabla
            for label, value in info_data:
                row_frame = ctk.CTkFrame(scroll_frame, fg_color="#2d3748")
                row_frame.pack(fill="x", pady=2)

                label_widget = ctk.CTkLabel(
                    row_frame,
                    text=label + ":",
                    font=ctk.CTkFont(size=12, weight="bold"),
                    anchor="w",
                    width=150
                )
                label_widget.pack(side="left", padx=10, pady=8)

                value_widget = ctk.CTkLabel(
                    row_frame,
                    text=str(value),
                    font=ctk.CTkFont(size=11),
                    anchor="w"
                )
                value_widget.pack(side="left", padx=10, pady=8, fill="x", expand=True)

            # Botones de acción
            button_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
            button_frame.pack(pady=20)

            kill_button = ctk.CTkButton(
                button_frame,
                text="❌ Terminar Proceso",
                command=lambda: self._kill_from_details(proc.pid, details_window),
                fg_color="#dc2626",
                hover_color="#b91c1c",
                width=150
            )
            kill_button.pack(side="left", padx=5)

            close_button = ctk.CTkButton(
                button_frame,
                text="Cerrar",
                command=details_window.destroy,
                fg_color="#6b7280",
                hover_color="#4b5563",
                width=100
            )
            close_button.pack(side="left", padx=5)

        except psutil.NoSuchProcess:
            messagebox.showerror("Error", f"El proceso {proc.pid} ya no existe")
        except Exception as e:
            messagebox.showerror("Error", f"Error al obtener detalles:\n{str(e)}")

    def _kill_from_details(self, pid: int, window):
        """Terminar proceso desde la ventana de detalles"""
        self._kill_process(pid)
        window.destroy()
    
    def _sort_by_column(self, column: str):
        """Ordenar por columna"""
        if self.sort_column == column:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = column
            self.sort_reverse = True
        self._update_process_display()
    
    def _kill_selected(self):
        """Terminar proceso seleccionado"""
        if not self.selected_pid:
            messagebox.showwarning("Advertencia", "Seleccione un proceso primero")
            return
        
        self._kill_process(self.selected_pid)
    
    def _kill_by_pid(self):
        """Terminar por PID manual"""
        pid_text = self.pid_entry.get().strip()
        if not pid_text:
            messagebox.showwarning("Advertencia", "Ingrese un PID")
            return
        
        try:
            pid = int(pid_text)
            self._kill_process(pid)
            self.pid_entry.delete(0, 'end')
        except ValueError:
            messagebox.showerror("Error", "PID debe ser un número")
    
    def _kill_process(self, pid: int):
        """Terminar proceso con confirmación"""
        # Confirmar
        if not messagebox.askyesno(
            "Confirmar",
            f"¿Terminar proceso PID {pid}?\n\nEsta acción no se puede deshacer."
        ):
            return
        
        # Ejecutar
        result = self.monitor.kill_process(pid)
        
        if result['success']:
            self.status_label.configure(text=f"✓ {result['message']}")
            self.selected_pid = None
            messagebox.showinfo("Éxito", result['message'])
        else:
            self.status_label.configure(text=f"❌ {result['error']}")
            messagebox.showerror("Error", result['error'])
    
    def _manual_refresh(self):
        """Actualización manual forzada"""
        self.status_label.configure(text="⏳ Actualizando...")
        # El monitor se actualiza automáticamente
        self.after(1000, lambda: self.status_label.configure(text="✓ Actualizado"))

    def _export_data(self):
        """Exportar datos de procesos a CSV o JSON"""
        # Obtener procesos actuales
        processes = self.monitor.get_processes(
            sort_by=self.sort_column,
            reverse=self.sort_reverse,
            limit=1000  # Exportar todos
        )

        if not processes:
            messagebox.showwarning("Advertencia", "No hay procesos para exportar")
            return

        # Preguntar formato
        dialog = ctk.CTkInputDialog(
            text="Formato de exportación (csv/json):",
            title="Exportar Datos"
        )
        format_choice = dialog.get_input()

        if not format_choice:
            return

        format_choice = format_choice.lower().strip()

        if format_choice not in ['csv', 'json']:
            messagebox.showerror("Error", "Formato inválido. Use 'csv' o 'json'")
            return

        # Seleccionar ubicación
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"procesos_{timestamp}.{format_choice}"

        filename = filedialog.asksaveasfilename(
            defaultextension=f".{format_choice}",
            filetypes=[(f"{format_choice.upper()} files", f"*.{format_choice}"), ("All files", "*.*")],
            initialfile=default_filename
        )

        if not filename:
            return

        try:
            if format_choice == 'csv':
                self._export_to_csv(processes, filename)
            else:
                self._export_to_json(processes, filename)

            self.status_label.configure(text=f"✓ Exportado a {format_choice.upper()}")
            messagebox.showinfo("Éxito", f"Datos exportados exitosamente a:\n{filename}")

        except Exception as e:
            self.status_label.configure(text="❌ Error al exportar")
            messagebox.showerror("Error", f"Error al exportar datos:\n{str(e)}")

    def _export_to_csv(self, processes: List[ProcessInfo], filename: str):
        """Exportar procesos a CSV"""
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # Encabezados
            writer.writerow(['PID', 'Nombre', 'CPU %', 'Memoria (MB)', 'Estado'])

            # Datos
            for proc in processes:
                mem_mb = proc.memory / (1024 ** 2)
                writer.writerow([
                    proc.pid,
                    proc.name,
                    f"{proc.cpu:.2f}",
                    f"{mem_mb:.2f}",
                    proc.status
                ])

    def _export_to_json(self, processes: List[ProcessInfo], filename: str):
        """Exportar procesos a JSON"""
        data = {
            'timestamp': datetime.now().isoformat(),
            'system': platform.system(),
            'total_processes': len(processes),
            'processes': []
        }

        for proc in processes:
            mem_mb = proc.memory / (1024 ** 2)
            total_ram = psutil.virtual_memory().total
            ram_percent = (proc.memory / total_ram) * 100 if total_ram > 0 else 0

            data['processes'].append({
                'pid': proc.pid,
                'name': proc.name,
                'cpu_percent': round(proc.cpu, 2),
                'memory_mb': round(mem_mb, 2),
                'memory_percent': round(ram_percent, 2),
                'status': proc.status
            })

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _on_closing(self):
        """Cerrar aplicación"""
        self.monitor.stop()
        self.destroy()

if __name__ == "__main__":
    app = TaskManagerApp()
    app.mainloop()