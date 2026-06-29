"""Tests para el loader de actuals."""

import sys
import os
import pandas as pd
import tempfile
from pathlib import Path
import pytest

# Añade src/ al path para imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.loaders.actuals import load_actuals, _normalize_concepto


class TestNormalizeConcepto:
    """Tests para la normalización de conceptos."""

    def test_revenue_english(self):
        assert _normalize_concepto('Revenue Labor') == 'Revenue'
        assert _normalize_concepto('revenue') == 'Revenue'

    def test_revenue_spanish(self):
        assert _normalize_concepto('Ingreso') == 'Revenue'
        assert _normalize_concepto('ingreso') == 'Revenue'

    def test_costs(self):
        assert _normalize_concepto('Costs') == 'Costs'
        assert _normalize_concepto('costs') == 'Costs'
        assert _normalize_concepto('coste') == 'Costs'
        assert _normalize_concepto('Coste') == 'Costs'

    def test_unknown(self):
        assert _normalize_concepto('Other') == 'Other'


class TestLoadActuals:
    """Tests para la carga y normalización de actuals."""

    @pytest.fixture
    def sample_data(self):
        """Datos de prueba realistas."""
        return {
            'PeriodoYYYYMM': ['202404', '202404', '202404', '202405', '202405'],
            'Concepto': ['Revenue Labor', 'Costs', 'Costs', 'Revenue Labor', 'Costs'],
            'CC': ['Salaries & Wages', 'Salaries & Wages', 'Office Expenses', 'Salaries & Wages', 'Professional Service'],
            'EnMLCeBe': [-450589.50, 125000.00, 25000.00, -520000.00, 150000.00],
            'Client': ['CLIENTE A', 'CLIENTE A', 'CLIENTE A', 'CLIENTE B', 'CLIENTE B'],
            'Project': ['Proyecto X', 'Proyecto X', 'Proyecto X', 'Proyecto Y', 'Proyecto Y'],
            'Glober': ['PERSONA 1', 'PERSONA 1', None, 'PERSONA 2', 'PERSONA 2'],
            'ContractType': ['TYM', 'TYM', 'TYM', 'FEE', 'FEE'],
        }

    def test_load_from_csv(self, sample_data, tmp_path):
        """Test carga desde CSV."""
        csv_file = tmp_path / "actuals.csv"
        df_input = pd.DataFrame(sample_data)
        df_input.to_csv(csv_file, index=False)

        df = load_actuals(str(csv_file))

        assert df.shape[0] == 5
        assert list(df.columns) == [
            'periodo', 'cliente', 'proyecto', 'concepto', 'cc', 'importe', 'persona', 'tipo_contrato'
        ]

    def test_load_from_excel(self, sample_data, tmp_path):
        """Test carga desde Excel."""
        excel_file = tmp_path / "actuals.xlsx"
        df_input = pd.DataFrame(sample_data)
        df_input.to_excel(excel_file, index=False)

        df = load_actuals(str(excel_file))

        assert df.shape[0] == 5
        assert 'importe' in df.columns

    def test_revenue_sign_inverted(self, sample_data, tmp_path):
        """Test que el signo del ingreso se invierte (Revenue viene en negativo)."""
        csv_file = tmp_path / "actuals.csv"
        df_input = pd.DataFrame(sample_data)
        df_input.to_csv(csv_file, index=False)

        df = load_actuals(str(csv_file))

        # Filtra Revenue
        revenue_rows = df[df['concepto'] == 'Revenue']
        assert len(revenue_rows) == 2
        # El ingreso original era -450589.50 y -520000.00, debe ser positivo
        assert revenue_rows.iloc[0]['importe'] == 450589.50
        assert revenue_rows.iloc[1]['importe'] == 520000.00

    def test_costs_sign_preserved(self, sample_data, tmp_path):
        """Test que el signo del coste se preserva (viene en positivo)."""
        csv_file = tmp_path / "actuals.csv"
        df_input = pd.DataFrame(sample_data)
        df_input.to_csv(csv_file, index=False)

        df = load_actuals(str(csv_file))

        # Filtra Costs
        costs_rows = df[df['concepto'] == 'Costs']
        assert len(costs_rows) == 3
        assert costs_rows.iloc[0]['importe'] == 125000.00
        assert costs_rows.iloc[1]['importe'] == 25000.00
        assert costs_rows.iloc[2]['importe'] == 150000.00

    def test_normalization_cliente_proyecto(self, sample_data, tmp_path):
        """Test normalización de texto: mayúsculas y espacios."""
        # Añade espacios en blanco para testing
        sample_data_with_spaces = sample_data.copy()
        sample_data_with_spaces['Client'] = [' CLIENTE A ', 'cliente a', ' CLIENTE A ', ' CLIENTE B', 'cliente b']
        sample_data_with_spaces['Project'] = ['  Proyecto X  ', 'proyecto x', ' Proyecto X ', 'Proyecto Y', ' proyecto y ']

        csv_file = tmp_path / "actuals.csv"
        df_input = pd.DataFrame(sample_data_with_spaces)
        df_input.to_csv(csv_file, index=False)

        df = load_actuals(str(csv_file))

        # Todas las cliente deben ser uppercase
        assert df['cliente'].unique().tolist() == ['CLIENTE A', 'CLIENTE B']
        assert df['proyecto'].unique().tolist() == ['PROYECTO X', 'PROYECTO Y']

    def test_columns_renamed_correctly(self, sample_data, tmp_path):
        """Test que las columnas originales se renombran correctamente."""
        csv_file = tmp_path / "actuals.csv"
        df_input = pd.DataFrame(sample_data)
        df_input.to_csv(csv_file, index=False)

        df = load_actuals(str(csv_file))

        # Verifica que no existen las columnas originales
        assert 'PeriodoYYYYMM' not in df.columns
        assert 'Concepto' not in df.columns
        assert 'EnMLCeBe' not in df.columns

        # Verifica que existen las nuevas
        assert 'periodo' in df.columns
        assert 'concepto' in df.columns
        assert 'importe' in df.columns

    def test_missing_optional_columns(self, tmp_path):
        """Test que funciona incluso si faltan columnas opcionales."""
        minimal_data = {
            'PeriodoYYYYMM': ['202404', '202404'],
            'Concepto': ['Revenue Labor', 'Costs'],
            'EnMLCeBe': [-450589.50, 125000.00],
            'Client': ['CLIENTE A', 'CLIENTE A'],
            'Project': ['Proyecto X', 'Proyecto X'],
        }

        csv_file = tmp_path / "actuals.csv"
        df_input = pd.DataFrame(minimal_data)
        df_input.to_csv(csv_file, index=False)

        df = load_actuals(str(csv_file))

        assert df.shape[0] == 2
        assert 'cc' in df.columns
        assert 'persona' in df.columns
        assert 'tipo_contrato' in df.columns

    def test_data_types(self, sample_data, tmp_path):
        """Test que los tipos de datos son correctos."""
        csv_file = tmp_path / "actuals.csv"
        df_input = pd.DataFrame(sample_data)
        df_input.to_csv(csv_file, index=False)

        df = load_actuals(str(csv_file))

        assert df['periodo'].dtype == 'object'  # str
        assert df['importe'].dtype == 'float64'
        assert df['cliente'].dtype == 'object'
        assert df['proyecto'].dtype == 'object'

    def test_example_from_spec(self, tmp_path):
        """Test con el ejemplo mencionado en SPEC: margen ≈ 450.589 €."""
        # Crea datos que producen el margen del ejemplo
        test_data = {
            'PeriodoYYYYMM': ['202404', '202404', '202404'],
            'Concepto': ['Revenue Labor', 'Costs', 'Costs'],
            'CC': ['', 'Salaries & Wages', 'Office Expenses'],
            'EnMLCeBe': [-450589.00, 100000.00, 50000.00],
            'Client': ['TEST CLIENT', 'TEST CLIENT', 'TEST CLIENT'],
            'Project': ['TEST PROJECT', 'TEST PROJECT', 'TEST PROJECT'],
            'Glober': ['P1', 'P1', 'P2'],
            'ContractType': ['TYM', 'TYM', 'TYM'],
        }

        csv_file = tmp_path / "actuals.csv"
        df_input = pd.DataFrame(test_data)
        df_input.to_csv(csv_file, index=False)

        df = load_actuals(str(csv_file))

        # Calcula el margen
        revenue = df[df['concepto'] == 'Revenue']['importe'].sum()
        costs = df[df['concepto'] == 'Costs']['importe'].sum()
        margen = revenue - costs

        assert revenue == 450589.00
        assert costs == 150000.00
        assert margen == 300589.00  # ingresos - costes


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
