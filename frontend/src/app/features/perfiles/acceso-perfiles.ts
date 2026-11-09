import { Component, EventEmitter, Input, Output } from '@angular/core';
import type { UsuarioDemo } from '../../core/models';

@Component({
  selector: 'app-acceso-perfiles',
  templateUrl: './acceso-perfiles.html'
})
export class AccesoPerfiles {
  @Input({ required: true }) perfiles: UsuarioDemo[] = [];
  @Input() error = '';
  @Input() iniciando = false;
  @Output() readonly seleccionar = new EventEmitter<string>();
}
