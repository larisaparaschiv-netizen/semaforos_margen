"""Cálculo de métricas: margen y semáforo."""

import pandas as pd
from typing import Dict, List, Tuple
from enum import Enum


class TrafficLight(Enum):
    """Colores del semáforo."""
    GREEN = 'verde'
    AMBER = 'ambar'
    RED = 'rojo'


def calculate_margin_eur(ingreso: float, coste: float) -> float:
    """
    Calcula el margen en EUR.

    Margen € = Ingreso − Coste

    Args:
        ingreso: ingresos en EUR
        coste: costes en EUR

    Returns:
        Margen en EUR
    """
    return ingreso - coste


def calculate_margin_pct(ingreso: float, coste: float) -> float:
    """
    Calcula el margen en porcentaje.

    Margen % = Margen € / Ingreso = (Ingreso − Coste) / Ingreso

    Args:
        ingreso: ingresos en EUR
        coste: costes en EUR

    Returns:
        Margen en porcentaje (0-100), o 0 si ingreso es 0
    """
    if ingreso == 0:
        return 0.0
    return ((ingreso - coste) / ingreso) * 100


def calculate_traffic_light(
    margen_pct_real: float,
    margen_pct_presupuestado: float,
    green_threshold: float = 2.5,
    amber_threshold: float = 5.0,
) -> TrafficLight:
    """
    Determina el semáforo según la desviación entre margen real y presupuestado.

    Desviación = |Margen % real − Margen % presupuestado|

    - Verde: desviación ≤ green_threshold pp
    - Ámbar: green_threshold < desviación ≤ amber_threshold pp
    - Rojo: desviación > amber_threshold pp

    Args:
        margen_pct_real: margen porcentual real
        margen_pct_presupuestado: margen porcentual presupuestado
        green_threshold: umbral verde en puntos porcentuales (default 2.5)
        amber_threshold: umbral ámbar en puntos porcentuales (default 5.0)

    Returns:
        TrafficLight (GREEN, AMBER, o RED)
    """
    desviacion = abs(margen_pct_real - margen_pct_presupuestado)

    if desviacion <= green_threshold:
        return TrafficLight.GREEN
    elif desviacion <= amber_threshold:
        return TrafficLight.AMBER
    else:
        return TrafficLight.RED


