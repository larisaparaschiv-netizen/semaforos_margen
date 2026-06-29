"""Loader para el archivo de Billing (ingresos esperados)."""

import pandas as pd


def load_billing(filepath: str) -> pd.DataFrame:
    """
    Carga el archivo de billing (ingresos esperados/futuros).

    Columnas originales: Billing MONTH, Type of Billing, Proyect, PO,
    Final Billing LC, Currency, Actual FX Rate, Final Billing USD,
    Sociedad, Billing number, Actual Status, Client, Cliente Origen.

    Args:
        filepath: ruta al archivo de billing (Excel o CSV)

    Returns:
        DataFrame con columnas canónicas:
        - mes (str, YYYYMM)
        - cliente_origen (str)
        - proyecto (str)
        - tipo_billing (str)
        - estado_billing (str)
        - importe_eur (float): Final Billing LC en EUR
        - moneda (str)
        - tasa_fx (float)
    """
    # Lee el archivo
    if filepath.endswith('.csv'):
        df = pd.read_csv(filepath)
    else:  # Excel
        df = pd.read_excel(filepath)

    # Mapeo de columnas originales a canónicas
    column_mapping = {
        'Billing MONTH': 'fecha_billing',
        'Type of Billing': 'tipo_billing',
        'Proyect': 'proyecto',
        'Project': 'proyecto',  # alias
        'Final Billing LC': 'importe_eur',
        'Currency': 'moneda',
        'Actual FX Rate': 'tasa_fx',
        'Actual Status': 'estado_billing',
        'Cliente Origen': 'cliente_origen',
        'Client': 'cliente',  # respaldo
    }

    # Renombra columnas que existan
    rename_dict = {k: v for k, v in column_mapping.items() if k in df.columns}
    df = df.rename(columns=rename_dict)

    # Selecciona solo las columnas que nos importan
    required_cols = ['fecha_billing', 'cliente_origen', 'proyecto', 'importe_eur']
    optional_cols = ['tipo_billing', 'estado_billing', 'moneda', 'tasa_fx']

    cols_to_keep = required_cols + [c for c in optional_cols if c in df.columns]
    df = df[cols_to_keep].copy()

    # Convierte fecha a YYYYMM
    df['fecha_billing'] = pd.to_datetime(df['fecha_billing'])
    df['mes'] = df['fecha_billing'].dt.strftime('%Y%m')
    df = df.drop(columns=['fecha_billing'])

    # Normaliza texto
    df['cliente_origen'] = df['cliente_origen'].str.strip().str.upper()
    df['proyecto'] = df['proyecto'].str.strip().str.upper()
    if 'tipo_billing' in df.columns:
        df['tipo_billing'] = df['tipo_billing'].str.strip()
    if 'estado_billing' in df.columns:
        df['estado_billing'] = df['estado_billing'].str.strip()

    # Asegura tipos
    df['importe_eur'] = df['importe_eur'].astype(float)
    if 'tasa_fx' in df.columns:
        df['tasa_fx'] = df['tasa_fx'].astype(float)

    # Reordena columnas
    final_cols = ['mes', 'cliente_origen', 'proyecto', 'tipo_billing', 'estado_billing', 'importe_eur', 'moneda', 'tasa_fx']
    return df[[c for c in final_cols if c in df.columns]]
