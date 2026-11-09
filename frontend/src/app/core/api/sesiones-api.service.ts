import { HttpClient } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import type { UsuarioDemo } from '../models';

@Injectable({ providedIn: 'root' })
export class SesionesApiService {
  private readonly http = inject(HttpClient);

  salud() {
    return this.http.get<{ status: string }>('/api/health');
  }

  perfiles() {
    return this.http.get<UsuarioDemo[]>('/api/demo/usuarios');
  }

  iniciar(id: string) {
    return this.http.post<{ token: string; usuario: UsuarioDemo }>(
      '/api/demo/sesion',
      { usuario_id: id }
    );
  }
}
