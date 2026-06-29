"""Loader para el archivo de Actuals (export SAP)."""

import pandas as pd
from pathlib import Path


def load_actuals(filepath: str) -> pd.DataFrame:
    """
    Carga el archivo de actuals y renombra columnas a esquema canónico.

    Mapea las columnas originales a un esquema estándar que usa el resto del pipeline.
    Los ingresos (Revenue Labor) llegan en negativo y se invierten aquí.

    Args:
        filepath: ruta al archivo de actuals (Excel o CSV)

    Returns:
        DataFrame con columnas canónicas:
        - periodo (str, YYYYMM)
        - cliente (str)
        - proyecto (str)
        - concepto (str): "Revenue" o "Costs"
        - cc (str): subcategoría (Salaries & Wages, Office Expenses, etc.)
        - importe (float): en EUR, positivo
        - persona (str): Glober
        - tipo_contrato (str): FEE, TYM, SLA, FIXED_PRICE, etc.
    """
    # Lee el archivo
    if filepath.endswith('.csv'):
        df = pd.read_csv(filepath)
    else:  # Excel
        df = pd.read_excel(filepath)

    # Mapeo de columnas originales a canónicas
    column_mapping = {
        'PeriodoYYYYMM': 'periodo',
        'Concepto': 'concepto_original',
        'CC': 'cc',
        'EnMLCeBe': 'importe_original',
        'Client': 'cliente',
        'Project': 'proyecto',
        'Glober': 'persona',
        'ContractType': 'tipo_contrato',
    }

    # Renombra columnas que existan
    rename_dict = {k: v for k, v in column_mapping.items() if k in df.columns}
    df = df.rename(columns=rename_dict)

    # Selecciona solo las columnas que nos importan
    required_cols = ['periodo', 'concepto_original', 'cliente', 'proyecto', 'importe_original']
    optional_cols = ['cc', 'persona', 'tipo_contrato']

    cols_to_keep = required_cols + [c for c in optional_cols if c in df.columns]
    df = df[cols_to_keep].copy()

    # Normaliza el concepto y ajusta el signo del importe
    df['concepto'] = df['concepto_original'].str.strip().str.lower()
    df['concepto'] = df['concepto'].apply(lambda x: _normalize_concepto(x))

    # Invierte el signo del ingreso (Revenue Labor llega en negativo)
    df['importe'] = df.apply(
        lambda row: -row['importe_original'] if row['concepto'] == 'Revenue' else row['importe_original'],
        axis=1
    )

    # Limpia el dataframe
    df = df.drop(columns=['concepto_original', 'importe_original'])

    # Rellena valores faltantes en columnas opcionales
    if 'cc' not in df.columns:
        df['cc'] = None
    if 'persona' not in df.columns:
        df['persona'] = None
    if 'tipo_contrato' not in df.columns:
        df['tipo_contrato'] = None

    # Normaliza texto: espacios y mayúsculas
    df['cliente'] = df['cliente'].str.strip().str.upper()
    df['proyecto'] = df['proyecto'].str.strip().str.upper()
    df['cc'] = df['cc'].str.strip().str.upper() if df['cc'].dtype == 'object' else df['cc']

    # Asegura tipos
    df['periodo'] = df['periodo'].astype(str)
    df['importe'] = df['importe'].astype(float)

    return df[['periodo', 'cliente', 'proyecto', 'concepto', 'cc', 'importe', 'persona', 'tipo_contrato']]


def _normalize_concepto(concepto: str) -> str:
    """Normaliza el concepto a 'Revenue' o 'Costs'."""
    if 'revenue' in concepto.lower() or 'ingreso' in concepto.lower():
        return 'Revenue'
    elif 'costs' in concepto.lower() or 'coste' in concepto.lower():
        return 'Costs'
    return concepto
