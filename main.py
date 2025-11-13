"""
main.py - Administrador de Tareas Multiplataforma Optimizado
Requiere: pip install customtkinter psutil
Compatible: Windows, Linux, macOS
"""

import customtkinter as ctk
from tkinter import messagebox
from system_monitor import SystemMonitor, ProcessInfo
import platform
import psutil
import time
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
        self._last_display_update = 0  # AGREGAR ESTA LÍNEA
        
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

    def _on_minimize(self, event):
        """Pausar actualizaciones cuando se minimiza"""
        self.is_minimized = True

    def _on_restore(self, event):
        """Reanudar actualizaciones"""
        self.is_minimized = False

    def _update_ui_from_stats(self, stats: Dict):
        """Actualizar UI con las estadísticas"""
        # NO actualizar si está minimizada
        if self.is_minimized:
            return
    
    def _create_sidebar(self):
        """Panel lateral con métricas"""
        self.sidebar = ctk.CTkFrame(self, width=250, corner_radius=0)
        self.sidebar.grid(row=0, column=0, rowspan=3, sticky="nsew")
        self.sidebar.grid_rowconfigure(9, weight=1)
        
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
        self.cpu_progress.grid(row=3, column=0, padx=20, pady=(0, 20))
        self.cpu_progress.set(0)
        
        # RAM
        self.ram_label = ctk.CTkLabel(
            self.sidebar,
            text="RAM: 0%",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.ram_label.grid(row=4, column=0, padx=20, pady=(10, 5))
        
        self.ram_progress = ctk.CTkProgressBar(self.sidebar, width=210)
        self.ram_progress.grid(row=5, column=0, padx=20, pady=(0, 20))
        self.ram_progress.set(0)
        
        # Contador de procesos
        self.process_count_label = ctk.CTkLabel(
            self.sidebar,
            text="Procesos: 0",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.process_count_label.grid(row=6, column=0, padx=20, pady=10)
        
        # Botón actualizar
        self.refresh_btn = ctk.CTkButton(
            self.sidebar,
            text="🔄 Actualizar",
            command=self._manual_refresh,
            fg_color="#2563eb",
            hover_color="#1d4ed8"
        )
        self.refresh_btn.grid(row=7, column=0, padx=20, pady=10)
        
        # Info del sistema (placeholder)
        self.sys_info = ctk.CTkLabel(
            self.sidebar,
            text="Cargando...",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        self.sys_info.grid(row=10, column=0, padx=20, pady=(0, 20))
    
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
        self.search_var.trace("w", lambda *args: self._update_process_display())
        
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
        
        # Encabezados
        headers_frame = ctk.CTkFrame(self.table_frame)
        headers_frame.grid(row=0, column=0, sticky="ew", padx=2, pady=2)
        
        headers = [
            ("Proceso", "name", 3),
            ("PID", "pid", 1),
            ("CPU %", "cpu", 1),
            ("Memoria (MB)", "memory", 1),
            ("% RAM", "memory_percent", 1)
        ]

        headers_frame.grid_columnconfigure(0, weight=3)  # Proceso
        headers_frame.grid_columnconfigure(1, weight=1)  # PID
        headers_frame.grid_columnconfigure(2, weight=1)  # CPU
        headers_frame.grid_columnconfigure(3, weight=1)  # Memoria
        headers_frame.grid_columnconfigure(4, weight=1)  # % RAM
        
        for i, (text, col, weight) in enumerate(headers):
            btn = ctk.CTkButton(
                headers_frame,
                text=text,
                command=lambda c=col: self._sort_by_column(c),
                fg_color="#1e293b",
                hover_color="#334155",
                height=35
            )
            btn.grid(row=0, column=i, sticky="ew", padx=2)
            
        
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
    
    def _update_ui_from_stats(self, stats: Dict):
        """Actualizar UI con las estadísticas (ejecutado en thread principal)"""
        # Actualizar métricas
        cpu = stats['cpu_percent']
        ram = stats['ram_percent']
        
        self.cpu_label.configure(text=f"CPU: {cpu:.1f}%")
        self.cpu_progress.set(cpu / 100)
        
        self.ram_label.configure(text=f"RAM: {ram:.1f}%")
        self.ram_progress.set(ram / 100)
        
        self.process_count_label.configure(text=f"Procesos: {stats['process_count']}")
        
        # Actualizar lista de procesos
        self._update_process_display()
    
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
        
        # MISMO GRID QUE LOS HEADERS
        proc_frame.grid_columnconfigure(0, weight=1)  # Proceso
        proc_frame.grid_columnconfigure(1, weight=1)  # PID
        proc_frame.grid_columnconfigure(2, weight=1)  # CPU
        proc_frame.grid_columnconfigure(3, weight=1)  # Memoria
        proc_frame.grid_columnconfigure(4, weight=1)  # % RAM
        proc_frame.grid_propagate(False)
        
        proc_frame.bind("<Button-1>", lambda e, p=proc.pid: self._select_process(p))
        
        total_ram = psutil.virtual_memory().total
        # Calcular porcentaje real
        ram_percent = (proc.memory / total_ram) * 100 if total_ram > 0 else 0
        # Si es menor a 0.01%, mostrar al menos 0.01% (para que no sea 0.00%)
        if ram_percent > 0 and ram_percent < 0.01:
            ram_percent = 0.01
        
        # COLUMNA 0 - NOMBRE (izquierda)
        name_label = ctk.CTkLabel(
            proc_frame, 
            text=proc.name[:40], 
            anchor="w", 
            font=ctk.CTkFont(size=11)
        )
        name_label.grid(row=0, column=0, sticky="ew", padx=2)
        name_label.bind("<Button-1>", lambda e, p=proc.pid: self._select_process(p))
        
        # COLUMNA 1 - PID (centrado)
        pid_label = ctk.CTkLabel(
            proc_frame, 
            text=str(proc.pid), 
            font=ctk.CTkFont(size=11), 
            anchor="center"
        )
        pid_label.grid(row=0, column=1, sticky="ew", padx=2)
        pid_label.bind("<Button-1>", lambda e, p=proc.pid: self._select_process(p))
        
        # COLUMNA 2 - CPU (centrado)
        cpu_color = "#10b981" if proc.cpu < 10 else "#ef4444" if proc.cpu > 50 else "#f59e0b"
        cpu_label = ctk.CTkLabel(
            proc_frame, 
            text=f"{proc.cpu:.1f}%", 
            text_color=cpu_color, 
            font=ctk.CTkFont(size=11), 
            anchor="center"
        )
        cpu_label.grid(row=0, column=2, sticky="ew", padx=2)
        cpu_label.bind("<Button-1>", lambda e, p=proc.pid: self._select_process(p))
        
        # COLUMNA 3 - MEMORIA MB (centrado)
        mem_mb = proc.memory / (1024 ** 2)
        mem_label = ctk.CTkLabel(
            proc_frame, 
            text=f"{mem_mb:.1f}", 
            font=ctk.CTkFont(size=11), 
            anchor="center"
        )
        mem_label.grid(row=0, column=3, sticky="ew", padx=2)
        mem_label.bind("<Button-1>", lambda e, p=proc.pid: self._select_process(p))
        
        # COLUMNA 4 - RAM % (centrado)
        ram_color = "#10b981" if ram_percent < 1 else "#f59e0b" if ram_percent < 5 else "#ef4444"
        ram_percent_label = ctk.CTkLabel(
            proc_frame, 
            text=f"{ram_percent:.3f}%" if ram_percent < 1 else f"{ram_percent:.2f}%",  # 3 decimales si es pequeño
            text_color=ram_color, 
            font=ctk.CTkFont(size=11), 
            anchor="center"
        )
        ram_percent_label.grid(row=0, column=4, sticky="ew", padx=2)
        ram_percent_label.bind("<Button-1>", lambda e, p=proc.pid: self._select_process(p))
        
        self.process_widgets.append(proc_frame)
        
        if proc.pid == self.selected_pid:
            proc_frame.configure(border_width=2, border_color="#3b82f6")        
    
    def _select_process(self, pid: int):
        """Seleccionar proceso"""
        self.selected_pid = pid
        self.status_label.configure(text=f"Seleccionado: PID {pid}")
        self._update_process_display()
    
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
    
    def _on_closing(self):
        """Cerrar aplicación"""
        self.monitor.stop()
        self.destroy()

if __name__ == "__main__":
    app = TaskManagerApp()
    app.mainloop()