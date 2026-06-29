#!/usr/bin/env python3
"""
Demo interactivo: genera datos de prueba y ejecuta el pipeline.
"""

import sys
import os
import tempfile
import pandas as pd
import openpyxl
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))

from main import main


def create_demo_data(temp_dir):
    """Crea archivos de prueba realistas."""

    print("\n📊 Generando datos de prueba...")

    # Actuals (mes cerrado 202604)
    actuals = pd.DataFrame({
        'PeriodoYYYYMM': ['202604', '202604', '202604', '202604', '202604', '202604'],
        'Concepto': ['Revenue Labor', 'Costs', 'Costs', 'Revenue Labor', 'Costs', 'Costs'],
        'CC': ['', 'Salaries & Wages', 'Office Expenses', '', 'Salaries & Wages', 'Professional Service'],
        'EnMLCeBe': [-120000.0, 80000.0, 15000.0, -95000.0, 70000.0, 12000.0],
        'Client': ['GRUPO ESTRELLA GALICIA', 'GRUPO ESTRELLA GALICIA', 'GRUPO ESTRELLA GALICIA',
                   'GRUPO ESTRELLA GALICIA', 'GRUPO ESTRELLA GALICIA', 'GRUPO ESTRELLA GALICIA'],
        'Project': ['DAM WORKFRONT HDR', 'DAM WORKFRONT HDR', 'DAM WORKFRONT HDR',
                    'FEES ACTIVOS DIG. 2', 'FEES ACTIVOS DIG. 2', 'FEES ACTIVOS DIG. 2'],
        'Glober': ['P1', 'P1', 'P2', 'P3', 'P3', 'P4'],
        'ContractType': ['FEE', 'FEE', 'FEE', 'FEE', 'FEE', 'FEE'],
    })

    # Horas (mes actual 202606)
    horas = pd.DataFrame({
        'Portfolio Name': ['Portfolio 1', 'Portfolio 2'],
        'Client': ['GRUPO ESTRELLA GALICIA', 'GRUPO ESTRELLA GALICIA'],
        'Project': ['DAM WORKFRONT HDR', 'FEES ACTIVOS DIG. 2'],
        'e-Mail': ['person1@globant.com', 'person2@globant.com'],
        'Date': pd.to_datetime(['2026-06-15', '2026-06-20']),
        'Task Name': ['Development', 'Integration'],
        'Hours': [40.0, 32.0],
        'Costo': [8000.0, 6400.0],
        'Vertical': ['Desarrollo', 'QA'],
        'Cluster': ['CODEBAY', 'CODEBAY'],
    })

    # Billing (mes actual 202606)
    billing = pd.DataFrame({
        'Billing MONTH': pd.to_datetime(['2026-06-15', '2026-06-20']),
        'Type of Billing': ['Provision', 'Provision'],
        'Proyect': ['DAM WORKFRONT HDR', 'FEES ACTIVOS DIG. 2'],
        'PO': [None, None],
        'Final Billing LC': [45000.0, 35000.0],
        'Currency': ['EUR', 'EUR'],
        'Actual FX Rate': [1.0, 1.0],
        'Final Billing USD': [45000.0, 35000.0],
        'Sociedad': ['GRUPO ESTRELLA', 'GRUPO ESTRELLA'],
        'Billing number': [12345, 12346],
        'Actual Status': ['Approved', 'Approved'],
        'Client': ['GRUPO ESTRELLA', 'GRUPO ESTRELLA'],
        'Cliente Origen': ['GRUPO ESTRELLA GALICIA', 'GRUPO ESTRELLA GALICIA'],
    })

    # Presupuesto
    wb = openpyxl.Workbook()
    ws_instr = wb.active
    ws_instr.title = 'Instrucciones'
    ws_presup = wb.create_sheet('Presupuesto')
    ws_presup.append(['Presupuesto por proyecto'])
    ws_presup.append([])
    ws_presup.append([])
    ws_presup.append(['Cliente Origen', 'Project', 'Año', 'Ingreso presup. (€)', 'Coste presup. (€)', 'Estado', 'TO Launch', 'Margen presup. (%)'])
    ws_presup.append(['GRUPO ESTRELLA GALICIA', 'DAM WORKFRONT HDR', 2026, 256307.0, 150000.0, 'Activo', True, 41.5])
    ws_presup.append(['GRUPO ESTRELLA GALICIA', 'FEES ACTIVOS DIG. 2', 2026, 200000.0, 120000.0, 'Activo', True, 40.0])

    # Guarda los archivos
    actuals_file = os.path.join(temp_dir, 'actuals.csv')
    horas_file = os.path.join(temp_dir, 'horas.csv')
    billing_file = os.path.join(temp_dir, 'billing.csv')
    presupuesto_file = os.path.join(temp_dir, 'presupuesto.xlsx')

    actuals.to_csv(actuals_file, index=False)
    horas.to_csv(horas_file, index=False)
    billing.to_csv(billing_file, index=False)
    wb.save(presupuesto_file)

    print(f"   ✓ Actuals: {len(actuals)} filas")
    print(f"   ✓ Horas: {len(horas)} filas")
    print(f"   ✓ Billing: {len(billing)} filas")
    print(f"   ✓ Presupuesto: {2} proyectos")

    return actuals_file, horas_file, billing_file, presupuesto_file


