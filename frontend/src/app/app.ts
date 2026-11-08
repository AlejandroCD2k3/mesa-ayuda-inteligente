import { HttpClient } from '@angular/common/http';
import { Component, inject, OnInit, signal } from '@angular/core';

@Component({
  selector: 'app-root',
  templateUrl: './app.html',
  styleUrl: './app.css'
})
export class App implements OnInit {
  private readonly http = inject(HttpClient);

  protected readonly estado = signal<'comprobando' | 'conectada' | 'sin-conexion'>('comprobando');

  ngOnInit(): void {
    this.http.get<{ status: string }>('/api/health').subscribe({
      next: (respuesta) => {
        this.estado.set(respuesta.status === 'ok' ? 'conectada' : 'sin-conexion');
      },
      error: () => {
        this.estado.set('sin-conexion');
      }
    });
  }
}