def aggregate_by_proyecto_mes(
    actuals_df: pd.DataFrame,
    horas_df: pd.DataFrame,
    billing_df: pd.DataFrame,
    presupuesto_df: pd.DataFrame,
    current_month: str,
) -> pd.DataFrame:
    """
    Agrega ingresos y costes por proyecto × mes.

    Para meses cerrados: usa actuals (ingresos y costes).
    Para mes actual/futuro: usa billing para ingresos y horas para costes del mes en curso.

    Args:
        actuals_df: DataFrame de actuals con columnas (periodo, cliente, proyecto, concepto, importe, ...)
        horas_df: DataFrame de horas con columnas (fecha, cliente, proyecto, horas, costo, ...)
        billing_df: DataFrame de billing con columnas (mes, cliente_origen, proyecto, importe_eur, ...)
        presupuesto_df: DataFrame de presupuesto con columnas (cliente_origen, proyecto, ...)
        current_month: mes actual en formato YYYYMM

    Returns:
        DataFrame agregado con columnas:
        - cliente_origen, proyecto, mes
        - ingreso, coste, margen_eur, margen_pct
        - ingreso_presupuestado, coste_presupuestado, margen_pct_presupuestado
        - desviacion_pct, semaforo
    """
    results = []

    # Obtén los proyectos válidos del presupuesto
    presupuesto_launch = presupuesto_df[presupuesto_df.get('to_launch', False) == True].copy()

    for _, presup_row in presupuesto_launch.iterrows():
        cliente = presup_row['cliente_origen']
        proyecto = presup_row['proyecto']

        # Normaliza para búsqueda
        cliente_norm = str(cliente).strip().upper()
        proyecto_norm = str(proyecto).strip().upper()

        # Obtén todos los meses con datos
        meses = set()

        # Meses en actuals
        if not actuals_df.empty:
            actuals_subset = actuals_df[
                (actuals_df['cliente'].astype(str).str.upper().str.strip() == cliente_norm) &
                (actuals_df['proyecto'].astype(str).str.upper().str.strip() == proyecto_norm)
            ]
            if not actuals_subset.empty:
                meses.update(actuals_subset['periodo'].unique())
        else:
            actuals_subset = pd.DataFrame()

        # Meses en billing
        if not billing_df.empty:
            billing_subset = billing_df[
                (billing_df['cliente_origen'].astype(str).str.upper().str.strip() == cliente_norm) &
                (billing_df['proyecto'].astype(str).str.upper().str.strip() == proyecto_norm)
            ]
            if not billing_subset.empty:
                meses.update(billing_subset['mes'].unique())
        else:
            billing_subset = pd.DataFrame()

        # Meses en horas (extraer mes de fecha)
        if not horas_df.empty:
            horas_subset = horas_df[
                (horas_df['cliente'].astype(str).str.upper().str.strip() == cliente_norm) &
                (horas_df['proyecto'].astype(str).str.upper().str.strip() == proyecto_norm)
            ]
        else:
            horas_subset = pd.DataFrame()
        if not horas_subset.empty:
            horas_subset = horas_subset.copy()
            horas_subset['mes'] = pd.to_datetime(horas_subset['fecha']).dt.strftime('%Y%m')
            meses.update(horas_subset['mes'].unique())

        # Procesa cada mes
        for mes in sorted(meses):
            ingreso = 0.0
            coste = 0.0

            # Determina si el mes está cerrado
            es_cerrado = mes < current_month

            if es_cerrado:
                # Usa actuals
                if not actuals_subset.empty:
                    actuals_mes = actuals_subset[actuals_subset['periodo'] == mes]
                    ingreso = actuals_mes[actuals_mes['concepto'] == 'Revenue']['importe'].sum()
                    coste = actuals_mes[actuals_mes['concepto'] == 'Costs']['importe'].sum()
                else:
                    ingreso = 0.0
                    coste = 0.0
            else:
                # Usa billing + horas
                if not billing_subset.empty:
                    billing_mes = billing_subset[billing_subset['mes'] == mes]
                    ingreso = billing_mes['importe_eur'].sum()
                else:
                    ingreso = 0.0

                if not horas_subset.empty:
                    horas_mes = horas_subset[horas_subset['mes'] == mes]
                    coste = horas_mes['costo'].sum()
                else:
                    coste = 0.0

            # Calcula margen
            margen_eur = calculate_margin_eur(ingreso, coste)
            margen_pct = calculate_margin_pct(ingreso, coste)

            # Obtén presupuesto
            ingreso_presup = float(presup_row.get('ingreso_presupuestado', 0) or 0)
            coste_presup = float(presup_row.get('coste_presupuestado', 0) or 0)
            margen_pct_presup = calculate_margin_pct(ingreso_presup, coste_presup)

            # Calcula semáforo
            desviacion = abs(margen_pct - margen_pct_presup)
            semaforo = calculate_traffic_light(margen_pct, margen_pct_presup)

            results.append({
                'cliente_origen': cliente,
                'proyecto': proyecto,
                'mes': mes,
                'es_cerrado': es_cerrado,
                'ingreso': ingreso,
                'coste': coste,
                'margen_eur': margen_eur,
                'margen_pct': margen_pct,
                'ingreso_presupuestado': ingreso_presup,
                'coste_presupuestado': coste_presup,
                'margen_pct_presupuestado': margen_pct_presup,
                'desviacion_pct': desviacion,
                'semaforo': semaforo.value,
            })

    if not results:
        return pd.DataFrame()

    return pd.DataFrame(results)


def aggregate_by_proyecto(
    metrics_mes_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Agrega métricas por proyecto (suma todos los meses).

    Args:
        metrics_mes_df: DataFrame de métricas por mes (salida de aggregate_by_proyecto_mes)

    Returns:
        DataFrame agregado con columnas:
        - cliente_origen, proyecto
        - ingreso, coste, margen_eur, margen_pct
        - ingreso_presupuestado, coste_presupuestado, margen_pct_presupuestado
        - desviacion_pct, semaforo
    """
    if metrics_mes_df.empty:
        return pd.DataFrame()

    # Agrupa por cliente + proyecto
    grouped = metrics_mes_df.groupby(['cliente_origen', 'proyecto']).agg({
        'ingreso': 'sum',
        'coste': 'sum',
        'ingreso_presupuestado': 'first',  # Es igual para todos los meses del proyecto
        'coste_presupuestado': 'first',
    }).reset_index()

    # Recalcula margen
    grouped['margen_eur'] = grouped.apply(
        lambda row: calculate_margin_eur(row['ingreso'], row['coste']),
        axis=1
    )
    grouped['margen_pct'] = grouped.apply(
        lambda row: calculate_margin_pct(row['ingreso'], row['coste']),
        axis=1
    )

    # Margen presupuestado
    grouped['margen_pct_presupuestado'] = grouped.apply(
        lambda row: calculate_margin_pct(row['ingreso_presupuestado'], row['coste_presupuestado']),
        axis=1
    )

    # Desviación y semáforo
    grouped['desviacion_pct'] = grouped.apply(
        lambda row: abs(row['margen_pct'] - row['margen_pct_presupuestado']),
        axis=1
    )
    grouped['semaforo'] = grouped.apply(
        lambda row: calculate_traffic_light(row['margen_pct'], row['margen_pct_presupuestado']).value,
        axis=1
    )

    return grouped[
        ['cliente_origen', 'proyecto', 'ingreso', 'coste', 'margen_eur', 'margen_pct',
         'ingreso_presupuestado', 'coste_presupuestado', 'margen_pct_presupuestado',
         'desviacion_pct', 'semaforo']
    ]
