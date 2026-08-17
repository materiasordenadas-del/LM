# Arquitectura — LM AI Director

## Principio

Separar **decisión** de **inyección**.

```text
Football Life / Master League
          |
          v
    [ML Inspector]
          |
          | world snapshot
          v
 [Transfer Director]
          |
          | ranked proposals
          v
  [Market Resolver]
          |
          | approved transaction
          v
 [Transfer Injector]
          |
          v
Football Life / save state
```

## 1. ML Inspector

Responsabilidad futura: leer de FL26 v1.4 el estado real de:

- jugador -> club;
- edad, posición, OVR y datos de desarrollo;
- contratos;
- presupuesto de transferencias;
- presupuesto/techo salarial;
- plantillas completas;
- fecha/ventana de mercado;
- movimientos ya realizados.

El Inspector no decide fichajes.

## 2. Transfer Director

Ya implementado como primera base en `src/lm_ai/engine.py`.

Para cada club:

1. calcula carencias de profundidad y calidad por grupo posicional;
2. aplica hard gates;
3. puntúa candidatos supervivientes;
4. devuelve un shortlist ordenado.

### Hard gates

Se usan para impedir que la aleatoriedad produzca operaciones absurdas:

- salario incompatible;
- precio incompatible;
- estrella fuera del alcance de prestigio;
- jugador demasiado inferior para un club élite;
- club pequeño intentando quitar un titular prime protegido a un club muy superior.

### Score actual

```text
30% necesidad de plantilla
20% encaje de calidad
15% potencial
10% asequibilidad
10% prestigio
 5% edad
 5% situación de mercado/contrato
 5% variabilidad aleatoria
```

Los pesos son configurables en `config/fl26_1_4.json`.

## 3. Market Resolver — siguiente capa

El shortlist no debe convertirse directamente en un traspaso. El resolver deberá simular:

- varios clubes interesados;
- voluntad de venta del vendedor;
- competencia de ofertas;
- prioridad del jugador;
- disponibilidad de presupuesto después de operaciones previas;
- límite de entradas/salidas por ventana;
- reemplazo antes de vender en posiciones críticas.

Resultado: `approved transaction`.

## 4. Transfer Injector — bloqueado actualmente

Nunca debe modificar únicamente un supuesto `team_id` del jugador. Un traspaso puede implicar varias estructuras sincronizadas: roster, contrato, tácticas, estado de ML y persistencia del save.

Objetivo técnico preferido:

1. localizar la rutina nativa de FL26 v1.4 que finaliza un traspaso;
2. observar sus argumentos/estructuras;
3. reproducir una operación controlada;
4. verificar persistencia después de guardar/cerrar/reabrir;
5. sólo entonces habilitar el Director automático.

## 5. Sider Bridge

`sider/modules/lm_ai_bridge.lua` es deliberadamente conservador.

Actualmente usa eventos documentados de Sider:

- `set_teams`;
- `context_reset`;
- `overlay_on`.

Más adelante puede evolucionar a:

- lectura con `memory.read`;
- búsqueda por firma con `memory.search_process`;
- custom events de Sider 7.3+;
- escritura únicamente detrás de validaciones de versión/firma.

Documentación técnica oficial de referencia:

- https://mapote.com/doc/sider/sider7/scripting.html
- https://mapote.com/doc/sider/sider7/custom-events.html

## 6. Club identity

La siguiente versión debe ampliar `archetype` a perfiles dinámicos:

- `elite` — alta exigencia de OVR, baja venta de titulares, capacidad de atraer estrellas;
- `contender` — busca salto de calidad y oportunidades;
- `developer` — juventud/potencial, mayor propensión a vender;
- `midtable` — valor, necesidad y sostenibilidad;
- `survival` — experiencia, cesiones, agentes libres y bajo coste.

El arquetipo es una base, no una etiqueta eterna. Resultados, ascensos, Europa y finanzas deberán modificar el perfil con las temporadas.
