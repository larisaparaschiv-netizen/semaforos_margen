"""Validación de claves y detección de no casados."""

import pandas as pd
from typing import Tuple, Set, Dict, List


def normalize_key(cliente: str, proyecto: str) -> Tuple[str, str]:
    """
    Normaliza la clave Cliente + Proyecto.

    Convierte a mayúsculas, elimina espacios en blanco redundantes.

    Args:
        cliente: nombre del cliente
        proyecto: nombre del proyecto

    Returns:
        Tupla (cliente_normalizado, proyecto_normalizado)
    """
    cliente = str(cliente).strip().upper()
    proyecto = str(proyecto).strip().upper()
    return (cliente, proyecto)


def extract_keys(df: pd.DataFrame, cliente_col: str, proyecto_col: str) -> Set[Tuple[str, str]]:
    """
    Extrae las claves únicas Cliente + Proyecto de un DataFrame.

    Args:
        df: DataFrame con datos
        cliente_col: nombre de la columna de cliente
        proyecto_col: nombre de la columna de proyecto

    Returns:
        Set de tuplas (cliente_normalizado, proyecto_normalizado)
    """
    keys = set()
    for _, row in df.iterrows():
        # Valida que no sean None/NaN/null
        cliente = row[cliente_col]
        proyecto = row[proyecto_col]

        # Salta si es None o NaN
        if pd.isna(cliente) or pd.isna(proyecto):
            continue

        cliente_str = str(cliente).strip()
        proyecto_str = str(proyecto).strip()

        # Salta si la conversión resultó en 'None' (por si acaso)
        if cliente_str.lower() == 'none' or proyecto_str.lower() == 'none':
            continue

        if cliente_str and proyecto_str:
            key = normalize_key(cliente_str, proyecto_str)
            keys.add(key)
    return keys


def find_unmapped(
    primary_df: pd.DataFrame,
    primary_cliente_col: str,
    primary_proyecto_col: str,
    reference_df: pd.DataFrame,
    reference_cliente_col: str,
    reference_proyecto_col: str,
    source_name: str,
    reference_name: str,
) -> pd.DataFrame:
    """
    Encuentra las claves que aparecen en primary pero no en reference (no casadas).

    Args:
        primary_df: DataFrame primario
        primary_cliente_col: columna de cliente en primary
        primary_proyecto_col: columna de proyecto en primary
        reference_df: DataFrame de referencia
        reference_cliente_col: columna de cliente en reference
        reference_proyecto_col: columna de proyecto en reference
        source_name: nombre de la fuente primaria (para el reporte)
        reference_name: nombre de la fuente de referencia

    Returns:
        DataFrame con las filas no casadas de primary_df, más columnas de diagnóstico
    """
    # Extrae claves
    primary_keys = extract_keys(primary_df, primary_cliente_col, primary_proyecto_col)
    reference_keys = extract_keys(reference_df, reference_cliente_col, reference_proyecto_col)

    # Encuentra las no casadas
    unmapped_keys = primary_keys - reference_keys

    if not unmapped_keys:
        return pd.DataFrame()

    # Filtra las filas de primary que tienen claves no casadas
    unmapped_rows = []
    for _, row in primary_df.iterrows():
        cliente = str(row[primary_cliente_col]).strip()
        proyecto = str(row[primary_proyecto_col]).strip()
        if cliente and cliente.lower() != 'nan' and proyecto and proyecto.lower() != 'nan':
            key = normalize_key(cliente, proyecto)
            if key in unmapped_keys:
                unmapped_rows.append(row)

    if not unmapped_rows:
        return pd.DataFrame()

    result = pd.DataFrame(unmapped_rows)
    result['_alert_type'] = f'NOT_MAPPED_IN_{reference_name.upper()}'
    result['_source'] = source_name
    result['_missing_in'] = reference_name

    return result


class ValidationReport:
    """Reporte de validación con todas las alertas de no casados."""

    def __init__(self):
        self.alerts: List[Dict] = []

    def add_alert(
        self,
        alert_type: str,
        cliente: str,
        proyecto: str,
        source: str,
        details: str = "",
    ):
        """Añade una alerta al reporte."""
        self.alerts.append({
            'alert_type': alert_type,
            'cliente': cliente,
            'proyecto': proyecto,
            'source': source,
            'details': details,
        })

    def to_dataframe(self) -> pd.DataFrame:
        """Convierte el reporte a DataFrame."""
        if not self.alerts:
            return pd.DataFrame()
        return pd.DataFrame(self.alerts)

    def has_alerts(self) -> bool:
        """Retorna True si hay alertas."""
        return len(self.alerts) > 0

    def summary(self) -> Dict[str, int]:
        """Retorna un resumen por tipo de alerta."""
        summary = {}
        for alert in self.alerts:
            alert_type = alert['alert_type']
            summary[alert_type] = summary.get(alert_type, 0) + 1
        return summary


