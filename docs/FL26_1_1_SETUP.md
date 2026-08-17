# FL26 v1.1 — instalación y primera captura

Target actual: **SP Football Life 2026 v1.1**.

## 1. No necesitas reiniciar tu Liga Master todavía

La base actual no modifica saves ni memoria. Puedes probar el bridge con cualquier partida.

Cuando lleguemos al primer `Transfer Injector`, se recomienda usar una **Liga Master nueva de prueba** para validar persistencia. Si funciona, entonces sí conviene empezar la carrera definitiva con el sistema activo desde el inicio.

## 2. Instalar el bridge

Copia:

```text
sider/modules/lm_ai_bridge.lua
```

hacia:

```text
<tu carpeta de Sider>/modules/lm_ai_bridge.lua
```

En `sider.ini` añade:

```ini
lua.module = "lm_ai_bridge.lua"
```

Inicia Football Life mediante tu flujo normal con Sider.

## 3. Comprobación

Al abrir el overlay de Sider debe aparecer algo similar a:

```text
LM AI Director 0.1.0-fl26.1.1 | OBSERVE | waiting for team context
```

Cuando FL26 determine el siguiente partido:

```text
LM AI Director 0.1.0-fl26.1.1 | OBSERVE | home:109 away:XXX
```

El módulo crea:

```text
<sider>/lm_ai_observations.csv
```

con registros como:

```text
START,0.1.0-fl26.1.1
SET_TEAMS,109,377
CONTEXT_RESET
```

## 4. Base Python

Desde la raíz del repositorio:

```bash
python -m pip install -e .
python -m lm_ai.cli --world examples/world.json --config config/fl26_1_1.json --seed 26 --output out/proposals.json
```

El archivo `out/proposals.json` contiene necesidades y candidatos de cada club de ejemplo.

## 5. Primera sesión de ingeniería inversa

Para FL26 v1.1 necesitamos capturar evidencia propia de esa versión.

Orden recomendado:

1. crear una Liga Master de prueba;
2. guardar antes de abrir el mercado;
3. identificar presupuesto de transferencias y salario con Cheat Engine;
4. cambiar una cifra dentro del juego y filtrar resultados;
5. identificar qué instrucciones leen/escriben esa dirección;
6. observar un fichaje normal realizado por el juego;
7. comparar memoria antes/después;
8. guardar, cerrar FL26 y volver a abrir;
9. comprobar qué estructuras persisten realmente.

## 6. Regla para offsets

No copiar offsets de PES 2021 Steam, FL25, FL26 v2.x ni otra build sin validarlos.

La configuración mantiene:

```json
"memory_write_enabled": false
```

hasta que tengamos una firma estable para v1.1.

## 7. Objetivo del primer hito de escritura

Una sola operación controlada:

```text
Jugador A
Club X -> Club Y
```

Debe cumplir simultáneamente:

- aparecer en Club Y;
- desaparecer de Club X;
- mantener contrato coherente;
- no romper gameplan/tácticas;
- sobrevivir a guardar/cerrar/reabrir la Liga Master.

Sólo después se conecta el AI Transfer Director.
