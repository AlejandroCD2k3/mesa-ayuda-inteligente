import { HttpClient } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { authHeaders } from '../../core/api/auth-headers';
import type { Ticket, TicketEvento } from '../../core/models';

@Injectable({ providedIn: 'root' })
export class TicketsApiService {
  private readonly http = inject(HttpClient);

  listar(token: string) {
    return this.http.get<Ticket[]>('/api/tickets', authHeaders(token));
  }

  eventos(id: number, token: string) {
    return this.http.get<TicketEvento[]>(
      `/api/tickets/${id}/eventos`, authHeaders(token)
    );
  }

  crear(datos: { origen_sistema: string; asunto: string; descripcion: string }, token: string) {
    return this.http.post<Ticket>('/api/tickets', datos, authHeaders(token));
  }

  confirmar(id: number, resuelta: boolean, token: string) {
    return this.http.post<Ticket>(
      `/api/tickets/${id}/confirmacion`, { resuelta }, authHeaders(token)
    );
  }

  resolver(id: number, respuesta: string, token: string) {
    return this.http.post<Ticket>(
      `/api/tickets/${id}/resolver`, { respuesta }, authHeaders(token)
    );
  }
}
