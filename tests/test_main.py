"""Tests para el pipeline principal (main.py)."""

import sys
import os
import tempfile
import pandas as pd
import pytest
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from main import main


@pytest.fixture
def temp_output_dir():
    """Crea un directorio temporal para salidas."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def sample_data_files(tmp_path):
    """Crea archivos de datos de ejemplo para testing."""
    import openpyxl

    # Actuals
    actuals = pd.DataFrame({
        'PeriodoYYYYMM': ['202404', '202404'],
        'Concepto': ['Revenue Labor', 'Costs'],
        'CC': ['', 'Salaries & Wages'],
        'EnMLCeBe': [-500000.0, 400000.0],
        'Client': ['CLIENT A', 'CLIENT A'],
        'Project': ['PROJECT X', 'PROJECT X'],
        'Glober': ['P1', 'P1'],
        'ContractType': ['TYM', 'TYM'],
    })

    # Horas
    horas = pd.DataFrame({
        'Portfolio Name': ['Airlines'],
        'Client': ['CLIENT A'],
        'Project': ['PROJECT X'],
        'e-Mail': ['person@company.com'],
        'Date': pd.to_datetime(['2026-06-15']),
        'Task Name': ['Task 1'],
        'Hours': [8.0],
        'Costo': [5000.0],
        'Vertical': ['Desarrollo'],
        'Cluster': ['Tech'],
    })

    # Billing
    billing = pd.DataFrame({
        'Billing MONTH': pd.to_datetime(['2026-06-15']),
        'Type of Billing': ['Provision'],
        'Proyect': ['PROJECT X'],
        'PO': [None],
        'Final Billing LC': [150000.0],
        'Currency': ['EUR'],
        'Actual FX Rate': [1.0],
        'Final Billing USD': [150000.0],
        'Sociedad': ['Company'],
        'Billing number': [12345],
        'Actual Status': ['Approved'],
        'Client': ['CLIENT A'],
        'Cliente Origen': ['CLIENT A'],
    })

    # Escribe archivos
    presupuesto_file = tmp_path / 'presupuesto.xlsx'
    actuals_file = tmp_path / 'actuals.csv'
    horas_file = tmp_path / 'horas.csv'
    billing_file = tmp_path / 'billing.csv'

    # Crea presupuesto con estructura correcta
    wb = openpyxl.Workbook()
    ws_instr = wb.active
    ws_instr.title = 'Instrucciones'
    ws_presup = wb.create_sheet('Presupuesto')
    ws_presup.append(['Presupuesto por proyecto'])
    ws_presup.append([])
    ws_presup.append([])
    ws_presup.append(['Cliente Origen', 'Project', 'Año', 'Ingreso presup. (€)', 'Coste presup. (€)', 'Estado', 'TO Launch'])
    ws_presup.append(['CLIENT A', 'PROJECT X', 2026, 500000.0, 400000.0, 'Activo', True])
    wb.save(presupuesto_file)

    actuals.to_csv(actuals_file, index=False)
    horas.to_csv(horas_file, index=False)
    billing.to_csv(billing_file, index=False)

    return {
        'presupuesto': str(presupuesto_file),
        'actuals': str(actuals_file),
        'horas': str(horas_file),
        'billing': str(billing_file),
    }


class TestMainPipeline:
    """Tests para el pipeline principal."""

    def test_main_basic_execution(self, sample_data_files, temp_output_dir):
        """Test que el pipeline se ejecuta correctamente."""
        success = main(
            actuals_file=sample_data_files['actuals'],
            horas_file=sample_data_files['horas'],
            billing_file=sample_data_files['billing'],
            presupuesto_file=sample_data_files['presupuesto'],
            current_month='202606',
            output_dir=temp_output_dir,
            verbose=False,
        )

        assert success

    def test_main_generates_output_files(self, sample_data_files, temp_output_dir):
        """Test que se generan los archivos de salida."""
        main(
            actuals_file=sample_data_files['actuals'],
            horas_file=sample_data_files['horas'],
            billing_file=sample_data_files['billing'],
            presupuesto_file=sample_data_files['presupuesto'],
            current_month='202606',
            output_dir=temp_output_dir,
            verbose=False,
        )

        # Verifica que se generaron los archivos
        assert os.path.exists(os.path.join(temp_output_dir, 'proyectos_margen.csv'))
        assert os.path.exists(os.path.join(temp_output_dir, 'metricas_mes.csv'))

    def test_main_proyecto_margen_format(self, sample_data_files, temp_output_dir):
        """Test que la tabla de proyectos tiene el formato correcto."""
        main(
            actuals_file=sample_data_files['actuals'],
            horas_file=sample_data_files['horas'],
            billing_file=sample_data_files['billing'],
            presupuesto_file=sample_data_files['presupuesto'],
            current_month='202606',
            output_dir=temp_output_dir,
            verbose=False,
        )

        df = pd.read_csv(os.path.join(temp_output_dir, 'proyectos_margen.csv'))

        # Verifica columnas esperadas
        expected_cols = [
            'cliente_origen', 'proyecto', 'ingreso', 'coste',
            'margen_eur', 'margen_pct', 'margen_pct_presupuestado',
            'desviacion_pct', 'semaforo'
        ]
        for col in expected_cols:
            assert col in df.columns

    def test_main_metrics_mes_format(self, sample_data_files, temp_output_dir):
        """Test que la tabla de métricas mensuales tiene el formato correcto."""
        main(
            actuals_file=sample_data_files['actuals'],
            horas_file=sample_data_files['horas'],
            billing_file=sample_data_files['billing'],
            presupuesto_file=sample_data_files['presupuesto'],
            current_month='202606',
            output_dir=temp_output_dir,
            verbose=False,
        )

        df = pd.read_csv(os.path.join(temp_output_dir, 'metricas_mes.csv'))

        # Verifica columnas
        assert 'mes' in df.columns
        assert 'es_cerrado' in df.columns
        assert 'semaforo' in df.columns

    def test_main_without_files(self, temp_output_dir):
        """Test que el pipeline funciona sin archivos."""
        success = main(
            actuals_file=None,
            horas_file=None,
            billing_file=None,
            presupuesto_file=None,
            current_month='202606',
            output_dir=temp_output_dir,
            verbose=False,
        )

        # No debería fallar, pero sin datos
        assert success

    def test_main_nonexistent_files(self, temp_output_dir):
        """Test que el pipeline maneja archivos inexistentes."""
        success = main(
            actuals_file='/nonexistent/actuals.csv',
            horas_file='/nonexistent/horas.csv',
            billing_file='/nonexistent/billing.csv',
            presupuesto_file='/nonexistent/presupuesto.xlsx',
            current_month='202606',
            output_dir=temp_output_dir,
            verbose=False,
        )

        # Debería completar sin errores (archivos opcionales)
        assert success

    def test_main_output_dir_created(self, sample_data_files):
        """Test que se crea el directorio de salida si no existe."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = os.path.join(tmpdir, 'new_output_dir')
            assert not os.path.exists(output_dir)

            main(
                actuals_file=sample_data_files['actuals'],
                horas_file=sample_data_files['horas'],
                billing_file=sample_data_files['billing'],
                presupuesto_file=sample_data_files['presupuesto'],
                current_month='202606',
                output_dir=output_dir,
                verbose=False,
            )

            assert os.path.exists(output_dir)

    def test_main_with_verbose(self, sample_data_files, temp_output_dir, capsys):
        """Test que el modo verbose imprime mensajes."""
        main(
            actuals_file=sample_data_files['actuals'],
            horas_file=sample_data_files['horas'],
            billing_file=sample_data_files['billing'],
            presupuesto_file=sample_data_files['presupuesto'],
            current_month='202606',
            output_dir=temp_output_dir,
            verbose=True,
        )

        captured = capsys.readouterr()
        assert '🚀' in captured.out or 'Iniciando' in captured.out
        assert '✅' in captured.out or 'completado' in captured.out


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
