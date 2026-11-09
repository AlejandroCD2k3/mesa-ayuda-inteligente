import { DatePipe } from '@angular/common';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Component, computed, inject, OnDestroy, OnInit, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';

type Categoria = 'AUTO' | 'FUNCIONAL' | 'TÉCNICO' | null;
type Estado = 'ABIERTO' | 'PENDIENTE_CONFIRMACION' | 'EN_ATENCION' | 'RESUELTO';
type Vista = 'resumen' | 'solicitudes' | 'soporte';
type Filtro = 'TODOS' | Estado;

type RolDemo = 'estudiante' | 'soporte_funcional' | 'soporte_tecnico';

export interface UsuarioDemo {
  id: string;
  nombre: string;
  rol: RolDemo;
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

@Component({
  selector: 'app-root',
  imports: [FormsModule, DatePipe],
  templateUrl: './app.html',
  styleUrl: './app.css'
})
export class App implements OnInit, OnDestroy {
  private readonly http = inject(HttpClient);
  private intervalo: ReturnType<typeof setInterval> | undefined;
  private token = '';
  private versionSesion = 0;
  private versionHistorial = 0;

  readonly conexion = signal<'comprobando' | 'conectada' | 'sin-conexion'>('comprobando');
  readonly tickets = signal<Ticket[]>([]);
  readonly eventos = signal<TicketEvento[]>([]);
  readonly cargandoEventos = signal(false);
  readonly errorEventos = signal('');
  readonly perfiles = signal<UsuarioDemo[]>([]);
  readonly usuario = signal<UsuarioDemo | null>(null);
  readonly iniciando = signal(false);
  readonly esEstudiante = computed(
    () => this.usuario()?.rol === 'estudiante'
  );
  readonly cargando = signal(false);
  readonly enviando = signal(false);
  readonly vista = signal<Vista>('resumen');
  readonly busqueda = signal('');
  readonly filtro = signal<Filtro>('TODOS');
  readonly seleccionadoId = signal<number | null>(null);
  readonly mensaje = signal('');
  readonly error = signal('');

  formulario = {
    origen_sistema: 'MAIA',
    asunto: '',
    descripcion: ''
  };
  respuestaAtencion = '';

  readonly total = computed(() => this.tickets().length);
  readonly pendientes = computed(() => this.tickets().filter(
    (ticket) => ticket.estado === 'PENDIENTE_CONFIRMACION'
  ).length);
  readonly enAtencion = computed(() => this.tickets().filter(
    (ticket) => ticket.estado === 'EN_ATENCION'
  ).length);
  readonly resueltos = computed(() => this.tickets().filter(
    (ticket) => ticket.estado === 'RESUELTO'
  ).length);
  readonly recientes = computed(() => this.tickets().slice(0, 5));
  readonly paraSoporte = computed(() => this.tickets().filter(
    (ticket) => ticket.estado === 'EN_ATENCION'
  ));
  readonly seleccion = computed(() => this.tickets().find(
    (ticket) => ticket.id === this.seleccionadoId()
  ) ?? null);
  readonly visibles = computed(() => {
    const texto = this.busqueda().trim().toLocaleLowerCase();
    return this.tickets().filter((ticket) => {
      const coincideEstado = this.filtro() === 'TODOS' || ticket.estado === this.filtro();
      const coincideTexto = !texto || [
        ticket.id.toString(), ticket.asunto, ticket.solicitante, ticket.origen_sistema
      ].some((campo) => campo.toLocaleLowerCase().includes(texto));
      return coincideEstado && coincideTexto;
    });
  });

  ngOnInit(): void {
    this.http.get<{ status: string }>('/api/health').subscribe({
      next: (respuesta) => this.conexion.set(
        respuesta.status === 'ok' ? 'conectada' : 'sin-conexion'
      ),
      error: () => this.conexion.set('sin-conexion')
    });

    this.http.get<UsuarioDemo[]>('/api/demo/usuarios').subscribe({
      next: (perfiles) => this.perfiles.set(perfiles),
      error: () => this.error.set(
        'No se pudieron consultar los perfiles de demostración.'
      )
    });

    this.intervalo = setInterval(() => {
      if (this.token) this.cargarTickets(false);
    }, 7000);
  }

  ngOnDestroy(): void {
    if (this.intervalo !== undefined) {
      clearInterval(this.intervalo);
    }
    this.versionSesion++;
    this.versionHistorial++;
  }

  iniciarPerfil(id: string): void {
    if (this.iniciando()) return;

    this.cerrarSesion();
    const version = this.versionSesion;
    this.iniciando.set(true);

    this.http.post<{ token: string; usuario: UsuarioDemo }>(
      '/api/demo/sesion',
      { usuario_id: id }
    ).subscribe({
      next: (respuesta) => {
        if (version !== this.versionSesion) return;

        this.token = respuesta.token;
        this.usuario.set(respuesta.usuario);
        this.iniciando.set(false);
        this.cargarTickets();
      },
      error: () => {
        if (version !== this.versionSesion) return;

        this.iniciando.set(false);
        this.error.set(
          'No fue posible iniciar el perfil. Comprueba el backend.'
        );
      }
    });
  }

