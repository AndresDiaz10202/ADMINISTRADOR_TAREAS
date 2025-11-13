"""
config.py - Configuración centralizada y utilidades
"""

import platform
from typing import Dict, Any
from dataclasses import dataclass

@dataclass
class AppConfig:
    """Configuración de la aplicación"""
    
    # Intervalos de actualización (segundos)
    UPDATE_INTERVAL: float = 5.0  # 5 segundos
    MAX_PROCESSES_DISPLAY: int = 50  # Solo 50 procesos
    
    # Límites de rendimiento
    MAX_PROCESSES_DISPLAY: int = 100
    TOP_CPU_PROCESSES: int = 50
    
    # Apariencia
    THEME_MODE: str = "dark"
    COLOR_THEME: str = "blue"
    
    # Colores personalizados
    COLOR_LOW_CPU: str = "#10b981"    # Verde
    COLOR_MED_CPU: str = "#f59e0b"    # Amarillo
    COLOR_HIGH_CPU: str = "#ef4444"   # Rojo
    
    COLOR_PRIMARY: str = "#2563eb"
    COLOR_DANGER: str = "#dc2626"
    COLOR_WARNING: str = "#ea580c"
    
    # Umbrales
    CPU_HIGH_THRESHOLD: float = 50.0
    CPU_LOW_THRESHOLD: float = 10.0
    
    MEMORY_HIGH_THRESHOLD: float = 80.0
    MEMORY_LOW_THRESHOLD: float = 50.0
    
    # Sistema operativo
    OS_TYPE: str = platform.system()
    IS_WINDOWS: bool = OS_TYPE == 'Windows'
    IS_LINUX: bool = OS_TYPE == 'Linux'
    IS_MACOS: bool = OS_TYPE == 'Darwin'
    
    @classmethod
    def get_os_emoji(cls) -> str:
        """Obtener emoji según el SO"""
        emojis = {
            'Windows': '🪟',
            'Linux': '🐧',
            'Darwin': '🍎'
        }
        return emojis.get(cls.OS_TYPE, '💻')
    
    @classmethod
    def get_critical_processes(cls) -> set:
        """Obtener procesos críticos del SO actual"""
        if cls.IS_WINDOWS:
            return {
                'system', 'registry', 'csrss.exe', 'wininit.exe', 
                'services.exe', 'lsass.exe', 'lsm.exe', 'smss.exe',
                'winlogon.exe', 'dwm.exe', 'svchost.exe', 'explorer.exe'
            }
        elif cls.IS_LINUX:
            return {
                'systemd', 'init', 'kthreadd', 'ksoftirqd',
                'systemd-journald', 'systemd-udevd', 'systemd-logind',
                'dbus-daemon', 'dbus-broker', 'NetworkManager',
                'accounts-daemon', 'polkitd', 'gdm', 'gdm-x-session',
                'Xorg', 'X', 'snapd', 'rsyslogd'
            }
        elif cls.IS_MACOS:
            return {
                'kernel_task', 'launchd', 'WindowServer', 'loginwindow',
                'systemstats', 'UserEventAgent', 'cfprefsd', 'distnoted',
                'mds', 'mds_stores', 'notifyd', 'coreservicesd'
            }
        return set()

class PerformanceMonitor:
    """Monitor de rendimiento de la propia aplicación"""
    
    def __init__(self):
        self.update_times = []
        self.ui_update_times = []
        self.max_samples = 30
    
    def record_update_time(self, elapsed: float):
        """Registrar tiempo de actualización"""
        self.update_times.append(elapsed)
        if len(self.update_times) > self.max_samples:
            self.update_times.pop(0)
    
    def record_ui_time(self, elapsed: float):
        """Registrar tiempo de actualización UI"""
        self.ui_update_times.append(elapsed)
        if len(self.ui_update_times) > self.max_samples:
            self.ui_update_times.pop(0)
    
    def get_stats(self) -> Dict[str, float]:
        """Obtener estadísticas de rendimiento"""
        if not self.update_times:
            return {'avg_update': 0, 'avg_ui': 0}
        
        return {
            'avg_update': sum(self.update_times) / len(self.update_times),
            'avg_ui': sum(self.ui_update_times) / len(self.ui_update_times) if self.ui_update_times else 0,
            'max_update': max(self.update_times),
            'min_update': min(self.update_times)
        }

