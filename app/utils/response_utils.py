from flask import jsonify
from typing import Any, Dict, Optional, List

def success_response(data: Any = None, message: str = "Operación exitosa", status_code: int = 200) -> tuple:
    """
    Crear respuesta exitosa estandarizada
    
    Args:
        data: Datos a retornar
        message: Mensaje de éxito
        status_code: Código de estado HTTP
        
    Returns:
        tuple: (response_json, status_code)
    """
    response = {
        "success": True,
        "message": message,
        "data": data
    }
    return jsonify(response), status_code

def error_response(message: str = "Error en la operación", status_code: int = 400, errors: Optional[Dict] = None) -> tuple:
    """
    Crear respuesta de error estandarizada
    
    Args:
        message: Mensaje de error
        status_code: Código de estado HTTP
        errors: Diccionario con errores específicos
        
    Returns:
        tuple: (response_json, status_code)
    """
    response = {
        "success": False,
        "message": message,
        "errors": errors or {}
    }
    return jsonify(response), status_code

def paginated_response(data: List[Any], page: int, per_page: int, total: int, message: str = "Datos obtenidos exitosamente") -> tuple:
    """
    Crear respuesta paginada estandarizada
    
    Args:
        data: Lista de datos
        page: Página actual
        per_page: Elementos por página
        total: Total de elementos
        message: Mensaje de éxito
        
    Returns:
        tuple: (response_json, status_code)
    """
    total_pages = (total + per_page - 1) // per_page
    
    response = {
        "success": True,
        "message": message,
        "data": data,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": total_pages,
            "has_prev": page > 1,
            "has_next": page < total_pages
        }
    }
    return jsonify(response), 200

def validation_error_response(errors: Dict[str, List[str]]) -> tuple:
    """
    Crear respuesta de error de validación
    
    Args:
        errors: Diccionario con errores de validación
        
    Returns:
        tuple: (response_json, status_code)
    """
    return error_response(
        message="Errores de validación",
        status_code=422,
        errors=errors
    )