def show_results(output_dir):
    """Muestra los resultados generados."""

    print("\n📊 RESULTADOS GENERADOS")
    print("=" * 80)

    # Tabla principal
    proyectos_file = os.path.join(output_dir, 'proyectos_margen.csv')
    if os.path.exists(proyectos_file):
        print("\n📈 proyectos_margen.csv (Tabla por proyecto):")
        print("-" * 80)
        df = pd.read_csv(proyectos_file)
        # Formatea para lectura
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
        pd.set_option('display.max_colwidth', 25)
        print(df.to_string(index=False))

    # Métricas por mes
    metricas_file = os.path.join(output_dir, 'metricas_mes.csv')
    if os.path.exists(metricas_file):
        print("\n📅 metricas_mes.csv (Drill-down mensual):")
        print("-" * 80)
        df = pd.read_csv(metricas_file)
        cols_to_show = ['cliente_origen', 'proyecto', 'mes', 'es_cerrado', 'ingreso', 'coste', 'margen_eur', 'margen_pct', 'semaforo']
        print(df[cols_to_show].to_string(index=False))

    # Alertas
    alertas_file = os.path.join(output_dir, 'alertas.csv')
    if os.path.exists(alertas_file):
        print("\n⚠️  alertas.csv (Validación):")
        print("-" * 80)
        df = pd.read_csv(alertas_file)
        print(f"Total alertas: {len(df)}")
        print("\nResumen por tipo:")
        print(df['alert_type'].value_counts())


def main_demo():
    """Ejecuta el demo completo."""

    print("\n" + "=" * 80)
    print("🎯 DEMO: Herramienta de Margen de Proyectos")
    print("=" * 80)

    with tempfile.TemporaryDirectory() as temp_dir:
        # Crea datos de prueba
        actuals_file, horas_file, billing_file, presupuesto_file = create_demo_data(temp_dir)

        # Ejecuta el pipeline
        print("\n🚀 Ejecutando pipeline...")
        success = main(
            actuals_file=actuals_file,
            horas_file=horas_file,
            billing_file=billing_file,
            presupuesto_file=presupuesto_file,
            current_month='202606',
            output_dir='./output',
            verbose=True,
        )

        if success:
            # Muestra resultados
            show_results('./output')

            print("\n" + "=" * 80)
            print("✅ DEMO COMPLETADO")
            print("=" * 80)
            print("\n📂 Archivos guardados en: ./output/")
            print("   • proyectos_margen.csv")
            print("   • metricas_mes.csv")
            print("   • alertas.csv")
            print("\n💡 Puedes revisar los archivos CSV con cualquier editor o Excel")
        else:
            print("\n❌ Error ejecutando pipeline")
            return False

    return True


if __name__ == '__main__':
    success = main_demo()
    sys.exit(0 if success else 1)
