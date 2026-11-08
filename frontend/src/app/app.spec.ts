import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { App, Ticket } from './app';

const funcional: Ticket = {
  id: 1,
  origen_sistema: 'MAIA',
  solicitante: 'usuario.demo',
  asunto: 'Problema de acceso',
  descripcion: 'Necesito ayuda para ingresar.',
  categoria: 'FUNCIONAL',
  estado: 'EN_ATENCION',
  responsable: 'soporte_funcional',
  motivo_clasificacion: 'Revisión funcional.',
  respuesta_sugerida: null,
  respuesta_atencion: null,
  fecha_creacion: '2026-11-07T12:00:00Z',
  fecha_actualizacion: '2026-11-07T12:00:00Z'
};

const automatico: Ticket = {
  ...funcional,
  id: 2,
  asunto: '¿Dónde encuentro mis actividades?',
  categoria: 'AUTO',
  estado: 'PENDIENTE_CONFIRMACION',
  responsable: null,
  respuesta_sugerida: 'Ingresa al curso y revisa las actividades.'
};

describe('Mesa de Ayuda Inteligente', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [App],
      providers: [provideHttpClient(), provideHttpClientTesting()]
    }).compileComponents();
  });

  afterEach(() => {
    TestBed.inject(HttpTestingController).verify();
  });

  function iniciar(tickets: Ticket[] = []) {
    const fixture = TestBed.createComponent(App);
    fixture.detectChanges();
    const http = TestBed.inject(HttpTestingController);
    http.expectOne('/api/health').flush({ status: 'ok' });
    http.expectOne('/api/tickets').flush(tickets);
    fixture.detectChanges();
    return { fixture, http, app: fixture.componentInstance };
  }

  it('consulta la salud y el listado de la API', () => {
    const { fixture, app } = iniciar([]);
    expect(app.conexion()).toBe('conectada');
    expect(fixture.nativeElement.textContent).toContain('Mesa de Ayuda UNAD');
  });

  it('muestra cuando la API no responde', () => {
    const fixture = TestBed.createComponent(App);
    fixture.detectChanges();
    const http = TestBed.inject(HttpTestingController);
    http.expectOne('/api/health').flush(
      { detail: 'Servicio no disponible' },
      { status: 503, statusText: 'Service Unavailable' }
    );
    http.expectOne('/api/tickets').flush([]);
    fixture.detectChanges();
    expect(fixture.componentInstance.conexion()).toBe('sin-conexion');
  });

  it('muestra los indicadores de estado con tickets reales', () => {
    const { app, fixture } = iniciar([funcional, automatico]);
    expect(app.total()).toBe(2);
    expect(app.enAtencion()).toBe(1);
    expect(app.pendientes()).toBe(1);
    expect(app.resueltos()).toBe(0);
    expect(fixture.nativeElement.textContent).toContain('Últimas solicitudes');
  });

  it('crea una solicitud por POST y la presenta en el historial', () => {
    const { app, http } = iniciar([]);
    app.formulario = {
      origen_sistema: 'MAIA', solicitante: 'usuario.demo',
      asunto: 'Problema de acceso', descripcion: 'No puedo ingresar.'
    };
    app.crearTicket();
    const solicitud = http.expectOne('/api/tickets');
    expect(solicitud.request.method).toBe('POST');
    expect(solicitud.request.body.origen_sistema).toBe('MAIA');
    solicitud.flush(funcional);
    expect(app.tickets().length).toBe(1);
    expect(app.seleccion()?.id).toBe(1);
  });

  it('confirma una solución automática y marca el ticket resuelto', () => {
    const { app, http } = iniciar([automatico]);
    app.seleccionar(automatico);
    app.confirmar(true);
    const solicitud = http.expectOne('/api/tickets/2/confirmacion');
    expect(solicitud.request.method).toBe('POST');
    expect(solicitud.request.body).toEqual({ resuelta: true });
    solicitud.flush({ ...automatico, estado: 'RESUELTO' });
    expect(app.seleccion()?.estado).toBe('RESUELTO');
  });

  it('permite rechazar una sugerencia y remitirla a soporte', () => {
    const { app, http } = iniciar([automatico]);
    app.seleccionar(automatico);
    app.confirmar(false);
    http.expectOne('/api/tickets/2/confirmacion').flush({
      ...automatico, categoria: 'FUNCIONAL', estado: 'EN_ATENCION',
      responsable: 'soporte_funcional'
    });
    expect(app.seleccion()?.responsable).toBe('soporte_funcional');
  });

  it('registra la respuesta humana y cierra el caso', () => {
    const { app, http } = iniciar([funcional]);
    app.seleccionar(funcional);
    app.respuestaAtencion = 'Se restableció el acceso.';
    app.resolver();
    const solicitud = http.expectOne('/api/tickets/1/resolver');
    expect(solicitud.request.body).toEqual({ respuesta: 'Se restableció el acceso.' });
    solicitud.flush({
      ...funcional, estado: 'RESUELTO', respuesta_atencion: 'Se restableció el acceso.'
    });
    expect(app.seleccion()?.estado).toBe('RESUELTO');
    expect(app.respuestaAtencion).toBe('');
  });
});