def validate_across_sources(
    actuals_df: pd.DataFrame,
    horas_df: pd.DataFrame,
    billing_df: pd.DataFrame,
    presupuesto_df: pd.DataFrame,
) -> ValidationReport:
    """
    Valida que todas las fuentes estén alineadas en claves Cliente + Proyecto.

    Genera alertas para:
    - Clientes + proyectos en actuals sin cobertura en presupuesto (no marcados TO_LAUNCH)
    - Clientes + proyectos en billing sin cobertura en presupuesto
    - Clientes + proyectos en horas sin cobertura en presupuesto
    - Inconsistencias en nombres entre fuentes

    Args:
        actuals_df: DataFrame de actuals (columnas: cliente, proyecto, ...)
        horas_df: DataFrame de horas (columnas: cliente, proyecto, ...)
        billing_df: DataFrame de billing (columnas: cliente_origen, proyecto, ...)
        presupuesto_df: DataFrame de presupuesto (columnas: cliente_origen, proyecto, to_launch, ...)

    Returns:
        ValidationReport con todas las alertas
    """
    report = ValidationReport()

    # Extrae claves de presupuesto (solo TO_LAUNCH = TRUE)
    # Asegura que to_launch sea booleano
    if 'to_launch' in presupuesto_df.columns:
        presupuesto_df = presupuesto_df.copy()
        presupuesto_df['to_launch'] = presupuesto_df['to_launch'].fillna(False).astype(bool)
        presupuesto_launch = presupuesto_df[presupuesto_df['to_launch'] == True].copy()
    else:
        presupuesto_launch = presupuesto_df.copy()
    presupuesto_keys = extract_keys(presupuesto_launch, 'cliente_origen', 'proyecto')

    # Valida actuals contra presupuesto
    # Solo alerta si aparece en actuals pero NO aparece en presupuesto en absoluto (ni siquiera con TO_LAUNCH=FALSE)
    all_presupuesto_keys = extract_keys(presupuesto_df, 'cliente_origen', 'proyecto')
    actuals_keys = extract_keys(actuals_df, 'cliente', 'proyecto')
    for key in actuals_keys - all_presupuesto_keys:
        cliente, proyecto = key
        report.add_alert(
            alert_type='ACTUALS_NOT_IN_BUDGET',
            cliente=cliente,
            proyecto=proyecto,
            source='Actuals',
            details='Aparece en actuals pero no en presupuesto'
        )

    # Valida billing contra presupuesto
    billing_keys = extract_keys(billing_df, 'cliente_origen', 'proyecto')
    for key in billing_keys - all_presupuesto_keys:
        cliente, proyecto = key
        report.add_alert(
            alert_type='BILLING_NOT_IN_BUDGET',
            cliente=cliente,
            proyecto=proyecto,
            source='Billing',
            details='Aparece en billing pero no en presupuesto'
        )

    # Valida horas contra presupuesto
    horas_keys = extract_keys(horas_df, 'cliente', 'proyecto')
    for key in horas_keys - all_presupuesto_keys:
        cliente, proyecto = key
        report.add_alert(
            alert_type='HORAS_NOT_IN_BUDGET',
            cliente=cliente,
            proyecto=proyecto,
            source='Horas',
            details='Aparece en horas pero no en presupuesto'
        )

    # Valida que presupuesto tenga datos en horas o actuals (al menos ingresos)
    for _, row in presupuesto_launch.iterrows():
        cliente = row['cliente_origen']
        proyecto = row['proyecto']
        key = normalize_key(cliente, proyecto)

        has_actuals = key in actuals_keys
        has_billing = key in billing_keys
        has_horas = key in horas_keys

        if not (has_actuals or has_billing or has_horas):
            report.add_alert(
                alert_type='BUDGET_NO_DATA',
                cliente=cliente,
                proyecto=proyecto,
                source='Presupuesto',
                details='Presupuesto sin datos en actuals, billing ni horas'
            )

    return report


def get_valid_keys(
    actuals_df: pd.DataFrame,
    horas_df: pd.DataFrame,
    billing_df: pd.DataFrame,
    presupuesto_df: pd.DataFrame,
) -> Set[Tuple[str, str]]:
    """
    Retorna el set de claves Cliente + Proyecto válidas (en presupuesto con TO_LAUNCH=TRUE).

    Esto es el universo de proyectos para el procesamiento.

    Args:
        actuals_df: DataFrame de actuals
        horas_df: DataFrame de horas
        billing_df: DataFrame de billing
        presupuesto_df: DataFrame de presupuesto

    Returns:
        Set de tuplas (cliente, proyecto) normalizadas
    """
    # Asegura que to_launch sea booleano
    presupuesto_copy = presupuesto_df.copy()
    if 'to_launch' in presupuesto_copy.columns:
        presupuesto_copy['to_launch'] = presupuesto_copy['to_launch'].fillna(False).astype(bool)
        presupuesto_launch = presupuesto_copy[presupuesto_copy['to_launch'] == True].copy()
    else:
        presupuesto_launch = presupuesto_copy.copy()
    return extract_keys(presupuesto_launch, 'cliente_origen', 'proyecto')
