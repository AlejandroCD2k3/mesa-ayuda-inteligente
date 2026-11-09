"""Adaptador de IA con punto de inyección para pruebas."""
from urllib.request import urlopen
from .infrastructure.ai.openrouter import analizar_ticket_con_ia as _analizar


def analizar_ticket_con_ia(session, ticket):
    return _analizar(session, ticket, abrir=urlopen)
