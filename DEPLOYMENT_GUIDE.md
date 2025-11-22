# 📋 Guía de Despliegue y Ejecución

## Administrador de Tareas Multiplataforma

Esta guía te ayudará a desplegar y ejecutar el proyecto en tu sistema operativo.

---

## 📌 Requisitos Previos

Antes de comenzar, asegúrate de tener instalado:

- **Python 3.8 o superior**
  - Verifica con: `python --version` o `python3 --version`
  - Descarga desde: https://www.python.org/downloads/

- **pip** (administrador de paquetes de Python)
  - Normalmente viene incluido con Python
  - Verifica con: `pip --version` o `pip3 --version`

- **Git** (opcional, solo si vas a clonar el repositorio)
  - Verifica con: `git --version`

---

## 🚀 Pasos de Instalación

### 1️⃣ Obtener el Proyecto

**Opción A: Si ya tienes el proyecto descargado**
```bash
cd ADMINISTRADOR_TAREAS
```

**Opción B: Clonar desde GitHub**
```bash
git clone https://github.com/AndresDiaz10202/ADMINISTRADOR_TAREAS.git
cd ADMINISTRADOR_TAREAS
```

### 2️⃣ Crear un Entorno Virtual (Recomendado)

Es recomendable usar un entorno virtual para aislar las dependencias:

**En Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**En Linux/macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

Verás `(venv)` al inicio de tu línea de comandos cuando el entorno esté activado.

### 3️⃣ Instalar Dependencias

```bash
pip install -r requirements.txt
```

Esto instalará:
- `customtkinter>=5.2.0` - Interfaz gráfica moderna
- `psutil>=5.9.0` - Monitoreo del sistema

### 4️⃣ Ejecutar la Aplicación

```bash
python main.py
```

**En sistemas Linux/macOS puede ser necesario usar:**
```bash
python3 main.py
```

---

## 🎯 Ejecución Rápida

Si ya tienes todo configurado:

```bash
# Activar entorno virtual (si lo usas)
source venv/bin/activate  # Linux/macOS
# o
venv\Scripts\activate     # Windows

# Ejecutar
python main.py
```

---

## 🧪 Ejecutar Pruebas

Para verificar que el monitor del sistema funciona correctamente:

```bash
python test_monitor.py
```

---

## 🛠️ Solución de Problemas Comunes

### ❌ Error: "python: command not found"
- En algunos sistemas debes usar `python3` en lugar de `python`
- Verifica que Python esté instalado: `python3 --version`

### ❌ Error: "No module named 'customtkinter'"
- Asegúrate de haber instalado las dependencias: `pip install -r requirements.txt`
- Verifica que el entorno virtual esté activado (si lo usas)

### ❌ Error: "Permission denied" (Linux/macOS)
- Algunos procesos requieren permisos de administrador
- Ejecuta con: `sudo python3 main.py` (no recomendado para uso normal)

### ❌ La interfaz gráfica no se muestra
- Asegúrate de tener un entorno gráfico (X11 en Linux)
- En servidores sin interfaz gráfica, este programa no funcionará

### ❌ Error: "Access is denied" al terminar procesos (Windows)
- Ejecuta como administrador: clic derecho en la terminal → "Ejecutar como administrador"
- Algunos procesos del sistema están protegidos y no se pueden terminar

---

## 🖥️ Instrucciones Específicas por Sistema Operativo

### Windows

1. Abre **PowerShell** o **CMD**
2. Navega a la carpeta del proyecto
3. Ejecuta:
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

### Linux (Ubuntu/Debian)

1. Abre una **Terminal**
2. Instala Python si no lo tienes:
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
```
3. Ejecuta:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 main.py
```

### macOS

1. Abre **Terminal**
2. Ejecuta:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 main.py
```

---

## 📦 Despliegue como Ejecutable (Opcional)

Si quieres distribuir la aplicación sin necesidad de Python instalado:

### Instalar PyInstaller
```bash
pip install pyinstaller
```

### Crear ejecutable

**Windows:**
```bash
pyinstaller --onefile --windowed --name="AdminTareas" main.py
```

**Linux/macOS:**
```bash
pyinstaller --onefile --windowed --name="AdminTareas" main.py
```

El ejecutable estará en la carpeta `dist/`

---

## 🎨 Características de la Aplicación

Una vez ejecutada, podrás:

- ✅ Ver procesos en tiempo real
- ✅ Monitorear uso de CPU y RAM
- ✅ Buscar procesos específicos
- ✅ Ordenar por CPU, Memoria, PID o Nombre
- ✅ Terminar procesos (con protección de procesos críticos)
- ✅ Actualización automática cada 2 segundos

---

## 🔒 Seguridad

La aplicación incluye protección contra terminación de procesos críticos:

- **Windows**: `system`, `csrss.exe`, `lsass.exe`, `services.exe`
- **Linux**: `systemd`, `init`, `kthreadd`, `dbus-daemon`

---

## 📞 Soporte

Si encuentras problemas:

1. Revisa esta guía completa
2. Verifica que tengas las versiones correctas de Python y dependencias
3. Consulta el archivo `ADVANCE_GUIDE.md` para información técnica detallada
4. Abre un issue en el repositorio de GitHub

---

## 📄 Licencia

Consulta el repositorio para información sobre la licencia.

---

**¡Listo! Tu Administrador de Tareas debería estar funcionando. 🎉**
