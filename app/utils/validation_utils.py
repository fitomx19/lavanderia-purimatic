import re
from typing import Any, Dict, List, Optional
from marshmallow import ValidationError

def validate_email(email: str) -> bool:
    """
    Validar formato de email
    
    Args:
        email: Email a validar
        
    Returns:
        bool: True si el email es válido
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone: str) -> bool:
    """
    Validar formato de teléfono
    
    Args:
        phone: Teléfono a validar
        
    Returns:
        bool: True si el teléfono es válido
    """
    # Permitir números con o sin espacios, guiones o paréntesis
    pattern = r'^[\+]?[1-9][\d\s\-\(\)]{7,15}$'
    return re.match(pattern, phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')) is not None

def validate_password_strength(password: str) -> tuple[bool, List[str]]:
    """
    Validar fortaleza de contraseña
    
    Args:
        password: Contraseña a validar
        
    Returns:
        tuple: (es_valida, lista_errores)
    """
    errors = []
    
    if len(password) < 8:
        errors.append("La contraseña debe tener al menos 8 caracteres")
    
    if not re.search(r'[A-Z]', password):
        errors.append("La contraseña debe contener al menos una letra mayúscula")
    
    if not re.search(r'[a-z]', password):
        errors.append("La contraseña debe contener al menos una letra minúscula")
    
    if not re.search(r'\d', password):
        errors.append("La contraseña debe contener al menos un número")
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        errors.append("La contraseña debe contener al menos un carácter especial")
    
    return len(errors) == 0, errors

def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> Dict[str, List[str]]:
    """
    Validar campos requeridos
    
    Args:
        data: Datos a validar
        required_fields: Lista de campos requeridos
        
    Returns:
        Dict: Diccionario con errores de validación
    """
    errors = {}
    
    for field in required_fields:
        if field not in data or data[field] is None or data[field] == '':
            errors[field] = [f"El campo '{field}' es requerido"]
    
    return errors

def validate_enum_value(value: Any, valid_values: List[Any], field_name: str) -> Optional[str]:
    """
    Validar que un valor esté en una lista de valores válidos
    
    Args:
        value: Valor a validar
        valid_values: Lista de valores válidos
        field_name: Nombre del campo para el mensaje de error
        
    Returns:
        str: Mensaje de error si es inválido, None si es válido
    """
    if value not in valid_values:
        return f"El valor '{value}' no es válido para el campo '{field_name}'. Valores válidos: {', '.join(map(str, valid_values))}"
    return None

def validate_positive_number(value: Any, field_name: str) -> Optional[str]:
    """
    Validar que un valor sea un número positivo
    
    Args:
        value: Valor a validar
        field_name: Nombre del campo para el mensaje de error
        
    Returns:
        str: Mensaje de error si es inválido, None si es válido
    """
    try:
        num_value = float(value)
        if num_value <= 0:
            return f"El campo '{field_name}' debe ser un número positivo"
    except (ValueError, TypeError):
        return f"El campo '{field_name}' debe ser un número válido"
    
    return None

def validate_string_length(value: str, min_length: int, max_length: int, field_name: str) -> Optional[str]:
    """
    Validar longitud de string
    
    Args:
        value: String a validar
        min_length: Longitud mínima
        max_length: Longitud máxima
        field_name: Nombre del campo para el mensaje de error
        
    Returns:
        str: Mensaje de error si es inválido, None si es válido
    """
    if not isinstance(value, str):
        return f"El campo '{field_name}' debe ser una cadena de texto"
    
    if len(value) < min_length:
        return f"El campo '{field_name}' debe tener al menos {min_length} caracteres"
    
    if len(value) > max_length:
        return f"El campo '{field_name}' no puede tener más de {max_length} caracteres"
    
    return None

def handle_validation_errors(errors: Dict[str, List[str]]) -> Dict[str, List[str]]:
    """
    Procesar errores de validación de Marshmallow
    
    Args:
        errors: Errores de validación
        
    Returns:
        Dict: Errores formateados
    """
    formatted_errors = {}
    
    for field, field_errors in errors.items():
        if isinstance(field_errors, list):
            formatted_errors[field] = field_errors
        else:
            formatted_errors[field] = [str(field_errors)]
    
    return formatted_errors

def validate_unique_field(value: Any, field_name: str, collection_name: str, exclude_id: Optional[str] = None) -> Optional[str]:
    """
    Validar que un campo sea único en la colección
    
    Args:
        value: Valor a validar
        field_name: Nombre del campo
        collection_name: Nombre de la colección
        exclude_id: ID a excluir de la validación (para updates)
        
    Returns:
        str: Mensaje de error si no es único, None si es único
    """
    from app import get_db
    
    db = get_db()
    collection = db[collection_name]
    
    query = {field_name: value}
    if exclude_id:
        query['_id'] = {'$ne': exclude_id}
    
    existing = collection.find_one(query)
    
    if existing:
        return f"El valor '{value}' ya existe para el campo '{field_name}'"
    
    return None
