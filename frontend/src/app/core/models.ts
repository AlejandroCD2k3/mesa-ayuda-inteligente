export type Categoria = 'AUTO' | 'FUNCIONAL' | 'TÉCNICO' | null;
export type Estado = 'ABIERTO' | 'PENDIENTE_CONFIRMACION' | 'EN_ATENCION' | 'RESUELTO';
export type Vista = 'resumen' | 'solicitudes' | 'soporte' | 'conocimiento';
export type Filtro = 'TODOS' | Estado;

export type RolDemo = 'estudiante' | 'soporte_funcional' | 'soporte_tecnico';

export interface UsuarioDemo {
  id: string;
  nombre: string;
  rol: RolDemo;
}

export type CategoriaArticulo = 'AUTO' | 'FUNCIONAL' | 'TÉCNICO';

export interface ArticuloConocimiento {
  id: number;
  titulo: string;
  contenido: string;
  categoria: CategoriaArticulo;
  publicado: boolean;
  creado_por: string;
  fecha_creacion: string;
  fecha_actualizacion: string;
}

export interface TicketEvento {
  id: number;
  ticket_id: number;
  tipo: string;
  detalle: string;
  actor: string;
  fecha: string;
}

export interface Ticket {
  id: number;
  origen_sistema: string;
  solicitante: string;
  asunto: string;
  descripcion: string;
  categoria: Categoria;
  estado: Estado;
  responsable: string | null;
  motivo_clasificacion: string | null;
  respuesta_sugerida: string | null;
  respuesta_atencion: string | null;
  fecha_creacion: string;
  fecha_actualizacion: string;
}
