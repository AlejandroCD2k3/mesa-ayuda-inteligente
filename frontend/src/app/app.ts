import { DatePipe } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { Component, computed, inject, OnDestroy, OnInit, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';

type Categoria = 'AUTO' | 'FUNCIONAL' | 'TÉCNICO' | null;
type Estado = 'ABIERTO' | 'PENDIENTE_CONFIRMACION' | 'EN_ATENCION' | 'RESUELTO';
type Vista = 'resumen' | 'solicitudes' | 'soporte';
type Filtro = 'TODOS' | Estado;

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

  readonly conexion = signal<'comprobando' | 'conectada' | 'sin-conexion'>('comprobando');
  readonly tickets = signal<Ticket[]>([]);
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
    solicitante: '',
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
    this.cargarTickets();
    this.intervalo = setInterval(() => this.cargarTickets(false), 7000);
  }

  ngOnDestroy(): void {
    if (this.intervalo !== undefined) clearInterval(this.intervalo);
  }

  cambiarVista(vista: Vista): void {
    this.vista.set(vista);
    this.error.set('');
    this.mensaje.set('');
  }

  seleccionar(ticket: Ticket): void {
    this.seleccionadoId.set(ticket.id);
    this.respuestaAtencion = '';
    this.error.set('');
  }

  cargarTickets(mostrarIndicador = true): void {
    if (this.cargando()) return;
    this.cargando.set(true);
    this.http.get<Ticket[]>('/api/tickets').subscribe({
      next: (tickets) => {
        this.tickets.set([...tickets].sort((a, b) => b.id - a.id));
        this.cargando.set(false);
      },
      error: () => {
        this.cargando.set(false);
        if (mostrarIndicador) this.error.set('No fue posible consultar los tickets. Revisa FastAPI e intenta de nuevo.');
      }
    });
  }

  crearTicket(): void {
    const datos = {
      origen_sistema: this.formulario.origen_sistema.trim(),
      solicitante: this.formulario.solicitante.trim(),
      asunto: this.formulario.asunto.trim(),
      descripcion: this.formulario.descripcion.trim()
    };
    if (Object.values(datos).some((valor) => !valor)) {
      this.error.set('Completa todos los campos para registrar la solicitud.');
      return;
    }
    if (this.enviando()) return;
    this.enviando.set(true);
    this.error.set('');
    this.http.post<Ticket>('/api/tickets', datos).subscribe({
      next: (ticket) => {
        this.agregarTicket(ticket);
        this.seleccionadoId.set(ticket.id);
        this.formulario = { origen_sistema: 'MAIA', solicitante: '', asunto: '', descripcion: '' };
        this.enviando.set(false);
        this.mensaje.set(`Solicitud #${ticket.id} registrada correctamente.`);
      },
      error: () => {
        this.enviando.set(false);
        this.error.set('No se pudo registrar la solicitud. Revisa la conexión e inténtalo nuevamente.');
      }
    });
  }

  confirmar(resuelta: boolean): void {
    const ticket = this.seleccion();
    if (!ticket || ticket.estado !== 'PENDIENTE_CONFIRMACION' || this.enviando()) return;
    this.enviando.set(true);
    this.error.set('');
    this.http.post<Ticket>(`/api/tickets/${ticket.id}/confirmacion`, { resuelta }).subscribe({
      next: (actualizado) => {
        this.actualizarTicket(actualizado);
        this.enviando.set(false);
        this.mensaje.set(resuelta
          ? `Solicitud #${ticket.id} resuelta. ¡Gracias por confirmarlo!`
          : `Solicitud #${ticket.id} enviada a soporte funcional.`);
      },
      error: () => {
        this.enviando.set(false);
        this.error.set('No se pudo registrar la confirmación. Actualiza las solicitudes e inténtalo de nuevo.');
      }
    });
  }

  resolver(): void {
    const ticket = this.seleccion();
    const respuesta = this.respuestaAtencion.trim();
    if (!ticket || ticket.estado !== 'EN_ATENCION' || this.enviando()) return;
    if (!respuesta) {
      this.error.set('Escribe una respuesta antes de resolver el ticket.');
      return;
    }
    this.enviando.set(true);
    this.error.set('');
    this.http.post<Ticket>(`/api/tickets/${ticket.id}/resolver`, { respuesta }).subscribe({
      next: (actualizado) => {
        this.actualizarTicket(actualizado);
        this.respuestaAtencion = '';
        this.enviando.set(false);
        this.mensaje.set(`Ticket #${ticket.id} marcado como resuelto.`);
      },
      error: () => {
        this.enviando.set(false);
        this.error.set('No se pudo cerrar el ticket. Comprueba que siga en atención.');
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
