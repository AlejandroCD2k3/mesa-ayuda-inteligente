"""Base de soluciones consultable por estudiantes y soporte."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, StringConstraints
from sqlalchemy import or_
from sqlmodel import Session, select

from .database import get_session
from .models import ArticuloConocimiento, CategoriaTicket, ahora_utc
from .sesiones_demo import UsuarioDemo, obtener_usuario_demo


Texto = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1),
]


class ContenidoArticulo(BaseModel):
    titulo: Texto
    contenido: Texto
    publicado: bool = True


class NuevoArticulo(ContenidoArticulo):
    categoria: CategoriaTicket


router = APIRouter(
    prefix="/api/conocimiento",
    tags=["Centro de conocimiento"],
)


def categorias_editables(
    usuario: UsuarioDemo,
) -> tuple[CategoriaTicket, ...]:
    if usuario.rol == "soporte_funcional":
        return (
            CategoriaTicket.AUTO,
            CategoriaTicket.FUNCIONAL,
        )

    if usuario.rol == "soporte_tecnico":
        return (CategoriaTicket.TECNICO,)

    return ()


def autorizado_para_editar(
    articulo: ArticuloConocimiento,
    usuario: UsuarioDemo,
) -> bool:
    return articulo.categoria in categorias_editables(usuario)


def obtener_visible(
    articulo_id: int,
    session: Session,
    usuario: UsuarioDemo,
) -> ArticuloConocimiento:
    articulo = session.get(ArticuloConocimiento, articulo_id)

    if articulo is None or not (
        articulo.publicado or autorizado_para_editar(articulo, usuario)
    ):
        raise HTTPException(
            status_code=404,
            detail="Articulo no encontrado",
        )

    return articulo


@router.get("", response_model=list[ArticuloConocimiento])
def listar_articulos(
    q: str = "",
    session: Session = Depends(get_session),
    usuario: UsuarioDemo = Depends(obtener_usuario_demo),
):
    consulta = select(ArticuloConocimiento)
    categorias = categorias_editables(usuario)

    if categorias:
        consulta = consulta.where(
            or_(
                ArticuloConocimiento.publicado == True,
                ArticuloConocimiento.categoria.in_(categorias),
            )
        )
    else:
        consulta = consulta.where(
            ArticuloConocimiento.publicado == True
        )

    articulos = session.exec(
        consulta.order_by(ArticuloConocimiento.id.desc())
    ).all()

    busqueda = q.strip().casefold()

    if not busqueda:
        return articulos

    return [
        articulo
        for articulo in articulos
        if busqueda in articulo.titulo.casefold()
        or busqueda in articulo.contenido.casefold()
    ]


@router.get("/{articulo_id}", response_model=ArticuloConocimiento)
def consultar_articulo(
    articulo_id: int,
    session: Session = Depends(get_session),
    usuario: UsuarioDemo = Depends(obtener_usuario_demo),
):
    return obtener_visible(articulo_id, session, usuario)


@router.post(
    "",
    response_model=ArticuloConocimiento,
    status_code=201,
)
def crear_articulo(
    datos: NuevoArticulo,
    session: Session = Depends(get_session),
    usuario: UsuarioDemo = Depends(obtener_usuario_demo),
):
    if datos.categoria not in categorias_editables(usuario):
        raise HTTPException(
            status_code=403,
            detail="Equipo sin permisos para esta categoria",
        )

    articulo = ArticuloConocimiento(
        **datos.model_dump(),
        creado_por=usuario.id,
    )

    session.add(articulo)
    session.commit()
    session.refresh(articulo)

    return articulo


@router.put(
    "/{articulo_id}",
    response_model=ArticuloConocimiento,
)
def actualizar_articulo(
    articulo_id: int,
    datos: ContenidoArticulo,
    session: Session = Depends(get_session),
    usuario: UsuarioDemo = Depends(obtener_usuario_demo),
):
    articulo = obtener_visible(articulo_id, session, usuario)

    if not autorizado_para_editar(articulo, usuario):
        raise HTTPException(
            status_code=403,
            detail="No puedes editar este articulo",
        )

    articulo.titulo = datos.titulo
    articulo.contenido = datos.contenido
    articulo.publicado = datos.publicado
    articulo.fecha_actualizacion = ahora_utc()

    session.add(articulo)
    session.commit()
    session.refresh(articulo)

    return articulo
