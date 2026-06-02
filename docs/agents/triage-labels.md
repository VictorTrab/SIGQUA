# Triage labels

Las skills globales usan cinco estados canonicos. En SIGQUA se representan como texto dentro de los archivos Markdown locales.

| Rol canonico | Estado local | Significado |
| --- | --- | --- |
| `needs-triage` | `needs-triage` | Requiere evaluacion inicial. |
| `needs-info` | `needs-info` | Falta informacion del usuario o del codigo. |
| `ready-for-agent` | `ready-for-agent` | Esta especificado para implementacion por agente. |
| `ready-for-human` | `ready-for-human` | Requiere decision o implementacion humana. |
| `wontfix` | `wontfix` | No se va a ejecutar. |

Usar la linea `Estado: <estado>` en PRD o issues locales cuando aplique.
