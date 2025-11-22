"""
Asistente IA - Análisis de Anomalías y Recomendaciones Inteligentes
Detecta patrones anormales en procesos y genera sugerencias automáticas
"""

import time
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict
import statistics


@dataclass
class ProcessAnomaly:
    """Representa una anomalía detectada en un proceso"""
    process_name: str
    pid: int
    anomaly_type: str  # 'high_cpu', 'high_memory', 'memory_leak', 'sudden_spike'
    severity: str  # 'low', 'medium', 'high', 'critical'
    current_value: float
    baseline_value: float
    recommendation: str
    icon: str


@dataclass
class SystemInsight:
    """Insight del sistema generado por IA"""
    title: str
    description: str
    severity: str  # 'info', 'warning', 'critical'
    action_label: Optional[str] = None
    action_data: Optional[Dict] = None
    icon: str = "💡"


class AIAssistant:
    """Asistente de IA para análisis de procesos y detección de anomalías"""

    def __init__(self):
        # Historial de métricas por proceso (key: process_name)
        self.process_history: Dict[str, Dict[str, List[float]]] = defaultdict(
            lambda: {'cpu': [], 'memory': [], 'timestamps': []}
        )

        # Baseline calculado (promedio de las últimas mediciones)
        self.baselines: Dict[str, Dict[str, float]] = {}

        # Anomalías detectadas actualmente
        self.current_anomalies: List[ProcessAnomaly] = []

        # Configuración de umbrales
        self.config = {
            'history_size': 20,  # Número de muestras para calcular baseline
            'cpu_high_threshold': 50.0,  # CPU % considerado alto
            'memory_high_threshold': 500.0,  # MB considerado alto
            'anomaly_multiplier': 2.5,  # Cuántas veces sobre baseline es anomalía
            'memory_leak_slope': 10.0,  # MB/muestra que indica memory leak
            'spike_multiplier': 3.0,  # Aumento súbito respecto a promedio
        }

        # Cache de insights para no repetir
        self.last_insights_time = 0
        self.insights_cooldown = 30  # segundos

    def update_process_data(self, processes: List[Dict]):
        """
        Actualiza el historial con nuevos datos de procesos

        Args:
            processes: Lista de dicts con keys: name, pid, cpu, memory, memory_percent
        """
        current_time = time.time()

        for proc in processes:
            name = proc['name']
            cpu = proc['cpu']
            memory = proc['memory']  # MB

            # Actualizar historial
            history = self.process_history[name]
            history['cpu'].append(cpu)
            history['memory'].append(memory)
            history['timestamps'].append(current_time)

            # Limitar tamaño del historial
            max_size = self.config['history_size']
            if len(history['cpu']) > max_size:
                history['cpu'] = history['cpu'][-max_size:]
                history['memory'] = history['memory'][-max_size:]
                history['timestamps'] = history['timestamps'][-max_size:]

        # Limpiar procesos que ya no existen (no han aparecido en las últimas 5 actualizaciones)
        self._cleanup_old_processes(processes)

    def _cleanup_old_processes(self, current_processes: List[Dict]):
        """Elimina del historial procesos que ya no están corriendo"""
        current_names = {proc['name'] for proc in current_processes}

        # Procesos en historial que no están en la lista actual
        to_remove = [name for name in self.process_history.keys()
                     if name not in current_names]

        for name in to_remove:
            # Solo eliminar si hace más de 2 minutos que no aparece
            if self.process_history[name]['timestamps']:
                last_seen = self.process_history[name]['timestamps'][-1]
                if time.time() - last_seen > 120:  # 2 minutos
                    del self.process_history[name]
                    if name in self.baselines:
                        del self.baselines[name]

    def calculate_baselines(self):
        """Calcula los valores baseline (promedio) para cada proceso"""
        for name, history in self.process_history.items():
            if len(history['cpu']) < 3:  # Necesitamos al menos 3 muestras
                continue

            try:
                cpu_baseline = statistics.mean(history['cpu'])
                memory_baseline = statistics.mean(history['memory'])

                self.baselines[name] = {
                    'cpu': cpu_baseline,
                    'memory': memory_baseline,
                    'cpu_stdev': statistics.stdev(history['cpu']) if len(history['cpu']) > 1 else 0,
                    'memory_stdev': statistics.stdev(history['memory']) if len(history['memory']) > 1 else 0
                }
            except statistics.StatisticsError:
                continue

    def detect_anomalies(self, current_processes: List[Dict]) -> List[ProcessAnomaly]:
        """
        Detecta anomalías en los procesos actuales

        Returns:
            Lista de anomalías detectadas
        """
        self.calculate_baselines()
        anomalies = []

        for proc in current_processes:
            name = proc['name']
            pid = proc['pid']
            cpu = proc['cpu']
            memory = proc['memory']

            # Saltar si no hay suficiente historial
            if name not in self.baselines:
                continue

            baseline = self.baselines[name]

            # 1. Detección de CPU alta anómala
            if cpu > self.config['cpu_high_threshold']:
                if cpu > baseline['cpu'] * self.config['anomaly_multiplier']:
                    severity = 'critical' if cpu > 80 else 'high'
                    anomalies.append(ProcessAnomaly(
                        process_name=name,
                        pid=pid,
                        anomaly_type='high_cpu',
                        severity=severity,
                        current_value=cpu,
                        baseline_value=baseline['cpu'],
                        recommendation=f"'{name}' usa {cpu:.1f}% CPU (normal: {baseline['cpu']:.1f}%). Considera cerrarlo si no es esencial.",
                        icon="🔥"
                    ))

            # 2. Detección de memoria alta anómala
            if memory > self.config['memory_high_threshold']:
                if memory > baseline['memory'] * self.config['anomaly_multiplier']:
                    severity = 'critical' if memory > 2000 else 'high'
                    anomalies.append(ProcessAnomaly(
                        process_name=name,
                        pid=pid,
                        anomaly_type='high_memory',
                        severity=severity,
                        current_value=memory,
                        baseline_value=baseline['memory'],
                        recommendation=f"'{name}' usa {memory:.0f}MB (normal: {baseline['memory']:.0f}MB). Posible fuga de memoria.",
                        icon="💾"
                    ))

            # 3. Detección de memory leak (crecimiento constante)
            if len(self.process_history[name]['memory']) >= 5:
                memory_leak = self._detect_memory_leak(name)
                if memory_leak:
                    anomalies.append(ProcessAnomaly(
                        process_name=name,
                        pid=pid,
                        anomaly_type='memory_leak',
                        severity='high',
                        current_value=memory,
                        baseline_value=baseline['memory'],
                        recommendation=f"'{name}' tiene una fuga de memoria (crecimiento constante). Reinicia el proceso.",
                        icon="⚠️"
                    ))

            # 4. Detección de spike súbito
            if len(self.process_history[name]['cpu']) >= 2:
                prev_cpu = self.process_history[name]['cpu'][-2]
                if cpu > prev_cpu * self.config['spike_multiplier'] and cpu > 30:
                    anomalies.append(ProcessAnomaly(
                        process_name=name,
                        pid=pid,
                        anomaly_type='sudden_spike',
                        severity='medium',
                        current_value=cpu,
                        baseline_value=prev_cpu,
                        recommendation=f"'{name}' tuvo un aumento súbito de CPU: {prev_cpu:.1f}% → {cpu:.1f}%",
                        icon="📈"
                    ))

        # Ordenar por severidad
        severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        anomalies.sort(key=lambda x: severity_order.get(x.severity, 999))

        self.current_anomalies = anomalies
        return anomalies

    def _detect_memory_leak(self, process_name: str) -> bool:
        """Detecta si un proceso tiene una fuga de memoria (crecimiento constante)"""
        history = self.process_history[process_name]['memory']

        if len(history) < 5:
            return False

        # Verificar tendencia creciente en las últimas 5 muestras
        last_samples = history[-5:]
        increases = sum(1 for i in range(len(last_samples)-1)
                       if last_samples[i+1] > last_samples[i])

        # Si al menos 4 de 5 muestras aumentan, es probable memory leak
        if increases >= 4:
            # Calcular pendiente
            slope = (last_samples[-1] - last_samples[0]) / len(last_samples)
            return slope > self.config['memory_leak_slope']

        return False

    def generate_insights(self, cpu_percent: float, ram_percent: float,
                         total_processes: int) -> List[SystemInsight]:
        """
        Genera insights del sistema basados en el estado actual

        Args:
            cpu_percent: Porcentaje de CPU total del sistema
            ram_percent: Porcentaje de RAM total del sistema
            total_processes: Número total de procesos

        Returns:
            Lista de insights generados
        """
        # Cooldown para no generar insights muy frecuentemente
        current_time = time.time()
        if current_time - self.last_insights_time < self.insights_cooldown:
            return []

        insights = []

        # 1. CPU alta del sistema
        if cpu_percent > 80:
            insights.append(SystemInsight(
                title="CPU crítica",
                description=f"El sistema está usando {cpu_percent:.1f}% de CPU. Rendimiento degradado.",
                severity='critical',
                icon="🚨"
            ))
        elif cpu_percent > 60:
            insights.append(SystemInsight(
                title="CPU elevada",
                description=f"Uso de CPU en {cpu_percent:.1f}%. Considera cerrar aplicaciones innecesarias.",
                severity='warning',
                icon="⚡"
            ))

        # 2. RAM alta del sistema
        if ram_percent > 85:
            insights.append(SystemInsight(
                title="RAM crítica",
                description=f"RAM al {ram_percent:.1f}%. El sistema puede ralentizarse.",
                severity='critical',
                icon="🚨"
            ))
        elif ram_percent > 70:
            insights.append(SystemInsight(
                title="RAM elevada",
                description=f"Memoria en {ram_percent:.1f}%. Libera RAM cerrando apps no esenciales.",
                severity='warning',
                icon="💡"
            ))

        # 3. Predicción de problemas basada en tendencia
        prediction = self._predict_resource_trend(cpu_percent, ram_percent)
        if prediction:
            insights.append(prediction)

        # 4. Sugerencias basadas en número de procesos
        if total_processes > 200:
            insights.append(SystemInsight(
                title="Muchos procesos activos",
                description=f"{total_processes} procesos corriendo. Esto puede afectar el rendimiento.",
                severity='info',
                icon="📊"
            ))

        self.last_insights_time = current_time
        return insights

    def _predict_resource_trend(self, current_cpu: float, current_ram: float) -> Optional[SystemInsight]:
        """Predice si los recursos llegarán a niveles críticos pronto"""
        # Esta es una predicción simple basada en el historial global
        # En una implementación más avanzada, usarías modelos de ML

        # Por ahora, una predicción simple: si está creciendo rápido, alertar
        if current_cpu > 70 and current_ram > 70:
            return SystemInsight(
                title="⚠️ Predicción: Saturación inminente",
                description="CPU y RAM están altos simultáneamente. El sistema podría saturarse pronto.",
                severity='warning',
                icon="🔮"
            )

        return None

    def get_top_resource_hogs(self, processes: List[Dict], limit: int = 3) -> Dict[str, List[Dict]]:
        """
        Identifica los procesos que más recursos consumen

        Returns:
            Dict con 'cpu' y 'memory', cada uno con lista de top procesos
        """
        # Top CPU
        top_cpu = sorted(processes, key=lambda x: x['cpu'], reverse=True)[:limit]

        # Top Memory
        top_memory = sorted(processes, key=lambda x: x['memory'], reverse=True)[:limit]

        return {
            'cpu': top_cpu,
            'memory': top_memory
        }

    def generate_recommendation_for_process(self, process: Dict) -> str:
        """Genera una recomendación específica para un proceso dado"""
        name = process['name']
        cpu = process['cpu']
        memory = process['memory']

        # Procesos del sistema - no recomendar cerrar
        system_processes = {'System Idle Process', 'System', 'svchost.exe', 'csrss.exe',
                           'smss.exe', 'wininit.exe', 'services.exe', 'lsass.exe'}

        if name in system_processes:
            return f"'{name}' es un proceso del sistema crítico. No debe cerrarse."

        # Procesos comunes y recomendaciones
        if 'chrome' in name.lower() or 'firefox' in name.lower() or 'edge' in name.lower():
            if memory > 500:
                return f"'{name}' usa mucha RAM. Cierra pestañas innecesarias o extensiones."

        if cpu > 50:
            return f"'{name}' usa mucho CPU. Verifica si está realizando una tarea importante."

        if memory > 1000:
            return f"'{name}' usa {memory:.0f}MB de RAM. Considera reiniciarlo si no es esencial."

        return f"'{name}' está funcionando normalmente."
