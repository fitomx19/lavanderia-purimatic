"""
Datos de prueba para el sistema de lavandería
"""

from datetime import datetime
from app.utils.auth_utils import hash_password

# Datos de tiendas (se asumeque ya existen en MongoDB)
STORES_DATA = [
    {
        "_id": "store_001",
        "nombre": "Purimatic Centro",
        "direccion": "Av. Principal 123, Centro",
        "telefono": "+58-412-1234567",
        "email": "centro@purimatic.com",
        "gerente": "Juan Pérez",
        "horario": "Lunes a Domingo 6:00 AM - 10:00 PM",
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    },
    {
        "_id": "store_002", 
        "nombre": "Purimatic Norte",
        "direccion": "Centro Comercial Norte, Local 45",
        "telefono": "+58-414-9876543",
        "email": "norte@purimatic.com",
        "gerente": "María González",
        "horario": "Lunes a Domingo 7:00 AM - 9:00 PM",
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
]

# Datos de empleados
EMPLOYEES_DATA = [
    {
        "username": "admin",
        "email": "admin@purimatic.com",
        "password_hash": hash_password("AdminPurimatic2024!"),
        "role": "admin",
        "store_id": "store_001",
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    },
    {
        "username": "empleado_centro",
        "email": "empleado.centro@purimatic.com", 
        "password_hash": hash_password("Empleado123!"),
        "role": "empleado",
        "store_id": "store_001",
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    },
    {
        "username": "empleado_norte",
        "email": "empleado.norte@purimatic.com",
        "password_hash": hash_password("Empleado123!"),
        "role": "empleado", 
        "store_id": "store_002",
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
]

# Datos de clientes
CLIENTS_DATA = [
    {
        "nombre": "Carlos Rodríguez",
        "telefono": "+58-412-1111111",
        "email": "carlos.rodriguez@email.com",
        "saldo_tarjeta_recargable": 50.00,
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    },
    {
        "nombre": "Ana Martínez",
        "telefono": "+58-414-2222222", 
        "email": "ana.martinez@email.com",
        "saldo_tarjeta_recargable": 25.75,
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    },
    {
        "nombre": "Luis García",
        "telefono": "+58-416-3333333",
        "email": "luis.garcia@email.com", 
        "saldo_tarjeta_recargable": 100.00,
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    },
    {
        "nombre": "Elena Torres",
        "telefono": "+58-424-4444444",
        "email": "elena.torres@email.com",
        "saldo_tarjeta_recargable": 15.50,
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
]

# Datos de productos
PRODUCTS_DATA = [
    {
        "nombre": "Jabón en Polvo Premium",
        "descripcion": "Jabón en polvo para lavado de ropa, fórmula concentrada",
        "precio": 8.50,
        "tipo": "jabon",
        "stock": 50,
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    },
    {
        "nombre": "Suavizante Floral",
        "descripcion": "Suavizante de telas con aroma floral fresco",
        "precio": 6.75,
        "tipo": "suavizante", 
        "stock": 30,
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    },
    {
        "nombre": "Bolsas para Ropa Sucia",
        "descripcion": "Bolsas de tela resistente para transportar ropa",
        "precio": 3.25,
        "tipo": "bolsas",
        "stock": 100,
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    },
    {
        "nombre": "Quitamanchas Potente",
        "descripcion": "Removedor de manchas difíciles para pre-tratamiento",
        "precio": 12.00,
        "tipo": "quitamanchas",
        "stock": 25,
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    },
    {
        "nombre": "Blanqueador sin Cloro",
        "descripcion": "Blanqueador seguro para ropa de colores",
        "precio": 7.90,
        "tipo": "blanqueador",
        "stock": 15,
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    },
    {
        "nombre": "Jabón Líquido Delicado",
        "descripcion": "Jabón líquido especial para telas delicadas",
        "precio": 9.25,
        "tipo": "jabon",
        "stock": 20,
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
]

# Datos de lavadoras
WASHERS_DATA = [
    # Tienda Centro
    {
        "numero": 1,
        "marca": "LG",
        "capacidad": 15,
        "estado": "disponible",
        "store_id": "store_001",
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    },
    {
        "numero": 2,
        "marca": "Samsung",
        "capacidad": 12,
        "estado": "disponible",
        "store_id": "store_001",
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    },
    {
        "numero": 3,
        "marca": "Whirlpool",
        "capacidad": 18,
        "estado": "ocupada",
        "store_id": "store_001",
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    },
    {
        "numero": 4,
        "marca": "LG",
        "capacidad": 15,
        "estado": "mantenimiento",
        "store_id": "store_001",
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    },
    # Tienda Norte
    {
        "numero": 1,
        "marca": "Samsung",
        "capacidad": 20,
        "estado": "disponible",
        "store_id": "store_002",
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    },
    {
        "numero": 2,
        "marca": "Miele",
        "capacidad": 10,
        "estado": "disponible",
        "store_id": "store_002",
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    },
    {
        "numero": 3,
        "marca": "Electrolux",
        "capacidad": 16,
        "estado": "ocupada",
        "store_id": "store_002",
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
]

# Datos de secadoras
DRYERS_DATA = [
    # Tienda Centro
    {
        "numero": 1,
        "marca": "LG",
        "capacidad": 15,
        "estado": "disponible",
        "store_id": "store_001",
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    },
    {
        "numero": 2,
        "marca": "Samsung",
        "capacidad": 12,
        "estado": "disponible", 
        "store_id": "store_001",
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    },
    {
        "numero": 3,
        "marca": "Whirlpool",
        "capacidad": 18,
        "estado": "ocupada",
        "store_id": "store_001",
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    },
    # Tienda Norte
    {
        "numero": 1,
        "marca": "Samsung",
        "capacidad": 20,
        "estado": "disponible",
        "store_id": "store_002",
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    },
    {
        "numero": 2,
        "marca": "Miele",
        "capacidad": 10,
        "estado": "mantenimiento",
        "store_id": "store_002",
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
]

# Función para obtener todos los datos de prueba
def get_all_test_data():
    """
    Retorna un diccionario con todos los datos de prueba organizados por colección
    """
    return {
        "stores": STORES_DATA,
        "employees": EMPLOYEES_DATA,
        "clients": CLIENTS_DATA,
        "products": PRODUCTS_DATA,
        "washers": WASHERS_DATA,
        "dryers": DRYERS_DATA
    }

# Script para insertar datos de prueba
def insert_test_data():
    """
    Script para insertar datos de prueba en MongoDB
    Ejecutar este script para poblar la base de datos con datos iniciales
    """
    from pymongo import MongoClient
    import os
    from dotenv import load_dotenv
    
    # Cargar variables de entorno
    load_dotenv()
    
    # Conectar a MongoDB
    client = MongoClient(os.getenv('MONGODB_URI'))
    db = client.get_database()
    
    try:
        # Insertar datos en cada colección
        collections_data = get_all_test_data()
        
        for collection_name, data in collections_data.items():
            collection = db[collection_name]
            
            # Limpiar colección existente (opcional)
            # collection.delete_many({})
            
            # Insertar datos
            if data:
                result = collection.insert_many(data)
                print(f"Insertados {len(result.inserted_ids)} documentos en {collection_name}")
            else:
                print(f"No hay datos para insertar en {collection_name}")
        
        print("Datos de prueba insertados exitosamente!")
        
    except Exception as e:
        print(f"Error al insertar datos de prueba: {e}")
    
    finally:
        client.close()

if __name__ == "__main__":
    insert_test_data() 