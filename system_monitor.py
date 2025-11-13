"""
system_monitor.py - Módulo Core para monitoreo eficiente del sistema
Optimizado para bajo consumo y compatible Windows/Linux
"""

import psutil
import platform
import threading
import time
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from collections import defaultdict

@dataclass
class ProcessInfo:
    """Información de proceso optimizada"""
    pid: int
    name: str
    cpu: float
    memory: int
    status: str
    username: str = ""
    
    def __hash__(self):
        return hash(self.pid)

class SystemMonitor:
    """Monitor del sistema con actualización diferencial optimizada"""
    
    def __init__(self, update_interval: float = 10.0):
        self.update_interval = update_interval
        self.running = False
        self.callbacks: List[Callable] = []
        
        # Caché para optimización
        self._process_cache: Dict[int, ProcessInfo] = {}
        self._last_cpu_times = {}
        self._system_cpu_percent = 0.0
        self._system_ram_percent = 0.0
        
        # Detección de SO
        self.os_type = platform.system()  # 'Windows', 'Linux', 'Darwin'
        self.is_windows = self.os_type == 'Windows'
        self.is_linux = self.os_type == 'Linux'
        
        # Procesos críticos por SO
        self._critical_processes = self._get_critical_processes()
        
        # Thread de monitoreo
        self._monitor_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        
    def _get_critical_processes(self) -> set:
        """Obtener procesos críticos según el SO"""
        if self.is_windows:
            return {
                'system', 'csrss.exe', 'wininit.exe', 'services.exe',
                'lsass.exe', 'smss.exe', 'winlogon.exe', 'dwm.exe',
                'svchost.exe', 'systemd', 'init'
            }
        elif self.is_linux:
            return {
                'systemd', 'init', 'kthreadd', 'systemd-journald',
                'systemd-udevd', 'dbus-daemon', 'NetworkManager',
                'accounts-daemon', 'gdm', 'Xorg', 'snapd'
            }
        else:  # macOS
            return {
                'kernel_task', 'launchd', 'WindowServer', 'loginwindow',
                'systemstats', 'mds', 'mds_stores'
            }
    
    def is_critical_process(self, name: str) -> bool:
        """Verificar si un proceso es crítico"""
        return name.lower() in self._critical_processes
    
    def get_system_info(self) -> Dict:
        """Obtener información general del sistema"""
        cpu_count = psutil.cpu_count()
        cpu_count_logical = psutil.cpu_count(logical=True)
        ram = psutil.virtual_memory()
        
        return {
            'os': self.os_type,
            'os_version': platform.version(),
            'cpu_physical': cpu_count,
            'cpu_logical': cpu_count_logical,
            'ram_total': ram.total,
            'ram_available': ram.available,
            'boot_time': psutil.boot_time()
        }
    
    def _get_process_username(self, proc: psutil.Process) -> str:
        """Obtener usuario del proceso (compatible multi-SO)"""
        try:
            return proc.username()
        except (psutil.AccessDenied, psutil.NoSuchProcess, AttributeError):
            return "N/A"
    
    def _collect_processes_optimized(self) -> Dict[int, ProcessInfo]:
        """Recolección optimizada de procesos - Solo cambios"""
        new_processes = {}
        current_pids = set()
        
        # Attrs INCLUYENDO cpu_percent para obtenerlo directamente
        attrs = ['pid', 'name', 'cpu_percent', 'memory_info', 'status']
        
        for proc in psutil.process_iter(attrs):
            try:
                pinfo = proc.info
                pid = pinfo['pid']
                current_pids.add(pid)
                
                # Obtener CPU directamente del info
                cpu_percent = pinfo['cpu_percent'] or 0.0
                
                # Crear info del proceso
                process_info = ProcessInfo(
                    pid=pid,
                    name=pinfo['name'],
                    cpu=cpu_percent,
                    memory=pinfo['memory_info'].rss if pinfo['memory_info'] else 0,
                    status=pinfo['status']
                )
                
                new_processes[pid] = process_info
                
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        
        # Actualizar caché
        self._process_cache = new_processes
        
        return new_processes
    
    
    
    def get_current_stats(self) -> Dict:
        """Obtener estadísticas actuales (thread-safe)"""
        with self._lock:
            ram = psutil.virtual_memory()
            return {
                'cpu_percent': self._system_cpu_percent,
                'ram_percent': ram.percent,
                'ram_used': ram.used,
                'ram_total': ram.total,
                'process_count': len(self._process_cache),
                'processes': list(self._process_cache.values())
            }
    
    def get_processes(self, 
                     sort_by: str = 'cpu',
                     reverse: bool = True,
                     limit: int = 100,
                     filter_text: str = '') -> List[ProcessInfo]:
        """Obtener lista de procesos filtrada y ordenada"""
        with self._lock:
            processes = list(self._process_cache.values())
        
        # Filtrar
        if filter_text:
            filter_lower = filter_text.lower()
            processes = [p for p in processes if filter_lower in p.name.lower()]
        
        # Ordenar
        sort_key = {
            'cpu': lambda p: p.cpu,
            'memory': lambda p: p.memory,
            'name': lambda p: p.name.lower(),
            'pid': lambda p: p.pid
        }.get(sort_by, lambda p: p.cpu)
        
        processes.sort(key=sort_key, reverse=reverse)
        
        return processes[:limit]

    def _update_cpu_percentages(self):
        """Actualizar porcentaje de CPU del sistema"""
        try:
            # Solo CPU del sistema (no por proceso)
            self._system_cpu_percent = psutil.cpu_percent(interval=None)
        except Exception as e:
            print(f"Error actualizando CPU del sistema: {e}")    
    
    def kill_process(self, pid: int, force: bool = False) -> Dict:
        """Terminar proceso de forma segura"""
        try:
            proc = psutil.Process(pid)
            name = proc.name()
            
            # Verificar si es crítico
            if self.is_critical_process(name):
                return {
                    'success': False,
                    'error': f'Cannot kill critical system process: {name}'
                }
            
            # Intentar terminación
            if force:
                proc.kill()
            else:
                proc.terminate()
                proc.wait(timeout=3)
            
            return {
                'success': True,
                'message': f'Process {name} (PID: {pid}) terminated'
            }
            
        except psutil.NoSuchProcess:
            return {'success': False, 'error': f'Process {pid} does not exist'}
        except psutil.AccessDenied:
            return {'success': False, 'error': f'Access denied for PID {pid}. Try running as admin/root'}
        except psutil.TimeoutExpired:
            # Intentar forzar
            try:
                proc.kill()
                return {
                    'success': True,
                    'message': f'Process {pid} force killed'
                }
            except:
                return {'success': False, 'error': 'Failed to kill process'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def register_callback(self, callback: Callable):
        """Registrar callback para actualizaciones"""
        self.callbacks.append(callback)
    
    def _monitor_loop(self):
        """Loop principal de monitoreo"""
        # Primera medición de CPU
        psutil.cpu_percent(interval=None)
        
        while self.running:
            try:
                start_time = time.time()
                
                # Actualizar procesos
                self._collect_processes_optimized()
                
                # Actualizar CPU del SISTEMA (descomentar esta línea)
                self._update_cpu_percentages()
                
                # RAM
                ram = psutil.virtual_memory()
                self._system_ram_percent = ram.percent
                
                # Notificar callbacks
                stats = self.get_current_stats()
                for callback in self.callbacks:
                    try:
                        callback(stats)
                    except Exception as e:
                        print(f"Error en callback: {e}")
                
                # Dormir el tiempo restante
                elapsed = time.time() - start_time
                sleep_time = max(0, self.update_interval - elapsed)
                time.sleep(sleep_time)
                
            except Exception as e:
                print(f"Error en monitor loop: {e}")
                time.sleep(self.update_interval)
    
    def start(self):
        """Iniciar monitoreo"""
        if self.running:
            return
        
        self.running = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
    
    def stop(self):
        """Detener monitoreo"""
        self.running = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=2)
    
    @staticmethod
    def format_bytes(bytes_val: int) -> str:
        """Formatear bytes a unidades legibles"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_val < 1024.0:
                return f"{bytes_val:.1f} {unit}"
            bytes_val /= 1024.0
        return f"{bytes_val:.1f} PB"