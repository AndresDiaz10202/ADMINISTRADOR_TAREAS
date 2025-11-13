"""
test_monitor.py - Script de pruebas para el monitor del sistema
Útil para verificar que todo funciona sin abrir la GUI
"""

import time
from system_monitor import SystemMonitor
from config import APP_CONFIG, format_uptime

def print_separator():
    print("\n" + "="*60 + "\n")

def test_system_info():
    """Probar información del sistema"""
    print("🔍 PRUEBA 1: Información del Sistema")
    print_separator()
    
    monitor = SystemMonitor()
    info = monitor.get_system_info()
    
    print(f"Sistema Operativo: {info['os']}")
    print(f"Versión: {info['os_version']}")
    print(f"CPUs Físicas: {info['cpu_physical']}")
    print(f"CPUs Lógicas: {info['cpu_logical']}")
    print(f"RAM Total: {SystemMonitor.format_bytes(info['ram_total'])}")
    print(f"RAM Disponible: {SystemMonitor.format_bytes(info['ram_available'])}")
    print(f"Tiempo encendido: {format_uptime(info['boot_time'])}")
    
    print("\n✅ Prueba completada")

def test_process_collection():
    """Probar recolección de procesos"""
    print("🔍 PRUEBA 2: Recolección de Procesos")
    print_separator()
    
    monitor = SystemMonitor()
    
    print("Recolectando procesos (esto puede tomar unos segundos)...")
    start = time.time()
    
    # Simular actualización
    monitor._collect_processes_optimized()
    monitor._update_cpu_percentages()
    
    elapsed = time.time() - start
    
    stats = monitor.get_current_stats()
    
    print(f"\nTiempo de recolección: {elapsed:.3f} segundos")
    print(f"Procesos encontrados: {stats['process_count']}")
    print(f"CPU del sistema: {stats['cpu_percent']:.1f}%")
    print(f"RAM del sistema: {stats['ram_percent']:.1f}%")
    
    print("\n✅ Prueba completada")

def test_top_processes():
    """Mostrar top 10 procesos"""
    print("🔍 PRUEBA 3: Top 10 Procesos por CPU")
    print_separator()
    
    monitor = SystemMonitor()
    monitor.start()
    
    print("Esperando primera actualización...")
    time.sleep(3)
    
    processes = monitor.get_processes(sort_by='cpu', reverse=True, limit=10)
    
    print(f"\n{'Proceso':<30} {'PID':<8} {'CPU %':<10} {'Memoria':<12}")
    print("-" * 60)
    
    for proc in processes:
        print(f"{proc.name[:29]:<30} {proc.pid:<8} {proc.cpu:<10.1f} {SystemMonitor.format_bytes(proc.memory):<12}")
    
    monitor.stop()
    print("\n✅ Prueba completada")

def test_critical_processes():
    """Verificar detección de procesos críticos"""
    print("🔍 PRUEBA 4: Detección de Procesos Críticos")
    print_separator()
    
    monitor = SystemMonitor()
    critical = monitor._critical_processes
    
    print(f"Sistema operativo: {monitor.os_type}")
    print(f"Procesos críticos protegidos: {len(critical)}")
    print("\nLista de procesos protegidos:")
    
    for i, proc_name in enumerate(sorted(critical), 1):
        print(f"  {i}. {proc_name}")
    
    print("\n✅ Prueba completada")

def test_monitoring_loop():
    """Probar loop de monitoreo continuo"""
    print("🔍 PRUEBA 5: Monitoreo Continuo (10 segundos)")
    print_separator()
    
    monitor = SystemMonitor(update_interval=2.0)
    
    update_count = 0
    
    def callback(stats):
        nonlocal update_count
        update_count += 1
        print(f"Actualización #{update_count}: "
              f"CPU={stats['cpu_percent']:.1f}% | "
              f"RAM={stats['ram_percent']:.1f}% | "
              f"Procesos={stats['process_count']}")
    
    monitor.register_callback(callback)
    monitor.start()
    
    print("Monitoreando... (presiona Ctrl+C para detener)")
    
    try:
        time.sleep(10)
    except KeyboardInterrupt:
        print("\n\nInterrumpido por el usuario")
    
    monitor.stop()
    print(f"\n✅ Prueba completada - {update_count} actualizaciones recibidas")