def get_permission_message() -> str:
    """Obtener mensaje de permisos según el SO"""
    config = AppConfig()
    
    if config.IS_WINDOWS:
        return (
            "Para terminar algunos procesos del sistema, ejecute esta aplicación como Administrador:\n\n"
            "1. Clic derecho en el ejecutable o acceso directo\n"
            "2. Seleccione 'Ejecutar como administrador'"
        )
    elif config.IS_LINUX:
        return (
            "Para terminar procesos del sistema, ejecute con permisos elevados:\n\n"
            "sudo python main.py\n\n"
            "O use pkexec para ejecutar con interfaz gráfica:\n"
            "pkexec python main.py"
        )
    elif config.IS_MACOS:
        return (
            "Para terminar procesos del sistema, ejecute con sudo:\n\n"
            "sudo python main.py\n\n"
            "Nota: Es posible que necesite configurar permisos de accesibilidad"
        )
    
    return "Es posible que necesite permisos elevados para terminar algunos procesos."

def format_uptime(boot_time: float) -> str:
    """Formatear tiempo de actividad del sistema"""
    import time
    uptime_seconds = time.time() - boot_time
    
    days = int(uptime_seconds // 86400)
    hours = int((uptime_seconds % 86400) // 3600)
    minutes = int((uptime_seconds % 3600) // 60)
    
    if days > 0:
        return f"{days}d {hours}h {minutes}m"
    elif hours > 0:
        return f"{hours}h {minutes}m"
    else:
        return f"{minutes}m"

def get_system_icon(os_type: str) -> str:
    """Obtener icono del sistema según el SO"""
    icons = {
        'Windows': '🪟',
        'Linux': '🐧',
        'Darwin': '🍎',
        'FreeBSD': '👹',
        'OpenBSD': '🐡'
    }
    return icons.get(os_type, '💻')

def validate_pid(pid_str: str) -> tuple[bool, int, str]:
    """
    Validar PID ingresado
    Returns: (es_válido, pid_numerico, mensaje_error)
    """
    if not pid_str or not pid_str.strip():
        return False, 0, "PID no puede estar vacío"
    
    try:
        pid = int(pid_str.strip())
        if pid <= 0:
            return False, 0, "PID debe ser mayor a 0"
        if pid > 2147483647:  # Max PID en sistemas Unix/Windows
            return False, 0, "PID fuera de rango"
        return True, pid, ""
    except ValueError:
        return False, 0, "PID debe ser un número entero"

class ColorScheme:
    """Esquema de colores para la interfaz"""
    
    # Fondos
    BG_DARK = "#1e293b"
    BG_DARKER = "#0f172a"
    BG_LIGHT = "#2d3748"
    
    # Estados
    SUCCESS = "#10b981"
    WARNING = "#f59e0b"
    ERROR = "#ef4444"
    INFO = "#3b82f6"
    
    # Texto
    TEXT_PRIMARY = "#f8fafc"
    TEXT_SECONDARY = "#94a3b8"
    TEXT_MUTED = "#64748b"
    
    # Bordes
    BORDER_DEFAULT = "#334155"
    BORDER_ACTIVE = "#3b82f6"
    BORDER_HOVER = "#475569"
    
    @staticmethod
    def get_cpu_color(cpu_percent: float) -> str:
        """Obtener color según uso de CPU"""
        if cpu_percent < 10:
            return ColorScheme.SUCCESS
        elif cpu_percent < 50:
            return ColorScheme.WARNING
        else:
            return ColorScheme.ERROR
    
    @staticmethod
    def get_memory_color(mem_percent: float) -> str:
        """Obtener color según uso de memoria"""
        if mem_percent < 50:
            return ColorScheme.SUCCESS
        elif mem_percent < 80:
            return ColorScheme.WARNING
        else:
            return ColorScheme.ERROR

# Instancia global de configuración
APP_CONFIG = AppConfig()

# Constantes útiles
BYTE_UNITS = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
TIME_UNITS = [
    ('d', 86400),   # días
    ('h', 3600),    # horas
    ('m', 60),      # minutos
    ('s', 1)        # segundos
]