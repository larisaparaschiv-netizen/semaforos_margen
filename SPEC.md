# Herramienta de margen de proyectos — Especificación V1

> Documento de referencia para construir la herramienta. Es la **fuente de verdad**: cualquier
> cambio de reglas se actualiza aquí primero. Pensado para arrancar el desarrollo en Claude Code.

---

## 1. Objetivo y alcance de la V1

Un **procesador de datos** que cruza los ficheros financieros de la compañía y muestra, por
proyecto, el **margen real (actuals) frente al margen presupuestado**, con un semáforo de color.

**Principios:** «menos es más» (simplicidad y adopción), consistencia con los sistemas
corporativos, y fuente de datos desacoplada (carga manual ahora, conectores después: solo
cambia la capa de carga).

**Entra en V1**
- Margen real por proyecto: ingresos − costes reales.
- Comparación contra el margen presupuestado (carga manual).
- Semáforo de margen con color (umbral 2,5 %–5 %).
- Desglose mensual por proyecto: ingresos, coste de salarios, otros costes, margen y **horas por departamento (Vertical)**.
- Solo se muestran los proyectos marcados **TO Launch = TRUE** en el presupuesto.

**No entra (backlog)**
- Proyección de margen/coste a cierre y otros semáforos (avance, consumo, recursos, fiabilidad).
- Vista por departamentos y reparto de ingresos/costes (STV).
- Microproyectos, alertas de imputación, traducción horas↔dinero avanzada, gestión de riesgos integrada.

---

## 2. Los cuatro ficheros de entrada

### 2.1 Horas (report de Power BI · carpeta `informe_globant`)
- **Conexión ideal:** directa a Power BI; de momento export.
- **Grano:** una fila por persona, día, proyecto y tarea.
- **Columnas:** `Portfolio Name`, `Client`, `Project`, `e-Mail`, `Date`, `Task Name`, `Hours`, `Costo`, `Vertical`, `Cluster`.
- **Uso:**
  - Coste de salarios del **mes en curso** (columna `Costo`).
  - Desglose de **horas por departamento** = `Vertical` (dentro de `Cluster`, que es la unidad de negocio).

### 2.2 Actuals cerrados (export tipo SAP · ej. "Example Project Margin")
- **Origen:** sale del sistema; Larisa **consolida los meses cerrados** nuevos cada mes.
- **Grano:** una fila por apunte contable.
- **Columnas clave:** `PeriodoYYYYMM` (mes), `Concepto` (`Revenue Labor` / `Costs`), `CC`
  (subcategoría: Salaries & Wages, Office Expenses, Professional Service, Travel Expenses,
  Reimbursable…), `EnMLCeBe` (importe en EUR), `Client`, `Project`, `Glober` (persona),
  `ContractType` (FEE, TYM, SLA, FIXED_PRICE…).
- **Uso (meses cerrados):** ingreso y coste reales, con desglose por CC, por persona (`Glober`) y por tipo de contrato.
- **Signo:** el ingreso (`Revenue Labor`) viene **en negativo** y el coste (`Costs`) en positivo →
  se **invierte el signo del ingreso**. Margen = (−ΣRevenue) − ΣCosts.

### 2.3 Billing / ingresos esperados
- **Grano:** una fila por proyecto y mes.
- **Columnas clave:** `Billing MONTH`, `Type of Billing`, `Project`, `Final Billing LC`,
  `Currency`, `Actual FX Rate`, `Final Billing USD`, `Actual Status`, `Client`, `Cliente Origen`.
- **Uso:** ingreso del **mes en curso y futuros** = suma de `Final Billing LC` (en **EUR**),
  sobre las filas que cuentan.
- **Filtro:** las categorías de `Type of Billing` y los `Actual Status` que cuentan se definen en
  configuración (o vienen prefiltrados por Larisa). El procesador solo suma lo que recibe/le indican.

### 2.4 Presupuesto (manual · plantilla `Plantilla_Presupuesto_Proyectos.xlsx`)
- **Origen:** construido a mano por Larisa con los datos internos de los heads.
- **Grano:** una fila por proyecto y año.
- **Columnas:** `Cliente Origen`, `Project`, `Año`, `Tipo de contrato`, `Ingreso presupuestado (€)`,
  `Coste presupuestado (€)`, `Margen presupuestado (%)`, `Margen € / % (calculado)`,
  `Responsable`, `Fecha inicio`, `Fecha fin prevista`, `Estado`, `Fecha actualización`, `Notas`,
  **`TO Launch`** (checkbox TRUE/FALSE).
- **Uso:**
  - Margen presupuestado, referencia del semáforo (ingreso+coste, o ingreso+margen %).
  - **`TO Launch` = TRUE** define qué proyectos se muestran en la herramienta.

---

## 3. Clave de unión y validación

- **Clave única de toda la información:** `Cliente Origen` + `Project`.
  - En billing el cliente es `Cliente Origen`; en actuals es la columna `Client`; en horas es `Client`.
  - Deben coincidir porque todos derivan del mismo sistema previo.
