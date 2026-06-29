"""Loader para el report de Horas (Power BI)."""

import pandas as pd


def load_horas(filepath: str) -> pd.DataFrame:
    """
    Carga el report de horas del mes en curso.

    Columnas originales: Portfolio Name, Client, Project, e-Mail, Date,
    Task Name, Hours, Costo, Vertical, Cluster.

    Args:
        filepath: ruta al archivo de horas (Excel o CSV)

    Returns:
        DataFrame con columnas canónicas:
        - fecha (datetime)
        - cliente (str)
        - proyecto (str)
        - vertical (str): departamento
        - cluster (str): unidad de negocio
        - horas (float)
        - costo (float): en EUR
        - persona_email (str)
    """
    # Lee el archivo
    if filepath.endswith('.csv'):
        df = pd.read_csv(filepath)
    else:  # Excel
        df = pd.read_excel(filepath)

    # Mapeo de columnas originales a canónicas
    column_mapping = {
        'Portfolio Name': 'portfolio',
        'Client': 'cliente',
        'Project': 'proyecto',
        'e-Mail': 'persona_email',
        'Date': 'fecha',
        'Task Name': 'tarea',
        'Hours': 'horas',
        'Costo': 'costo',
        'Vertical': 'vertical',
        'Cluster': 'cluster',
    }

    # Renombra columnas que existan
    rename_dict = {k: v for k, v in column_mapping.items() if k in df.columns}
    df = df.rename(columns=rename_dict)

    # Selecciona solo las columnas que nos importan
    required_cols = ['cliente', 'proyecto', 'horas', 'costo']
    optional_cols = ['fecha', 'vertical', 'cluster', 'persona_email', 'tarea', 'portfolio']

    cols_to_keep = required_cols + [c for c in optional_cols if c in df.columns]
    df = df[cols_to_keep].copy()

    # Normaliza texto
    df['cliente'] = df['cliente'].str.strip().str.upper()
    df['proyecto'] = df['proyecto'].str.strip().str.upper()
    if 'vertical' in df.columns:
        df['vertical'] = df['vertical'].str.strip()
    if 'cluster' in df.columns:
        df['cluster'] = df['cluster'].str.strip()

    # Asegura tipos
    df['horas'] = df['horas'].astype(float)
    df['costo'] = df['costo'].astype(float)
    if 'fecha' in df.columns:
        df['fecha'] = pd.to_datetime(df['fecha'])

    # Reordena columnas
    final_cols = ['fecha', 'cliente', 'proyecto', 'vertical', 'cluster', 'horas', 'costo', 'persona_email']
    return df[[c for c in final_cols if c in df.columns]]
