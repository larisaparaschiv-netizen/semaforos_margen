"""Loader para el archivo de Presupuesto (manual)."""

import pandas as pd


def load_presupuesto(filepath: str) -> pd.DataFrame:
    """
    Carga la plantilla de presupuesto (manual).

    La plantilla tiene estructura: encabezados, instrucciones, y datos a partir de fila 3.
    Mapea las columnas al esquema canónico.

    Columnas originales: Cliente Origen, Project, Año, Tipo de contrato,
    Ingreso presup. (€), Coste presup. (€), Margen presup. (%), etc.

    Args:
        filepath: ruta al archivo de presupuesto (Excel)

    Returns:
        DataFrame con columnas canónicas:
        - cliente_origen (str)
        - proyecto (str)
        - año (int)
        - tipo_contrato (str)
        - ingreso_presupuestado (float): en EUR
        - coste_presupuestado (float): en EUR
        - margen_pct_presupuestado (float): porcentaje
        - to_launch (bool)
        - responsable (str)
        - estado (str)
        - fecha_actualizacion (datetime)
    """
    # Lee la hoja Presupuesto, saltando las filas de instrucciones (0-3)
    df = pd.read_excel(filepath, sheet_name="Presupuesto", header=3)

    # Las columnas están en fila 2 (índice 2) con valores como 'Cliente Origen', 'Project', etc.
    # Renombra las columnas para trabajar con ellas
    column_mapping = {
        'Presupuesto por proyecto': 'cliente_origen',  # Primera columna
        'Cliente Origen': 'cliente_origen',
        'Project': 'proyecto',
        'Año': 'año',
        'Tipo de contrato': 'tipo_contrato',
        'Ingreso presup. (€)': 'ingreso_presupuestado',
        'Coste presup. (€)': 'coste_presupuestado',
        'Margen presup. (%)': 'margen_pct_presupuestado',
        'Margen € (calc.)': 'margen_eur_calculado',
        'Margen % (calc.)': 'margen_pct_calculado',
        'Responsable': 'responsable',
        'Fecha inicio': 'fecha_inicio',
        'Fecha fin prev.': 'fecha_fin',
        'Estado': 'estado',
        'Fecha actualización': 'fecha_actualizacion',
        'TO Launch ': 'to_launch',  # Nota el espacio en la original
        'TO Launch': 'to_launch',
        'Notas': 'notas',
    }

    # Limpia los nombres de columnas existentes
    df.columns = df.columns.str.strip()

    # Renombra las columnas que existan
    rename_dict = {k: v for k, v in column_mapping.items() if k in df.columns}
    df = df.rename(columns=rename_dict)

    # Selecciona columnas de interés
    required_cols = ['cliente_origen', 'proyecto', 'año']
    optional_cols = ['tipo_contrato', 'ingreso_presupuestado', 'coste_presupuestado',
                    'margen_pct_presupuestado', 'margen_eur_calculado', 'margen_pct_calculado',
                    'responsable', 'fecha_inicio', 'fecha_fin', 'estado', 'fecha_actualizacion',
                    'to_launch', 'notas']

    cols_to_keep = required_cols + [c for c in optional_cols if c in df.columns]
    df = df[cols_to_keep].copy()

    # Elimina filas vacías
    df = df.dropna(subset=['cliente_origen', 'proyecto'], how='all')

    # Normaliza texto
    df['cliente_origen'] = df['cliente_origen'].fillna('').str.strip().str.upper()
    df['proyecto'] = df['proyecto'].fillna('').str.strip().str.upper()
    if 'tipo_contrato' in df.columns:
        df['tipo_contrato'] = df['tipo_contrato'].fillna('').str.strip()
    if 'estado' in df.columns:
        df['estado'] = df['estado'].fillna('').str.strip()

    # Convierte tipos
    if 'año' in df.columns:
        df['año'] = pd.to_numeric(df['año'], errors='coerce').astype('Int64')

    if 'ingreso_presupuestado' in df.columns:
        df['ingreso_presupuestado'] = pd.to_numeric(df['ingreso_presupuestado'], errors='coerce').astype(float)

    if 'coste_presupuestado' in df.columns:
        df['coste_presupuestado'] = pd.to_numeric(df['coste_presupuestado'], errors='coerce').astype(float)

    if 'margen_pct_presupuestado' in df.columns:
        df['margen_pct_presupuestado'] = pd.to_numeric(df['margen_pct_presupuestado'], errors='coerce').astype(float)

    if 'margen_eur_calculado' in df.columns:
        df['margen_eur_calculado'] = pd.to_numeric(df['margen_eur_calculado'], errors='coerce').astype(float)

    if 'margen_pct_calculado' in df.columns:
        df['margen_pct_calculado'] = pd.to_numeric(df['margen_pct_calculado'], errors='coerce').astype(float)

    # Convierte TO_LAUNCH a booleano
    if 'to_launch' in df.columns:
        df['to_launch'] = df['to_launch'].astype(bool)

    # Convierte fechas
    for date_col in ['fecha_inicio', 'fecha_fin', 'fecha_actualizacion']:
        if date_col in df.columns:
            df[date_col] = pd.to_datetime(df[date_col], errors='coerce')

    # Filtra solo filas con cliente_origen y proyecto no vacíos
    df = df[(df['cliente_origen'] != '') & (df['proyecto'] != '')]

    return df
