"""Importaciones compatibles con la API anterior."""
from .api.conocimiento import (
    ContenidoArticulo, NuevoArticulo, Texto, autorizado_para_editar,
    categorias_editables, consultar_articulo, crear_articulo, listar_articulos,
    actualizar_articulo, obtener_visible, router,
)
