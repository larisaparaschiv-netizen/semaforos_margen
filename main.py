#!/usr/bin/env python3
"""
Herramienta de margen de proyectos — pipeline principal.

Orquesta: carga → validación → métricas → salida
"""

import sys
import os
import argparse
import pandas as pd
from pathlib import Path

# Añade src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from config.settings import CURRENT_MONTH
from src.loaders.actuals import load_actuals
from src.loaders.horas import load_horas
from src.loaders.billing import load_billing
from src.loaders.presupuesto import load_presupuesto
from src.validate import validate_across_sources
from src.metrics import aggregate_by_proyecto_mes, aggregate_by_proyecto


def main(
    actuals_file: str = None,
    horas_file: str = None,
    billing_file: str = None,
    presupuesto_file: str = None,
    current_month: str = CURRENT_MONTH,
    output_dir: str = None,
    verbose: bool = False,
):
    """
    Ejecuta el pipeline completo de margen de proyectos.

    Args:
        actuals_file: ruta al archivo de actuals
        horas_file: ruta al archivo de horas
        billing_file: ruta al archivo de billing
        presupuesto_file: ruta al archivo de presupuesto
        current_month: mes actual en formato YYYYMM
        output_dir: directorio de salida (default: ./output)
        verbose: mostrar logs detallados
    """
    if output_dir is None:
        output_dir = os.path.join(os.path.dirname(__file__), 'output')

    Path(output_dir).mkdir(exist_ok=True)

    if verbose:
        print(f"🚀 Iniciando pipeline de margen de proyectos")
        print(f"   Mes actual: {current_month}")
        print(f"   Directorio de salida: {output_dir}")
        print()

    # ============================================================================
    # PASO 1: CARGA
    # ============================================================================
    if verbose:
        print("📂 Paso 1: Cargando datos...")

    try:
        if actuals_file and os.path.exists(actuals_file):
            actuals_df = load_actuals(actuals_file)
            if verbose:
                print(f"   ✓ Actuals: {actuals_df.shape[0]} filas")
        else:
            actuals_df = pd.DataFrame()
            if verbose:
                print(f"   ⚠ Actuals: no especificado")

        if horas_file and os.path.exists(horas_file):
            horas_df = load_horas(horas_file)
            if verbose:
                print(f"   ✓ Horas: {horas_df.shape[0]} filas")
        else:
            horas_df = pd.DataFrame()
            if verbose:
                print(f"   ⚠ Horas: no especificado")

        if billing_file and os.path.exists(billing_file):
            billing_df = load_billing(billing_file)
            if verbose:
                print(f"   ✓ Billing: {billing_df.shape[0]} filas")
        else:
            billing_df = pd.DataFrame()
            if verbose:
                print(f"   ⚠ Billing: no especificado")

        if presupuesto_file and os.path.exists(presupuesto_file):
            presupuesto_df = load_presupuesto(presupuesto_file)
            if verbose:
                print(f"   ✓ Presupuesto: {presupuesto_df.shape[0]} filas")
        else:
            presupuesto_df = pd.DataFrame()
            if verbose:
                print(f"   ⚠ Presupuesto: no especificado")

        if verbose:
            print()

    except Exception as e:
        print(f"❌ Error cargando datos: {e}")
        return False

    # ============================================================================
    # PASO 2: VALIDACIÓN
    # ============================================================================
    if verbose:
        print("✔️  Paso 2: Validando...")

    try:
        report = validate_across_sources(actuals_df, horas_df, billing_df, presupuesto_df)

        if report.has_alerts():
            if verbose:
                print(f"   ⚠️  Alertas detectadas:")
                summary = report.summary()
                for alert_type, count in summary.items():
                    print(f"      - {alert_type}: {count}")
            # Exporta alertas
            alerts_path = os.path.join(output_dir, 'alertas.csv')
            report.to_dataframe().to_csv(alerts_path, index=False)
            if verbose:
                print(f"   Alertas guardadas en: {alerts_path}")
        else:
            if verbose:
                print(f"   ✓ Sin alertas (alineación perfecta)")

        if verbose:
            print()

    except Exception as e:
        print(f"❌ Error validando: {e}")
        return False

    # ============================================================================
    # PASO 3: MÉTRICAS
    # ============================================================================
    if verbose:
        print("📊 Paso 3: Calculando métricas...")

    try:
        # Verifica si hay presupuesto
        if presupuesto_df.empty:
            if verbose:
                print(f"   ⚠️  Sin presupuesto, no se pueden calcular métricas")
                print()
            return True

        # Agregación por proyecto × mes
        metrics_mes = aggregate_by_proyecto_mes(
            actuals_df, horas_df, billing_df, presupuesto_df, current_month
        )

        if metrics_mes.shape[0] > 0:
            if verbose:
                print(f"   ✓ Métricas por mes: {metrics_mes.shape[0]} filas")

            # Exporta métricas por mes
            metrics_mes_path = os.path.join(output_dir, 'metricas_mes.csv')
            metrics_mes.to_csv(metrics_mes_path, index=False)
            if verbose:
                print(f"   Guardado en: {metrics_mes_path}")

            # Agregación por proyecto
            metrics_proyecto = aggregate_by_proyecto(metrics_mes)

            if verbose:
                print(f"   ✓ Métricas por proyecto: {metrics_proyecto.shape[0]} filas")

            # Filtro: solo proyectos con TO_LAUNCH=TRUE (ya está hecho en aggregate_by_proyecto_mes)
            # Exporta tabla principal por proyecto
            output_path = os.path.join(output_dir, 'proyectos_margen.csv')
            metrics_proyecto.to_csv(output_path, index=False)
            if verbose:
                print(f"   Guardado en: {output_path}")
                print()
        else:
            if verbose:
                print(f"   ⚠️  No hay datos para procesar")
                print()

    except Exception as e:
        print(f"❌ Error calculando métricas: {e}")
        return False

    # ============================================================================
    # RESUMEN FINAL
    # ============================================================================
    if verbose:
        print("=" * 70)
        print("✅ Pipeline completado exitosamente")
        print(f"   Archivos generados en: {output_dir}")
        print("=" * 70)

    return True


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Herramienta de margen de proyectos'
    )
    parser.add_argument(
        '--actuals',
        help='Ruta al archivo de actuals (Excel/CSV)',
    )
    parser.add_argument(
        '--horas',
        help='Ruta al archivo de horas (Excel/CSV)',
    )
    parser.add_argument(
        '--billing',
        help='Ruta al archivo de billing (Excel/CSV)',
    )
    parser.add_argument(
        '--presupuesto',
        help='Ruta al archivo de presupuesto (Excel)',
    )
    parser.add_argument(
        '--mes',
        default=CURRENT_MONTH,
        help=f'Mes actual en formato YYYYMM (default: {CURRENT_MONTH})',
    )
    parser.add_argument(
        '--output',
        help='Directorio de salida (default: ./output)',
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Mostrar logs detallados',
    )

    args = parser.parse_args()

    success = main(
        actuals_file=args.actuals,
        horas_file=args.horas,
        billing_file=args.billing,
        presupuesto_file=args.presupuesto,
        current_month=args.mes,
        output_dir=args.output,
        verbose=args.verbose,
    )

    sys.exit(0 if success else 1)
