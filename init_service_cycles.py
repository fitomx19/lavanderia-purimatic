#!/usr/bin/env python3
"""
Script para inicializar ciclos de servicio predefinidos
Ejecutar: python init_service_cycles.py
"""

import os
import sys
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Agregar el directorio raíz al path para imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import Config
from app import create_app
from app.services.service_cycle_service import ServiceCycleService

def initialize_service_cycles():
    """
    Inicializar ciclos de servicio predefinidos
    """
    print("🚀 Inicializando ciclos de servicio predefinidos...")
    
    # Crear instancia de la aplicación
    app = create_app(Config)
    
    with app.app_context():
        try:
            # Inicializar servicio
            service_cycle_service = ServiceCycleService()
            
            # Inicializar ciclos predefinidos
            result = service_cycle_service.initialize_default_cycles()
            
            if result['success']:
                print(f"✅ {result['message']}")
                
                # Mostrar ciclos creados
                if result['data']:
                    print("\n📋 Ciclos creados:")
                    for cycle in result['data']:
                        print(f"   • {cycle['name']} - {cycle['service_type']} - ${cycle['price']}")
                else:
                    print("ℹ️  Todos los ciclos ya existían")
                    
            else:
                print(f"❌ Error: {result['message']}")
                return False
                
        except Exception as e:
            print(f"❌ Error al inicializar ciclos: {e}")
            return False
    
    return True

def show_existing_cycles():
    """
    Mostrar ciclos existentes
    """
    print("\n📊 Consultando ciclos existentes...")
    
    # Crear instancia de la aplicación
    app = create_app(Config)
    
    with app.app_context():
        try:
            service_cycle_service = ServiceCycleService()
            result = service_cycle_service.get_cycles_list(page=1, per_page=50)
            
            if result['success']:
                cycles = result['data']
                if cycles:
                    print(f"\n📋 Ciclos existentes ({len(cycles)}):")
                    for cycle in cycles:
                        duration = cycle['duration_minutes']
                        types = ', '.join(cycle['machine_types_allowed'])
                        print(f"   • {cycle['name']}")
                        print(f"     Tipo: {cycle['service_type']} | Duración: {duration}min | Precio: ${cycle['price']}")
                        print(f"     Máquinas: {types} | Activo: {'Sí' if cycle['is_active'] else 'No'}")
                        print()
                else:
                    print("ℹ️  No se encontraron ciclos")
            else:
                print(f"❌ Error al consultar ciclos: {result['message']}")
                
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == '__main__':
    print("=" * 60)
    print("🏪 LAVANDERÍA PURIMATIC - Inicialización de Ciclos")
    print("=" * 60)
    
    # Verificar variables de entorno
    if not os.getenv('MONGODB_URI'):
        print("❌ Error: MONGODB_URI no está configurada")
        print("Asegúrate de tener el archivo .env con la configuración correcta")
        sys.exit(1)
    
    # Inicializar ciclos
    success = initialize_service_cycles()
    
    if success:
        # Mostrar ciclos existentes
        show_existing_cycles()
        
        print("\n" + "=" * 60)
        print("✅ Proceso completado exitosamente")
        print("=" * 60)
        print("\n💡 Próximos pasos:")
        print("   1. Verificar que los ciclos estén correctos")
        print("   2. Iniciar la aplicación con: python run.py")
        print("   3. Probar los endpoints de ciclos de servicio")
        print("\n📚 Endpoints disponibles:")
        print("   • GET /api/service-cycles - Listar ciclos")
        print("   • POST /api/service-cycles - Crear/actualizar ciclo")
        print("   • GET /api/service-cycles/{id} - Obtener ciclo específico")
        print("   • DELETE /api/service-cycles/{id} - Eliminar ciclo")
        
    else:
        print("\n❌ El proceso falló. Revisa los errores anteriores.")
        sys.exit(1) 