def test_search_and_filter():
    """Probar búsqueda y filtrado"""
    print("🔍 PRUEBA 6: Búsqueda y Filtrado")
    print_separator()
    
    monitor = SystemMonitor()
    monitor.start()
    
    print("Esperando primera actualización...")
    time.sleep(3)
    
    search_term = "python"
    processes = monitor.get_processes(
        sort_by='memory',
        reverse=True,
        limit=5,
        filter_text=search_term
    )
    
    print(f"\nBuscando procesos que contengan '{search_term}':")
    print(f"Encontrados: {len(processes)}\n")
    
    if processes:
        print(f"{'Proceso':<30} {'PID':<8} {'Memoria':<12}")
        print("-" * 50)
        
        for proc in processes:
            print(f"{proc.name[:29]:<30} {proc.pid:<8} {SystemMonitor.format_bytes(proc.memory):<12}")
    else:
        print(f"No se encontraron procesos con '{search_term}'")
    
    monitor.stop()
    print("\n✅ Prueba completada")

def test_performance():
    """Probar rendimiento del monitor"""
    print("🔍 PRUEBA 7: Benchmark de Rendimiento")
    print_separator()
    
    monitor = SystemMonitor()
    
    iterations = 5
    times = []
    
    print(f"Ejecutando {iterations} ciclos de actualización...\n")
    
    for i in range(iterations):
        start = time.time()
        
        monitor._collect_processes_optimized()
        monitor._update_cpu_percentages()
        
        elapsed = time.time() - start
        times.append(elapsed)
        
        print(f"Iteración {i+1}: {elapsed:.3f} segundos")
        time.sleep(0.5)
    
    avg_time = sum(times) / len(times)
    min_time = min(times)
    max_time = max(times)
    
    print(f"\n📊 Resultados:")
    print(f"  Tiempo promedio: {avg_time:.3f}s")
    print(f"  Tiempo mínimo: {min_time:.3f}s")
    print(f"  Tiempo máximo: {max_time:.3f}s")
    print(f"  Variación: {(max_time - min_time):.3f}s")
    
    if avg_time < 0.5:
        print("\n✅ Rendimiento EXCELENTE")
    elif avg_time < 1.0:
        print("\n✅ Rendimiento BUENO")
    else:
        print("\n⚠️  Rendimiento MEJORABLE")
    
    print("\n✅ Prueba completada")

def run_all_tests():
    """Ejecutar todas las pruebas"""
    print("\n" + "="*60)
    print("  SUITE DE PRUEBAS - ADMINISTRADOR DE TAREAS")
    print("="*60 + "\n")
    
    tests = [
        test_system_info,
        test_process_collection,
        test_top_processes,
        test_critical_processes,
        test_search_and_filter,
        test_performance,
        # test_monitoring_loop,  # Comentado porque toma tiempo
    ]
    
    for i, test in enumerate(tests, 1):
        try:
            test()
            time.sleep(1)
        except Exception as e:
            print(f"\n❌ Error en prueba: {e}")
            import traceback
            traceback.print_exc()
        
        if i < len(tests):
            input("\n[Presiona Enter para continuar...]")
    
    print("\n" + "="*60)
    print("  TODAS LAS PRUEBAS COMPLETADAS")
    print("="*60 + "\n")

if __name__ == "__main__":
    print("\n🚀 Script de Pruebas del Monitor del Sistema\n")
    print("Opciones:")
    print("  1. Ejecutar todas las pruebas")
    print("  2. Información del sistema")
    print("  3. Recolección de procesos")
    print("  4. Top 10 procesos")
    print("  5. Procesos críticos")
    print("  6. Búsqueda y filtrado")
    print("  7. Benchmark de rendimiento")
    print("  8. Monitoreo continuo (10s)")
    print("  0. Salir")
    
    choice = input("\nSelecciona una opción: ").strip()
    
    tests = {
        '1': run_all_tests,
        '2': test_system_info,
        '3': test_process_collection,
        '4': test_top_processes,
        '5': test_critical_processes,
        '6': test_search_and_filter,
        '7': test_performance,
        '8': test_monitoring_loop,
    }
    
    if choice in tests:
        tests[choice]()
    elif choice == '0':
        print("\n👋 ¡Hasta luego!\n")
    else:
        print("\n❌ Opción no válida\n")