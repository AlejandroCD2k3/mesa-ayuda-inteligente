import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { App } from './app';

describe('App', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [App],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting()
      ]
    }).compileComponents();
  });

  afterEach(() => {
    TestBed.inject(HttpTestingController).verify();
  });

  it('muestra el estado mientras consulta la API', () => {
    const fixture = TestBed.createComponent(App);
    fixture.detectChanges();

    const http = TestBed.inject(HttpTestingController);
    const solicitud = http.expectOne({
      method: 'GET',
      url: '/api/health'
    });

    expect(fixture.nativeElement.textContent).toContain('Comprobando conexión');

    solicitud.flush({ status: 'ok' });
  });

  it('muestra el estado conectado cuando FastAPI responde correctamente', () => {
    const fixture = TestBed.createComponent(App);
    fixture.detectChanges();

    const http = TestBed.inject(HttpTestingController);
    const solicitud = http.expectOne('/api/health');

    expect(solicitud.request.method).toBe('GET');

    solicitud.flush({ status: 'ok' });
    fixture.detectChanges();

    expect(fixture.nativeElement.textContent).toContain('API conectada');
  });

  it('muestra un error cuando FastAPI no esta disponible', () => {
    const fixture = TestBed.createComponent(App);
    fixture.detectChanges();

    const http = TestBed.inject(HttpTestingController);
    const solicitud = http.expectOne('/api/health');

    solicitud.flush(
      { detail: 'Servicio no disponible' },
      { status: 503, statusText: 'Service Unavailable' }
    );

    fixture.detectChanges();

    expect(fixture.nativeElement.textContent).toContain('Sin conexión con la API');
  });
});