  cerrarSesion(): void {
    this.versionSesion++;
    this.versionHistorial++;
    this.eventos.set([]);
    this.cargandoEventos.set(false);
    this.errorEventos.set('');
    this.token = '';
    this.usuario.set(null);
    this.tickets.set([]);
    this.seleccionadoId.set(null);
    this.vista.set('resumen');
    this.busqueda.set('');
    this.filtro.set('TODOS');
    this.cargando.set(false);
    this.enviando.set(false);
    this.iniciando.set(false);
    this.respuestaAtencion = '';

    this.formulario = {
      origen_sistema: 'MAIA',
      asunto: '',
      descripcion: ''
    };

    this.mensaje.set('');
    this.error.set('');
  }

  private opcionesSesion() {
    return {
      headers: {
        Authorization: `Bearer ${this.token}`
      }
    };
  }

  private errorSolicitud(
    error: HttpErrorResponse,
    mensaje: string
  ): void {
    if (error.status === 401) {
      this.cerrarSesion();
      this.error.set(
        'La sesión venció. Selecciona nuevamente un perfil.'
      );
      return;
    }

    this.error.set(mensaje);
  }

  cambiarVista(vista: Vista): void {
    if (!this.usuario()) return;
    if (vista === 'soporte' && this.esEstudiante()) return;
    if (vista === 'solicitudes' && !this.esEstudiante()) return;

    this.vista.set(vista);
    this.error.set('');
    this.mensaje.set('');
  }

  seleccionar(ticket: Ticket): void {
    this.seleccionadoId.set(ticket.id);
    this.respuestaAtencion = '';
    this.error.set('');
    this.cargarEventos(ticket.id);
  }

  cargarEventos(ticketId: number): void {
    if (!this.token || this.seleccionadoId() !== ticketId) return;

    const sesion = this.versionSesion;
    const peticion = ++this.versionHistorial;

    this.eventos.set([]);
    this.errorEventos.set('');
    this.cargandoEventos.set(true);

    this.http.get<TicketEvento[]>(
      `/api/tickets/${ticketId}/eventos`,
      this.opcionesSesion()
    ).subscribe({
      next: (eventos) => {
        if (
          sesion !== this.versionSesion ||
          peticion !== this.versionHistorial ||
          this.seleccionadoId() !== ticketId
        ) return;

        this.eventos.set(eventos);
        this.cargandoEventos.set(false);
      },
      error: (error: HttpErrorResponse) => {
        if (
          sesion !== this.versionSesion ||
          peticion !== this.versionHistorial ||
          this.seleccionadoId() !== ticketId
        ) return;

        this.cargandoEventos.set(false);

        if (error.status === 401) {
          this.errorSolicitud(
            error,
            'No se pudo consultar el historial.'
          );
        } else {
          this.errorEventos.set(
            'No fue posible cargar el historial.'
          );
        }
      }
    });
  }

  etiquetaEvento(tipo: string): string {
    const nombres: Record<string, string> = {
      CREACION: 'Solicitud registrada',
      CLASIFICACION: 'Clasificación',
      ASIGNACION: 'Asignación a soporte',
      ACTUALIZACION: 'Actualización',
      CONFIRMACION: 'Solución confirmada',
      ESCALAMIENTO: 'Escalamiento',
      RESOLUCION: 'Solicitud resuelta'
    };

    return nombres[tipo] ?? tipo;
  }

  nombreActor(actor: string): string {
    if (actor === 'sistema') return 'Sistema';

    return this.perfiles().find(
      (perfil) => perfil.id === actor
    )?.nombre ?? actor;
  }

  fechaEvento(fecha: string): string {
    return /(?:Z|[+-]\d{2}:\d{2})$/i.test(fecha)
      ? fecha
      : `${fecha}Z`;
  }

  cargarTickets(mostrarIndicador = true): void {
    if (!this.token || this.cargando()) return;

    const version = this.versionSesion;
    this.cargando.set(true);

    this.http.get<Ticket[]>(
      '/api/tickets',
      this.opcionesSesion()
    ).subscribe({
      next: (tickets) => {
        if (version !== this.versionSesion) return;

        const anterior = this.seleccion();

        this.tickets.set(
          [...tickets].sort((a, b) => b.id - a.id)
        );

        if (anterior) {
          const actual = this.seleccion();

          if (!actual) {
            this.seleccionadoId.set(null);
            this.versionHistorial++;
            this.eventos.set([]);
          } else if (
            actual.fecha_actualizacion !==
            anterior.fecha_actualizacion
          ) {
            this.cargarEventos(actual.id);
          }
        }

        this.cargando.set(false);
      },
      error: (error: HttpErrorResponse) => {
        if (version !== this.versionSesion) return;

        this.cargando.set(false);

        if (mostrarIndicador || error.status === 401) {
          this.errorSolicitud(
            error,
            'No fue posible consultar los tickets. Revisa FastAPI e intenta de nuevo.'
          );
        }
      }
    });
  }

