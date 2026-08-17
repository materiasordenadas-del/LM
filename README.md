# LM AI Director

Base experimental para convertir la Liga Master de **SP Football Life 2026 v1.1 / PES 2021** en un mercado más vivo y coherente.

## Objetivo

No aumentar fichajes al azar. El objetivo es que cada club compre y venda según:

- necesidad real de plantilla;
- nivel y prestigio del club;
- presupuesto y estructura salarial;
- edad, OVR y potencial del jugador;
- perfil comprador/vendedor del club;
- contexto competitivo;
- una pequeña dosis de aleatoriedad controlada.

Ejemplo esperado:

- Real Madrid necesita lateral derecho -> prioriza laterales de nivel élite o jóvenes de potencial élite.
- Un club de media tabla -> prioriza oportunidades, préstamos, jugadores de nivel compatible y jóvenes alcanzables.
- Un club desarrollador -> compra joven, desarrolla y acepta vender cuando llega una oferta de un club superior.

## Estado actual

**Fase 0 / Base funcional.**

Incluye:

1. modelo de jugadores y clubes;
2. cálculo de necesidades por posición;
3. filtros duros de realismo;
4. scoring de candidatos;
5. generación determinista de propuestas de mercado;
6. perfiles/arquetipos de clubes;
7. configuración específica para FL26 v1.1;
8. módulo Sider seguro que registra equipos observados durante Liga Master sin escribir memoria;
9. contrato preparado para añadir después el inyector de transferencias.

La primera versión **NO escribe aún fichajes dentro de una Liga Master activa**. Eso queda deliberadamente bloqueado hasta identificar y validar la rutina/estructura correcta de FL26 v1.1. No se incluyen offsets inventados.

## Inicio rápido

```bash
python -m pip install -e .
python -m lm_ai.cli \
  --world examples/world.json \
  --config config/fl26_1_1.json \
  --seed 26 \
  --output out/proposals.json
```

Ejecutar tests:

```bash
python -m unittest discover -s tests -v
```

## Sider

Copiar:

```text
sider/modules/lm_ai_bridge.lua
```

a la carpeta `modules` de tu Sider y añadir a `sider.ini`:

```ini
lua.module = "lm_ai_bridge.lua"
```

El bridge actual es sólo de observación. Registra `set_teams` y `context_reset`, y muestra estado en el overlay. No modifica memoria ni saves.

Ver `docs/FL26_1_1_SETUP.md` y `docs/ARCHITECTURE.md`.

## Roadmap inmediato

- **P1 — ML Inspector:** localizar estructuras de club/jugador/contrato/presupuesto en FL26 v1.1.
- **P2 — Market Observer:** observar cuándo la Liga Master genera actividad de mercado.
- **P3 — Transfer Injector:** ejecutar un único traspaso controlado y persistente en un save de prueba.
- **P4 — Frequency Hook:** aumentar intentos de mercado sin perder lógica.
- **P5 — AI Director:** conectar el motor de scoring con el inyector.
- **P6 — Eventos de carrera y regeneración juvenil.**

## Principio de seguridad del proyecto

Nunca escribir en memoria basándonos sólo en offsets de otra versión de PES/Football Life. Cada firma para FL26 v1.1 debe validarse antes de habilitar escritura.
