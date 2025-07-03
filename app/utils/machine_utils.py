"""
Utilidades para manejo de tipos de máquinas y compatibilidad con ciclos de servicio
"""

from typing import Dict, Any, Optional

def get_washer_machine_type(capacidad: float) -> str:
    """
    Determinar el tipo de lavadora basándose en la capacidad
    
    Args:
        capacidad: Capacidad en kg
        
    Returns:
        str: Tipo de máquina ('chica' o 'grande')
    """
    if capacidad <= 10.0:
        return 'chica'
    else:
        return 'grande'

def get_dryer_machine_type() -> str:
    """
    Determinar el tipo de secadora (siempre es 'secadora')
    
    Returns:
        str: Siempre retorna 'secadora'
    """
    return 'secadora'

def get_machine_type_from_data(machine_data: Dict[str, Any], machine_category: str) -> str:
    """
    Obtener el tipo de máquina basándose en los datos y categoría
    
    Args:
        machine_data: Datos de la máquina
        machine_category: Categoría ('washer' o 'dryer')
        
    Returns:
        str: Tipo de máquina
    """
    if machine_category == 'washer':
        capacidad = float(machine_data.get('capacidad', 0))
        return get_washer_machine_type(capacidad)
    elif machine_category == 'dryer':
        return get_dryer_machine_type()
    else:
        raise ValueError(f"Categoría de máquina no válida: {machine_category}")

def validate_cycle_machine_compatibility(cycle_data: Dict[str, Any], machine_data: Dict[str, Any], machine_category: str) -> Dict[str, Any]:
    """
    Validar si un ciclo es compatible con una máquina específica
    
    Args:
        cycle_data: Datos del ciclo de servicio
        machine_data: Datos de la máquina
        machine_category: Categoría de máquina ('washer' o 'dryer')
        
    Returns:
        Dict: Resultado de la validación
    """
    try:
        # Obtener tipo de máquina
        machine_type = get_machine_type_from_data(machine_data, machine_category)
        
        # Obtener tipos permitidos en el ciclo
        machine_types_allowed = cycle_data.get('machine_types_allowed', [])
        
        # Validar compatibilidad
        if machine_type not in machine_types_allowed:
            return {
                'valid': False,
                'message': f'El ciclo no es compatible con máquina tipo {machine_type}',
                'machine_type': machine_type,
                'allowed_types': machine_types_allowed
            }
        
        # Validar estado del ciclo
        if not cycle_data.get('is_active', False):
            return {
                'valid': False,
                'message': 'El ciclo no está activo',
                'machine_type': machine_type,
                'allowed_types': machine_types_allowed
            }
        
        return {
            'valid': True,
            'message': 'Ciclo compatible con la máquina',
            'machine_type': machine_type,
            'allowed_types': machine_types_allowed
        }
        
    except Exception as e:
        return {
            'valid': False,
            'message': f'Error en validación: {str(e)}',
            'machine_type': None,
            'allowed_types': []
        }

def get_compatible_cycles_for_machine(machine_data: Dict[str, Any], machine_category: str, available_cycles: list) -> list:
    """
    Obtener lista de ciclos compatibles con una máquina específica
    
    Args:
        machine_data: Datos de la máquina
        machine_category: Categoría de máquina ('washer' o 'dryer')
        available_cycles: Lista de ciclos disponibles
        
    Returns:
        list: Lista de ciclos compatibles
    """
    try:
        machine_type = get_machine_type_from_data(machine_data, machine_category)
        compatible_cycles = []
        
        for cycle in available_cycles:
            machine_types_allowed = cycle.get('machine_types_allowed', [])
            if machine_type in machine_types_allowed and cycle.get('is_active', False):
                compatible_cycles.append(cycle)
        
        return compatible_cycles
        
    except Exception:
        return []

def get_machine_classification_info() -> Dict[str, Any]:
    """
    Obtener información sobre la clasificación de máquinas
    
    Returns:
        Dict: Información de clasificación
    """
    return {
        'washer_types': {
            'chica': {
                'description': 'Lavadora chica',
                'capacity_range': '5.0 - 10.0 kg',
                'condition': 'capacidad <= 10.0'
            },
            'grande': {
                'description': 'Lavadora grande',
                'capacity_range': '10.1+ kg',
                'condition': 'capacidad > 10.0'
            }
        },
        'dryer_types': {
            'secadora': {
                'description': 'Secadora estándar',
                'capacity_range': 'Cualquier capacidad',
                'condition': 'Siempre secadora'
            }
        },
        'service_types': {
            'lavado': {
                'compatible_machines': ['chica', 'grande'],
                'description': 'Solo lavadoras'
            },
            'secado': {
                'compatible_machines': ['secadora'],
                'description': 'Solo secadoras'
            },
            'combo': {
                'compatible_machines': ['chica', 'grande', 'secadora'],
                'description': 'Lavadoras y secadoras'
            }
        }
    } 