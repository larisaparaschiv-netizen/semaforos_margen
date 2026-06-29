#!/usr/bin/env python3
"""
Interfaz web interactiva para la herramienta de margen de proyectos.
Ejecutar con: streamlit run streamlit_app.py
"""

import streamlit as st
import pandas as pd
import os
from pathlib import Path

# Configuración de la página
st.set_page_config(
    page_title="📊 Margen de Proyectos",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados
st.markdown("""
<style>
    .main-header {
        color: #1f77b4;
        text-align: center;
        margin-bottom: 30px;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .green { color: #09ab3b; font-weight: bold; }
    .amber { color: #ffa500; font-weight: bold; }
    .red { color: #d32f2f; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# Título
st.markdown("""
# 📊 Herramienta de Margen de Proyectos
**Dashboard interactivo** — Visualiza ingresos, costes, margen y semáforo por proyecto
""")

# ============================================================================
# SIDEBAR
# ============================================================================

st.sidebar.title("⚙️ Configuración")

with st.sidebar:
    st.subheader("📁 Cargar Datos")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🚀 Ejecutar Demo", use_container_width=True):
            st.session_state.run_demo = True

    with col2:
        uploaded_files = st.file_uploader(
            "📤 O sube archivos",
            accept_multiple_files=True,
            type=['csv', 'xlsx']
        )

    st.divider()

    st.subheader("📚 Información")
    st.markdown("""
    **Ficheros esperados:**
    - `presupuesto.xlsx` - Presupuesto de proyectos
    - `actuals.csv` - Datos reales (SAP)
    - `horas.csv` - Horas trabajadas (Power BI)
    - `billing.csv` - Ingresos esperados

    **Archivos generados:**
    - `proyectos_margen.csv`
    - `metricas_mes.csv`
    - `alertas.csv`
    """)


# ============================================================================
# FUNCIONES
# ============================================================================

def load_csv(filepath):
    """Carga un CSV con manejo de errores."""
    try:
        return pd.read_csv(filepath)
    except Exception as e:
        st.error(f"Error cargando {filepath}: {e}")
        return None


def format_semaforo(valor):
    """Formatea el semáforo con emoji."""
    if valor == 'verde':
        return '🟢 Verde'
    elif valor == 'ambar':
        return '🟡 Ámbar'
    elif valor == 'rojo':
        return '🔴 Rojo'
    return valor


def format_currency(value):
    """Formatea números como moneda."""
    try:
        return f"€{value:,.0f}"
    except:
        return value


# ============================================================================
# CARGAR DATOS
# ============================================================================

output_dir = Path('./output')
has_data = False
df_proyectos = None
df_metricas = None
df_alertas = None

# Intenta cargar datos existentes
if output_dir.exists():
    proyectos_file = output_dir / 'proyectos_margen.csv'
    metricas_file = output_dir / 'metricas_mes.csv'
    alertas_file = output_dir / 'alertas.csv'

    if proyectos_file.exists():
        df_proyectos = load_csv(proyectos_file)
        has_data = True

    if metricas_file.exists():
        df_metricas = load_csv(metricas_file)

    if alertas_file.exists():
        df_alertas = load_csv(alertas_file)

# ============================================================================
# MAIN CONTENT
# ============================================================================

if not has_data:
    st.info("""
    ### 👋 Bienvenido

    Para ver datos, tienes dos opciones:

    **Opción 1:** Haz clic en **"🚀 Ejecutar Demo"** en la izquierda
    - Genera datos de prueba automáticamente

    **Opción 2:** Usa el script desde terminal
    ```bash
    pip install -r requirements.txt
    python3 demo.py
    streamlit run streamlit_app.py
    ```
    """)

else:
    # TAB 1: Proyectos (principal)
    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 Proyectos",
        "📅 Detalles Mensuales",
        "⚠️ Alertas",
        "ℹ️ Información"
    ])

    # ========================================================================
    # TAB 1: TABLA DE PROYECTOS
    # ========================================================================
    with tab1:
        st.subheader("Margen por Proyecto")

        if df_proyectos is not None and len(df_proyectos) > 0:

            # Métricas principales
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                total_ingreso = df_proyectos['ingreso'].sum()
                st.metric(
                    "💰 Ingreso Total",
                    format_currency(total_ingreso),
                    delta=None
                )

            with col2:
                total_coste = df_proyectos['coste'].sum()
                st.metric(
                    "📊 Coste Total",
                    format_currency(total_coste),
                    delta=None
                )

            with col3:
                total_margen = df_proyectos['margen_eur'].sum()
                st.metric(
                    "💹 Margen Total",
                    format_currency(total_margen),
                    delta=f"{(total_margen/total_ingreso*100):.1f}%" if total_ingreso > 0 else "0%"
                )

            with col4:
                semaforos = df_proyectos['semaforo'].value_counts()
                verdes = semaforos.get('verde', 0)
                st.metric(
                    "📊 Proyectos",
                    len(df_proyectos),
                    delta=f"{verdes}🟢 / {len(df_proyectos)}"
                )

            st.divider()

            # Tabla principal
            st.markdown("### Detalles por Proyecto")

            # Prepara los datos para mostrar
            df_display = df_proyectos.copy()
            df_display['semaforo'] = df_display['semaforo'].apply(format_semaforo)
            df_display['ingreso'] = df_display['ingreso'].apply(format_currency)
            df_display['coste'] = df_display['coste'].apply(format_currency)
            df_display['margen_eur'] = df_display['margen_eur'].apply(format_currency)
            df_display['margen_pct'] = df_display['margen_pct'].apply(lambda x: f"{x:.1f}%")

            # Reordena columnas
            cols_order = ['cliente_origen', 'proyecto', 'ingreso', 'coste', 'margen_eur', 'margen_pct', 'semaforo']
            df_display = df_display[[col for col in cols_order if col in df_display.columns]]

            st.dataframe(
                df_display,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "cliente_origen": "Cliente",
                    "proyecto": "Proyecto",
                    "ingreso": "Ingreso",
                    "coste": "Coste",
                    "margen_eur": "Margen €",
                    "margen_pct": "Margen %",
                    "semaforo": "Semáforo"
                }
            )

            # Gráfico de semáforos
            st.markdown("### Distribución de Semáforos")
            semaforo_counts = df_proyectos['semaforo'].value_counts()

            col1, col2 = st.columns(2)

            with col1:
                st.bar_chart(semaforo_counts, color=['#09ab3b', '#ffa500', '#d32f2f'])

            with col2:
                # Tabla pequeña
                st.metric("🟢 Verde", semaforo_counts.get('verde', 0))
                st.metric("🟡 Ámbar", semaforo_counts.get('ambar', 0))
                st.metric("🔴 Rojo", semaforo_counts.get('rojo', 0))

        else:
            st.warning("No hay datos de proyectos disponibles")

    # ========================================================================
    # TAB 2: DETALLES MENSUALES
    # ========================================================================
    with tab2:
        st.subheader("Evolución Mensual por Proyecto")

        if df_metricas is not None and len(df_metricas) > 0:

            # Filtro por proyecto
            proyectos = sorted(df_metricas['proyecto'].unique())
            proyecto_sel = st.selectbox(
                "Selecciona un proyecto",
                proyectos,
                key="proyecto_select"
            )

            # Filtra datos
            df_mes_filtrado = df_metricas[df_metricas['proyecto'] == proyecto_sel]

            if len(df_mes_filtrado) > 0:
                # Métricas
                col1, col2, col3 = st.columns(3)

                with col1:
                    avg_margen = df_mes_filtrado['margen_pct'].mean()
                    st.metric("Margen % Promedio", f"{avg_margen:.1f}%")

                with col2:
                    total_ing = df_mes_filtrado['ingreso'].sum()
                    st.metric("Ingreso Total", format_currency(total_ing))

                with col3:
                    total_cost = df_mes_filtrado['coste'].sum()
                    st.metric("Coste Total", format_currency(total_cost))

                st.divider()

                # Tabla de meses
                st.markdown(f"### Detalle Mensual: {proyecto_sel}")

                df_display = df_mes_filtrado.copy()
                df_display['es_cerrado'] = df_display['es_cerrado'].apply(
                    lambda x: '✅ Cerrado' if x else '📝 Abierto'
                )
                df_display['semaforo'] = df_display['semaforo'].apply(format_semaforo)
                df_display['ingreso'] = df_display['ingreso'].apply(format_currency)
                df_display['coste'] = df_display['coste'].apply(format_currency)
                df_display['margen_eur'] = df_display['margen_eur'].apply(format_currency)
                df_display['margen_pct'] = df_display['margen_pct'].apply(lambda x: f"{x:.1f}%")

                cols = ['mes', 'es_cerrado', 'ingreso', 'coste', 'margen_eur', 'margen_pct', 'semaforo']
                df_display = df_display[[col for col in cols if col in df_display.columns]]

                st.dataframe(
                    df_display,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "mes": "Mes",
                        "es_cerrado": "Estado",
                        "ingreso": "Ingreso",
                        "coste": "Coste",
                        "margen_eur": "Margen €",
                        "margen_pct": "Margen %",
                        "semaforo": "Semáforo"
                    }
                )

                # Gráfico de evolución
                st.markdown("### Evolución del Margen")
                df_chart = df_mes_filtrado[['mes', 'margen_pct']].sort_values('mes')
                df_chart = df_chart.set_index('mes')
                st.line_chart(df_chart, color='#1f77b4')

        else:
            st.warning("No hay datos mensuales disponibles")

    # ========================================================================
    # TAB 3: ALERTAS
    # ========================================================================
    with tab3:
        st.subheader("Panel de Validación")

        if df_alertas is not None and len(df_alertas) > 0:

            # Resumen
            alert_counts = df_alertas['alert_type'].value_counts()

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("⚠️ Total Alertas", len(df_alertas))

            with col2:
                tipos = len(alert_counts)
                st.metric("📊 Tipos de Alerta", tipos)

            with col3:
                st.metric("📁 Proyectos Afectados", df_alertas['proyecto'].nunique())

            st.divider()

            # Tabla de alertas
            st.markdown("### Detalle de Alertas")

            df_display = df_alertas.copy()
            df_display['alert_type'] = df_display['alert_type'].apply(
                lambda x: f"⚠️ {x}" if pd.notna(x) else ""
            )

            st.dataframe(
                df_display[['alert_type', 'cliente', 'proyecto', 'details']],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "alert_type": "Tipo",
                    "cliente": "Cliente",
                    "proyecto": "Proyecto",
                    "details": "Detalles"
                }
            )

            # Resumen por tipo
            st.markdown("### Resumen por Tipo")
            st.bar_chart(alert_counts)

        else:
            st.success("✅ No hay alertas. Los datos están alineados.")

    # ========================================================================
    # TAB 4: INFORMACIÓN
    # ========================================================================
    with tab4:
        st.subheader("ℹ️ Acerca de la Herramienta")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("""
            ### 📊 Funcionalidades

            ✅ **Carga de datos** desde 4 fuentes
            - Actuals (SAP)
            - Horas (Power BI)
            - Billing (ingresos)
            - Presupuesto (manual)

            ✅ **Validación automática**
            - Claves únicas (Cliente + Proyecto)
            - Detección de "no casados"
            - Alertas de inconsistencias

            ✅ **Cálculo de margen**
            - Margen € = Ingreso - Coste
            - Margen % = Margen € / Ingreso
            - Distinción: meses cerrados vs abiertos
            """)

        with col2:
            st.markdown("""
            ### 🎨 Semáforo

            **🟢 Verde:** Desviación ≤ 2.5 pp
            - Margen real muy cercano al presupuestado

            **🟡 Ámbar:** Desviación > 2.5 pp y ≤ 5 pp
            - Margen real moderadamente diferente

            **🔴 Rojo:** Desviación > 5 pp
            - Margen real muy diferente al presupuestado

            ### 📈 Métricas

            - **Ingreso:** Suma de ingresos (actuals o billing)
            - **Coste:** Suma de costes (actuals o horas)
            - **Margen:** Diferencia (ingreso - coste)
            """)

        st.divider()

        st.markdown("""
        ### 🚀 Cómo usar

        1. **Demo automático:** Clic en "🚀 Ejecutar Demo" en la izquierda
        2. **Con tus datos:** Sube archivos CSV/Excel
        3. **Por terminal:** `python3 main.py --presupuesto ... --actuals ...`

        ### 📚 Documentación

        - `README.md` - Uso y características
        - `SPEC.md` - Especificación técnica
        - `INSTALL.md` - Instalación

        ### 📧 Requisitos

        - Python 3.9+
        - pandas
        - openpyxl
        - streamlit (para esta interfaz)
        """)


# ============================================================================
# FOOTER
# ============================================================================

st.divider()
st.markdown("""
<center>
    <small>
        🎯 <b>Herramienta de Margen de Proyectos</b> v1.0
        | 91 tests passing ✅
        | Desarrollado con Streamlit
    </small>
</center>
""", unsafe_allow_html=True)