  crearTicket(): void {
    if (!this.esEstudiante() || !this.token || this.enviando()) {
      return;
    }

    const datos = {
      origen_sistema: this.formulario.origen_sistema.trim(),
      asunto: this.formulario.asunto.trim(),
      descripcion: this.formulario.descripcion.trim()
    };

    if (Object.values(datos).some((valor) => !valor)) {
      this.error.set(
        'Completa todos los campos para registrar la solicitud.'
      );
      return;
    }

    const version = this.versionSesion;
    this.enviando.set(true);
    this.error.set('');

    this.http.post<Ticket>(
      '/api/tickets',
      datos,
      this.opcionesSesion()
    ).subscribe({
      next: (ticket) => {
        if (version !== this.versionSesion) return;

        this.agregarTicket(ticket);
        this.seleccionar(ticket);

        this.formulario = {
          origen_sistema: 'MAIA',
          asunto: '',
          descripcion: ''
        };

        this.enviando.set(false);
        this.mensaje.set(
          `Solicitud #${ticket.id} registrada correctamente.`
        );
      },
      error: (error: HttpErrorResponse) => {
        if (version !== this.versionSesion) return;

        this.enviando.set(false);
        this.errorSolicitud(
          error,
          'No se pudo registrar la solicitud. Revisa la conexión e inténtalo nuevamente.'
        );
      }
    });
  }

  confirmar(resuelta: boolean): void {
    const ticket = this.seleccion();

    if (
      !this.esEstudiante() ||
      !this.token ||
      !ticket ||
      ticket.estado !== 'PENDIENTE_CONFIRMACION' ||
      this.enviando()
    ) return;

    const version = this.versionSesion;
    this.enviando.set(true);
    this.error.set('');

    this.http.post<Ticket>(
      `/api/tickets/${ticket.id}/confirmacion`,
      { resuelta },
      this.opcionesSesion()
    ).subscribe({
      next: (actualizado) => {
        if (version !== this.versionSesion) return;

        this.actualizarTicket(actualizado);

        if (this.seleccionadoId() === ticket.id) {
          this.cargarEventos(ticket.id);
        }

        this.enviando.set(false);

        this.mensaje.set(resuelta
          ? `Solicitud #${ticket.id} resuelta. ¡Gracias por confirmarlo!`
          : `Solicitud #${ticket.id} enviada a soporte funcional.`
        );
      },
      error: (error: HttpErrorResponse) => {
        if (version !== this.versionSesion) return;

        this.enviando.set(false);
        this.errorSolicitud(
          error,
          'No se pudo registrar la confirmación. Actualiza las solicitudes e inténtalo de nuevo.'
        );
      }
    });
  }

  resolver(): void {
    const ticket = this.seleccion();
    const respuesta = this.respuestaAtencion.trim();

    if (
      this.esEstudiante() ||
      !this.token ||
      !ticket ||
      ticket.estado !== 'EN_ATENCION' ||
      this.enviando()
    ) return;

    if (!respuesta) {
      this.error.set(
        'Escribe una respuesta antes de resolver el ticket.'
      );
      return;
    }

    const version = this.versionSesion;
    this.enviando.set(true);
    this.error.set('');

    this.http.post<Ticket>(
      `/api/tickets/${ticket.id}/resolver`,
      { respuesta },
      this.opcionesSesion()
    ).subscribe({
      next: (actualizado) => {
        if (version !== this.versionSesion) return;

        this.actualizarTicket(actualizado);

        if (this.seleccionadoId() === ticket.id) {
          this.cargarEventos(ticket.id);
        }

        this.respuestaAtencion = '';
        this.enviando.set(false);

        this.mensaje.set(
          `Ticket #${ticket.id} marcado como resuelto.`
        );
      },
      error: (error: HttpErrorResponse) => {
        if (version !== this.versionSesion) return;

        this.enviando.set(false);
        this.errorSolicitud(
          error,
          'No se pudo cerrar el ticket. Comprueba que siga en atención.'
        );
      }
    });
  }

  etiquetaEstado(estado: Estado): string {
    const etiquetas: Record<Estado, string> = {
      ABIERTO: 'Abierto',
      PENDIENTE_CONFIRMACION: 'Por confirmar',
      EN_ATENCION: 'En atención',
      RESUELTO: 'Resuelto'
    };
    return etiquetas[estado];
  }

  etiquetaCategoria(categoria: Categoria): string {
    return categoria === 'TÉCNICO' ? 'Técnico' : (categoria === 'AUTO' ? 'Automático' : 'Funcional');
  }

  private agregarTicket(ticket: Ticket): void {
    this.tickets.update((anteriores) => [ticket, ...anteriores.filter((item) => item.id !== ticket.id)]);
  }

  private actualizarTicket(ticket: Ticket): void {
    this.tickets.update((anteriores) => anteriores.map(
      (item) => item.id === ticket.id ? ticket : item
    ));
  }
}