- **Alerta de no casados (obligatoria):** la validación lista los `Cliente + Project` que aparecen
  en un fichero y no encuentran pareja en otro (hay ingreso sin coste, nombre escrito distinto,
  proyecto sin presupuesto, etc.). **Nunca se descarta una fila en silencio**: se muestra para corregir en origen.
- Normalización de texto (espacios, mayúsculas) antes de cruzar.

---

## 4. Reglas de cálculo

Todo se agrega a **proyecto × mes**. Universo de proyectos = presupuesto con `TO Launch = TRUE`.

**Ingreso del mes**
- Mes **cerrado** → actuals: `−Σ(EnMLCeBe where Concepto = "Revenue Labor")`.
- Mes **en curso / futuro** → billing: `Σ(Final Billing LC en EUR)` de las filas que cuentan.
- **Nunca de los dos** a la vez: cada mes es cerrado *o* abierto.

**Coste del mes**
- Mes **cerrado** → actuals: `Σ(EnMLCeBe where Concepto = "Costs")` (todas las subcategorías), guardando el desglose por `CC`.
- Mes **en curso** → horas: `Σ(Costo)` del report de Power BI.
  - *Nota:* en el mes en curso el coste son solo salarios (otros costes no existen hasta el cierre). Marcar/aceptar.

**Margen**
- `Margen € = Ingreso − Coste`; `Margen % = Margen € / Ingreso`.
- Margen presupuestado: del fichero de presupuesto.

**Semáforo de margen** (desviación margen % real vs margen % presupuestado, en puntos porcentuales)
- 🟢 Verde: desviación ≤ 2,5 pp
- 🟡 Ámbar: 2,5 – 5 pp
- 🔴 Rojo: > 5 pp
- *(umbral exacto pendiente de confirmar; ver §7)*

**Constantes**
- Moneda: **EUR**.
- Departamento = `Vertical`; unidad de negocio = `Cluster`.

---

## 5. Salidas (qué plasma)

- **Vista 1 — tabla por proyecto** (solo `TO Launch = TRUE`): semáforo de margen + ingreso,
  coste, margen €/%, margen presupuestado y desviación.
- **Vista 2 — drill-down mensual por proyecto:** por mes → ingreso, coste (salarios + otros por
  `CC`), margen, **horas por Vertical**, y detalle por persona (`Glober`).
- **Panel de alertas:** no casados, proyectos sin presupuesto, filas fuera de cuadre.
- Salida técnica: un **dataset procesado** (parquet/SQLite/CSV) que alimenta la vista o el BI.

---

## 6. Arquitectura y estructura de proyecto

Pipeline con la **fuente desacoplada**: al pasar de Excel a conectores solo cambia `loaders/`.

```
herramienta-margen/
├── data/                # ficheros de entrada (manual ahora)
├── config/
│   └── settings.py      # umbral del semáforo, categorías/estados que cuentan, mes en curso, moneda
├── src/
│   ├── loaders/         # un módulo por fuente; misma interfaz (manual → conector)
│   │   ├── horas.py
│   │   ├── actuals.py
│   │   ├── billing.py
│   │   └── presupuesto.py
│   ├── validate.py      # claves, no casados, tipos, normalización de nombres
│   ├── model.py         # normaliza a tabla canónica: proyecto × mes × concepto × escenario
│   ├── metrics.py       # margen y semáforo (funciones puras, testeables)
│   └── output.py        # construye las tablas de salida / dataset procesado
├── tests/               # tests de metrics y validate con datos de ejemplo
├── main.py              # orquesta: load → validate → model → metrics → output
└── SPEC.md              # este documento
```

- **Librería base:** `pandas`.
- Cada loader devuelve un DataFrame con columnas canónicas (renombradas), de modo que el resto del
  pipeline no conoce los nombres originales de cada fichero.
- `metrics.py` y `validate.py` son **funciones puras** → fáciles de testear con casos pequeños
  (incluido el ejemplo del margen ≈ 450.589 € del fichero de actuals).

---

## 7. Decisiones abiertas (mantener en el repo)

1. **Umbral exacto** del semáforo y análisis de impacto en el margen global de la compañía.
2. **Categorías y estados** de billing que cuentan (lista en `config`).
3. **Otros costes del mes en curso:** no existen hasta el cierre → el margen del mes abierto es
   «solo salarios» en coste. ¿Se acepta o se marca como provisional?
4. **Nombres no casados:** ¿se corrigen en origen o se mantiene una tabla de equivalencias?
5. **Permisos:** los costes salariales son sensibles → definir quién ve qué.

---

## 8. Backlog (para versiones posteriores)

Proyección de margen a cierre y métodos de coste (% avance / actuals+presupuesto / run-rate /
reestimación del PM); consumo de presupuesto y demás semáforos; vista por departamentos y reparto
(STV); microproyectos y umbral mínimo; mapeo de otros costes en mes abierto; coste de trainees;
alertas y cierre semanal de imputación; niveles de detalle por rol; gestión de riesgos integrada.
