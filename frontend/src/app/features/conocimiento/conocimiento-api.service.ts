import { HttpClient } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { authHeaders } from '../../core/api/auth-headers';
import type { ArticuloConocimiento, CategoriaArticulo } from '../../core/models';

@Injectable({ providedIn: 'root' })
export class ConocimientoApiService {
  private readonly http = inject(HttpClient);

  listar(q: string, token: string) {
    return this.http.get<ArticuloConocimiento[]>('/api/conocimiento', {
      ...authHeaders(token),
      params: q ? { q } : {}
    });
  }

  crear(datos: {
    titulo: string;
    contenido: string;
    publicado: boolean;
    categoria: CategoriaArticulo;
  }, token: string) {
    return this.http.post<ArticuloConocimiento>(
      '/api/conocimiento', datos, authHeaders(token)
    );
  }

  actualizar(id: number, datos: {
    titulo: string;
    contenido: string;
    publicado: boolean;
  }, token: string) {
    return this.http.put<ArticuloConocimiento>(
      `/api/conocimiento/${id}`, datos, authHeaders(token)
    );
  }
}
