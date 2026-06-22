# Roadmap de producto: plataforma de observabilidad de datos

Este documento resume los pasos recomendados para evolucionar la primera version de la app hacia una plataforma de observabilidad de datos realmente util para empresas.

## Vision

La plataforma no deberia limitarse a detectar anomalías aisladas. Deberia ayudar a un equipo de datos a responder rapido:

- Que dato esta roto.
- A quien impacta.
- Que tan grave es.
- Quien debe resolverlo.
- Como evitar que vuelva a pasar.
- Donde se integra con las herramientas actuales de la empresa.

## Estado actual

La app actual ya cubre una base importante:

- Creacion de datasets.
- Carga manual de snapshots CSV, TSV, TXT y Excel.
- Runs historicos por dataset.
- Profiling basico por columna:
  - row count.
  - tipo de dato.
  - null count.
  - null percentage.
  - mean, std, min y max para columnas numericas.
- Alertas por:
  - caida significativa de filas.
  - columnas nuevas.
  - columnas removidas.
  - cambio de tipo de dato.
  - aumento de nulls.
  - desplazamiento de media en columnas numericas.
- Estado general del dataset:
  - learning.
  - healthy.
  - warning.
  - critical.
- UI inicial para ver datasets, KPIs, runs y alertas.

## Brechas principales

Para acercarse a una herramienta empresarial faltan estas capacidades:

- Conectores reales: Postgres, Snowflake, BigQuery, Redshift, S3, dbt, Airflow u OpenLineage.
- Freshness y SLAs: saber cuando deberia actualizarse un dataset y alertar si no ocurre.
- Reglas configurables: thresholds, expectations y contratos por dataset o columna.
- Ownership: owner, equipo, dominio, criticidad y canal de contacto.
- Incidentes: estado, responsable, comentarios, resolucion, historial y deduplicacion de alertas.
- Lineage e impacto: entender que dashboards, tablas, modelos o pipelines dependen de un dataset roto.
- Reduccion de ruido: agrupacion de alertas, silencios, severidad inteligente y ventanas de evaluacion.
- Seguridad: usuarios, roles, permisos y auditoria.
- Escalabilidad: procesos asincronicos, scheduler, paginacion, retencion de metricas y workers.
- UX operacional: dashboard global, filtros, busqueda, drill-down por columna y tendencias historicas.

## Roadmap recomendado

### Fase 1: Convertir la demo en producto base

Objetivo: que un equipo pueda monitorear datasets manuales de forma confiable.

- Agregar metadata por dataset:
  - owner.
  - equipo.
  - dominio.
  - criticidad.
  - descripcion.
  - frecuencia esperada de actualizacion.
- Agregar freshness:
  - ultima ejecucion.
  - frecuencia esperada.
  - alerta si el dataset no se actualiza a tiempo.
- Agregar reglas configurables:
  - columnas requeridas.
  - columnas nullable / not nullable.
  - min y max permitidos.
  - valores aceptados.
  - unicidad.
  - regex para strings.
- Separar alertas de incidentes:
  - una alerta es un evento detectado.
  - un incidente es un problema operativo que puede agrupar varias alertas.
- Agregar estados de incidente:
  - open.
  - acknowledged.
  - resolved.
  - muted.
- Agregar tendencias historicas:
  - row count.
  - null rate.
  - cantidad de columnas.
  - cantidad de alertas.

### Fase 2: Integraciones minimas de valor

Objetivo: dejar de depender exclusivamente del upload manual.

- Agregar conector Postgres como primer conector.
- Permitir definir datasets desde una tabla o query SQL.
- Agregar scheduler para ejecutar checks periodicos.
- Exponer una API para que pipelines externos creen runs.
- Agregar alertas por webhook o Slack.
- Importar metadata de dbt:
  - modelos.
  - owners.
  - tags.
  - tests.
  - dependencias basicas.

### Fase 3: Data contracts y calidad avanzada

Objetivo: prevenir roturas y formalizar que significa "dato correcto".

- Crear expectations versionadas por dataset.
- Crear contratos de datos con:
  - schema esperado.
  - tipos esperados.
  - freshness esperado.
  - owner.
  - SLA.
  - checks obligatorios.
- Validar cambios antes de aceptarlos como saludables.
- Agregar checks avanzados:
  - duplicados.
  - cardinalidad.
  - percentiles.
  - distribucion.
  - outliers.
  - integridad referencial.
  - valores fuera de rango.
- Mejorar baselines:
  - comparar contra N runs anteriores.
  - usar medias moviles.
  - diferenciar dias habiles, fines de semana o estacionalidad.

### Fase 4: Lineage e impacto

Objetivo: priorizar problemas segun impacto real.

- Modelar entidades de lineage:
  - datasets.
  - jobs.
  - runs.
  - dependencias upstream.
  - dependencias downstream.
- Ingerir eventos compatibles con OpenLineage.
- Agregar vista de grafo o arbol de dependencias.
- Mostrar impacto en incidentes:
  - dashboards afectados.
  - tablas downstream.
  - modelos afectados.
  - consumidores afectados.
- Permitir ownership por dominio y por nodo de lineage.

### Fase 5: Capacidades enterprise

Objetivo: operar la plataforma en organizaciones reales.

- Autenticacion.
- Workspaces u organizaciones.
- Roles y permisos.
- Audit log.
- Retencion configurable de metricas.
- Paginacion, filtros y busqueda.
- Background workers para profiling y checks.
- Deploy dockerizado.
- Observabilidad de la propia plataforma.
- Reportes ejecutivos:
  - salud por dominio.
  - datasets mas problematicos.
  - alertas recurrentes.
  - tiempo medio de resolucion.
  - cumplimiento de SLAs.

## Prioridad practica

El orden recomendado para avanzar es:

1. Dataset ownership, criticidad y freshness.
2. Reglas configurables / expectations simples.
3. Incidentes con estado y responsable.
4. Conector Postgres y scheduler.
5. Historicos y tendencias visuales.
6. Lineage basico.
7. Seguridad, roles y capacidades enterprise.

## Criterio de producto

Antes de agregar features sofisticadas, conviene validar que la plataforma pueda cumplir este flujo:

1. Un dataset critico deja de actualizarse o llega con mala calidad.
2. La plataforma detecta el problema.
3. La alerta se agrupa en un incidente.
4. El incidente tiene severidad, owner e impacto claro.
5. El equipo responsable recibe la notificacion.
6. El usuario puede ver que cambio, desde cuando ocurre y que consumidores estan afectados.
7. El problema queda resuelto o documentado para evitar recurrencia.

Si este flujo funciona bien, la plataforma empieza a parecer una herramienta empresarial y no solo una demo de profiling.
