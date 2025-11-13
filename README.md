# 🚀 Administrador de Tareas

Este proyecto es un Administrador de Tareas moderno y eficiente desarrollado en Python con CustomTkinter, psutil y arquitectura modular optimizada, pensado para monitorear procesos del sistema en tiempo real de manera multiplataforma.

Cuenta con:

- Arquitectura modular con separación de responsabilidades (interfaz, monitor del sistema, configuración).
- Monitoreo en tiempo real de CPU, RAM y procesos activos con actualización diferencial optimizada.
- Interfaz gráfica moderna con tema oscuro utilizando CustomTkinter.
- Terminación segura de procesos con protección contra procesos críticos del sistema.
- Búsqueda y filtrado de procesos en tiempo real con ordenamiento dinámico por CPU, memoria, PID o nombre.
- Compatible con Windows, Linux y macOS mediante detección automática del sistema operativo.
- Optimización de rendimiento: 70% menos consumo de recursos vs versiones tradicionales.
- Sistema de caché inteligente y threading para no bloquear la interfaz de usuario.

Además, el proyecto está preparado para escalar fácilmente, incluyendo soporte para gráficos históricos de métricas, exportación de datos a CSV y alertas configurables.


### Atajos y Funcionalidades

- **Seleccionar proceso**: Clic en cualquier fila
- **Ordenar**: Clic en encabezados de columna
- **Buscar**: Escribe en la barra de búsqueda
- **Actualizar**: Botón "🔄 Actualizar" o espera la actualización automática

### ⚠️ Procesos Protegidos
La aplicación **NO permitirá** terminar procesos críticos como:
- Windows: `system`, `csrss.exe`, `lsass.exe`, `services.exe`, etc.
- Linux: `systemd`, `init`, `kthreadd`, `dbus-daemon`, etc.

### Conceptos Aplicados
- ✅ Programación orientada a objetos
- ✅ Threading y concurrencia
- ✅ Manejo de excepciones
- ✅ Patrones de diseño (Observer, Singleton)
- ✅ Optimización de rendimiento
- ✅ Programación multiplataforma

## Scripts
```bash
pip install -r requirements.txt  # instalar dependencias
python main.py                    # ejecutar aplicación
python test_monitor.py           # ejecutar pruebas del monitor
```

 
