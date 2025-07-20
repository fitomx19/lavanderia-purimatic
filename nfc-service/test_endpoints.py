#!/usr/bin/env python3
"""
Script de prueba para el microservicio NFC mejorado
Prueba todos los endpoints con análisis detallado
"""

import requests
import json
import time
from datetime import datetime

# Configuración
BASE_URL = "http://localhost:5001"
TIMEOUT = 30

def print_separator(title):
    """Imprimir separador visual"""
    print("\n" + "="*60)
    print(f"🔍 {title}")
    print("="*60)

def test_endpoint(method, endpoint, data=None, description=""):
    """Probar un endpoint específico"""
    url = f"{BASE_URL}{endpoint}"
    print(f"\n📡 {method} {endpoint}")
    if description:
        print(f"   {description}")
    
    try:
        if method == "GET":
            response = requests.get(url, timeout=TIMEOUT)
        elif method == "POST":
            headers = {"Content-Type": "application/json"}
            response = requests.post(url, json=data, headers=headers, timeout=TIMEOUT)
        
        # Mostrar información de respuesta
        print(f"📊 Status: {response.status_code}")
        
        try:
            json_response = response.json()
            print(f"✅ Success: {json_response.get('success', 'N/A')}")
            print(f"💬 Message: {json_response.get('message', 'N/A')}")
            
            if 'duration_ms' in json_response:
                print(f"⏱️  Duration: {json_response['duration_ms']}ms")
            
            # Mostrar logs si existen
            if 'logs' in json_response and json_response['logs']:
                print("📝 Logs recientes:")
                for log in json_response['logs'][-3:]:  # Últimos 3 logs
                    print(f"   {log}")
            
            # Mostrar datos relevantes según el endpoint
            if 'data' in json_response and json_response['data']:
                show_relevant_data(endpoint, json_response['data'])
                
        except json.JSONDecodeError:
            print("❌ Respuesta no es JSON válido")
            print(f"📄 Respuesta: {response.text[:200]}...")
            
    except requests.exceptions.ConnectionError:
        print("❌ Error de conexión - ¿Está ejecutándose el microservicio?")
    except requests.exceptions.Timeout:
        print("⏰ Timeout - El endpoint tardó más de 30 segundos")
    except Exception as e:
        print(f"❌ Error inesperado: {str(e)}")

def show_relevant_data(endpoint, data):
    """Mostrar datos relevantes según el endpoint"""
    if endpoint == "/status":
        print(f"🔗 Estado conexión: {data.get('connection_status', 'N/A')}")
        print(f"📊 Hardware: {data.get('hardware_summary', {}).get('total_readers', 0)} lectores")
        print(f"🔧 Driver: {data.get('hardware_summary', {}).get('driver_status', 'N/A')}")
        
        troubleshooting = data.get('troubleshooting', [])
        if troubleshooting:
            print("🔧 Troubleshooting:")
            for tip in troubleshooting[:2]:
                print(f"   {tip}")
    
    elif endpoint == "/diagnostics":
        print(f"🏥 Salud del sistema: {data.get('system_health', 'N/A')}")
        hw_info = data.get('hardware_info', {})
        print(f"📦 PyCard: {hw_info.get('pyscard_version', 'N/A')}")
        print(f"🔌 Lectores ACR122U: {len(hw_info.get('acr122u_readers', []))}")
        
        # Mostrar recomendaciones
        recommendations = data.get('recommendations', {}).get('general', [])
        if recommendations:
            print("💡 Recomendaciones:")
            for rec in recommendations[:2]:
                print(f"   {rec}")
    
    elif endpoint in ["/read-card", "/wait-for-card"]:
        if 'uid' in data:
            print(f"🏷️  UID detectado: {data['uid']}")
            print(f"📏 Longitud: {data.get('uid_length', 'N/A')} caracteres")
    
    elif endpoint == "/initialize":
        print(f"🔧 Inicializado: {data.get('initialized', False)}")
        if 'reader' in data:
            print(f"📟 Lector: {data['reader']}")
    
    elif endpoint == "/test-connection":
        print(f"🧪 Prueba exitosa: {data.get('success', False)}")
        print(f"📡 Respuesta: {data.get('reader_response', 'N/A')}")

def main():
    """Función principal de pruebas"""
    print("🚀 Iniciando pruebas del microservicio NFC mejorado")
    print(f"🌐 URL base: {BASE_URL}")
    print(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. Health Check
    print_separator("Health Check Básico")
    test_endpoint("GET", "/health", description="Verificar que el servicio esté activo")
    
    # 2. Estado mejorado
    print_separator("Estado del Servicio (Mejorado)")
    test_endpoint("GET", "/status", description="Estado completo con troubleshooting")
    
    # 3. Diagnóstico completo
    print_separator("Diagnóstico Completo del Sistema")
    test_endpoint("GET", "/diagnostics", description="Análisis detallado de hardware y drivers")
    
    # 4. Inicialización
    print_separator("Inicialización del Lector")
    test_endpoint("POST", "/initialize", description="Forzar inicialización del ACR122U")
    
    # 5. Prueba de conexión
    print_separator("Prueba de Comunicación")
    test_endpoint("POST", "/test-connection", description="Probar comunicación con hardware")
    
    # 6. Reset del lector
    print_separator("Reset del Lector")
    test_endpoint("POST", "/reset-reader", description="Reiniciar conexión del lector")
    
    # 7. Lectura inmediata
    print_separator("Lectura Inmediata de Tarjeta")
    test_endpoint("POST", "/read-card", description="Leer UID de tarjeta si está presente")
    
    # 8. Espera con timeout corto
    print_separator("Espera de Tarjeta (Timeout 3s)")
    test_endpoint("POST", "/wait-for-card", 
                 data={"timeout": 3}, 
                 description="Esperar tarjeta por 3 segundos")
    
    # Resumen final
    print_separator("Resumen de Pruebas")
    print("✅ Pruebas completadas")
    print("\n📋 Endpoints probados:")
    endpoints = [
        "/health", "/status", "/diagnostics", "/initialize", 
        "/test-connection", "/reset-reader", "/read-card", "/wait-for-card"
    ]
    for i, endpoint in enumerate(endpoints, 1):
        print(f"   {i}. {endpoint}")
    
    print("\n💡 Para usar manualmente:")
    print("   curl http://localhost:5001/health")
    print("   curl http://localhost:5001/diagnostics")
    print("   curl -X POST http://localhost:5001/initialize")
    print("   curl -X POST http://localhost:5001/test-connection")

if __name__ == "__main__":
    main() 