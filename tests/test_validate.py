"""Tests para el módulo de validación."""

import sys
import os
import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.validate import (
    normalize_key,
    extract_keys,
    find_unmapped,
    ValidationReport,
    validate_across_sources,
    get_valid_keys,
)


class TestNormalizeKey:
    """Tests para normalización de claves."""

    def test_normalize_key_basic(self):
        cliente, proyecto = normalize_key('CLIENTE A', 'PROYECTO X')
        assert cliente == 'CLIENTE A'
        assert proyecto == 'PROYECTO X'

    def test_normalize_key_lowercase(self):
        cliente, proyecto = normalize_key('cliente a', 'proyecto x')
        assert cliente == 'CLIENTE A'
        assert proyecto == 'PROYECTO X'

    def test_normalize_key_mixed_case(self):
        cliente, proyecto = normalize_key('ClIeNtE A', 'PrOyEcTo X')
        assert cliente == 'CLIENTE A'
        assert proyecto == 'PROYECTO X'

    def test_normalize_key_spaces(self):
        cliente, proyecto = normalize_key('  CLIENTE A  ', '  PROYECTO X  ')
        assert cliente == 'CLIENTE A'
        assert proyecto == 'PROYECTO X'

    def test_normalize_key_combined(self):
        cliente, proyecto = normalize_key('  cliente a  ', '  proyecto x  ')
        assert cliente == 'CLIENTE A'
        assert proyecto == 'PROYECTO X'


class TestExtractKeys:
    """Tests para extracción de claves."""

    def test_extract_keys_basic(self):
        df = pd.DataFrame({
            'cliente': ['CLIENTE A', 'CLIENTE B'],
            'proyecto': ['PROYECTO X', 'PROYECTO Y'],
        })
        keys = extract_keys(df, 'cliente', 'proyecto')
        assert keys == {('CLIENTE A', 'PROYECTO X'), ('CLIENTE B', 'PROYECTO Y')}

    def test_extract_keys_normalization(self):
        df = pd.DataFrame({
            'cliente': ['cliente a', ' CLIENTE A ', 'cliente a'],
            'proyecto': ['proyecto x', ' PROYECTO X ', 'proyecto x'],
        })
        keys = extract_keys(df, 'cliente', 'proyecto')
        # Debe haber solo una clave (duplicadas se eliminan)
        assert len(keys) == 1
        assert ('CLIENTE A', 'PROYECTO X') in keys

    def test_extract_keys_with_nan(self):
        df = pd.DataFrame({
            'cliente': ['CLIENTE A', 'CLIENTE B', None],
            'proyecto': ['PROYECTO X', 'PROYECTO Y', None],
        })
        keys = extract_keys(df, 'cliente', 'proyecto')
        # No debe incluir la fila con None
        assert len(keys) == 2

    def test_extract_keys_empty_dataframe(self):
        df = pd.DataFrame({'cliente': [], 'proyecto': []})
        keys = extract_keys(df, 'cliente', 'proyecto')
        assert keys == set()

    def test_extract_keys_single_row(self):
        df = pd.DataFrame({
            'cliente': ['CLIENTE A'],
            'proyecto': ['PROYECTO X'],
        })
        keys = extract_keys(df, 'cliente', 'proyecto')
        assert len(keys) == 1
        assert ('CLIENTE A', 'PROYECTO X') in keys


class TestFindUnmapped:
    """Tests para detección de no casados."""

    def test_find_unmapped_all_mapped(self):
        primary = pd.DataFrame({
            'cliente': ['CLIENTE A', 'CLIENTE B'],
            'proyecto': ['PROYECTO X', 'PROYECTO Y'],
        })
        reference = pd.DataFrame({
            'cliente': ['CLIENTE A', 'CLIENTE B'],
            'proyecto': ['PROYECTO X', 'PROYECTO Y'],
        })

        result = find_unmapped(
            primary, 'cliente', 'proyecto',
            reference, 'cliente', 'proyecto',
            'Primary', 'Reference'
        )

        assert result.shape[0] == 0

    def test_find_unmapped_some_missing(self):
        primary = pd.DataFrame({
            'cliente': ['CLIENTE A', 'CLIENTE B', 'CLIENTE C'],
            'proyecto': ['PROYECTO X', 'PROYECTO Y', 'PROYECTO Z'],
        })
        reference = pd.DataFrame({
            'cliente': ['CLIENTE A', 'CLIENTE B'],
            'proyecto': ['PROYECTO X', 'PROYECTO Y'],
        })

        result = find_unmapped(
            primary, 'cliente', 'proyecto',
            reference, 'cliente', 'proyecto',
            'Primary', 'Reference'
        )

        assert result.shape[0] == 1
        assert result.iloc[0]['cliente'] == 'CLIENTE C'
        assert result.iloc[0]['proyecto'] == 'PROYECTO Z'
        assert '_alert_type' in result.columns
        assert '_source' in result.columns

    def test_find_unmapped_normalization(self):
        primary = pd.DataFrame({
            'cliente': ['cliente a', ' CLIENTE B '],
            'proyecto': ['proyecto x', 'PROYECTO Y'],
        })
        reference = pd.DataFrame({
            'cliente': ['CLIENTE A'],
            'proyecto': ['PROYECTO X'],
        })

        result = find_unmapped(
            primary, 'cliente', 'proyecto',
            reference, 'cliente', 'proyecto',
            'Primary', 'Reference'
        )

        # CLIENTE B, PROYECTO Y no está en reference
        assert result.shape[0] == 1
        assert result.iloc[0]['cliente'] == ' CLIENTE B '


class TestValidationReport:
    """Tests para el reporte de validación."""

    def test_report_empty(self):
        report = ValidationReport()
        assert not report.has_alerts()
        assert report.summary() == {}
        assert report.to_dataframe().shape[0] == 0

    def test_report_add_alert(self):
        report = ValidationReport()
        report.add_alert(
            alert_type='TEST_ALERT',
            cliente='CLIENT A',
            proyecto='PROJECT X',
            source='Test',
            details='Test alert'
        )

        assert report.has_alerts()
        assert len(report.alerts) == 1
        assert report.summary()['TEST_ALERT'] == 1

    def test_report_multiple_alerts(self):
        report = ValidationReport()
        report.add_alert('ALERT1', 'CLIENT A', 'PROJECT X', 'Source1')
        report.add_alert('ALERT1', 'CLIENT B', 'PROJECT Y', 'Source1')
        report.add_alert('ALERT2', 'CLIENT C', 'PROJECT Z', 'Source2')

        assert report.has_alerts()
        summary = report.summary()
        assert summary['ALERT1'] == 2
        assert summary['ALERT2'] == 1

    def test_report_to_dataframe(self):
        report = ValidationReport()
        report.add_alert('TEST', 'CLIENT A', 'PROJECT X', 'Source')

        df = report.to_dataframe()
        assert df.shape[0] == 1
        assert df.iloc[0]['alert_type'] == 'TEST'


class TestValidateAcrossSources:
    """Tests para validación cruzada de fuentes."""

    @pytest.fixture
    def perfect_data(self):
        """Datos perfectamente alineados."""
        presupuesto = pd.DataFrame({
            'cliente_origen': ['CLIENT A', 'CLIENT B'],
            'proyecto': ['PROJECT X', 'PROJECT Y'],
            'to_launch': [True, True],
        })

        actuals = pd.DataFrame({
            'cliente': ['CLIENT A', 'CLIENT B'],
            'proyecto': ['PROJECT X', 'PROJECT Y'],
        })

        horas = pd.DataFrame({
            'cliente': ['CLIENT A', 'CLIENT B'],
            'proyecto': ['PROJECT X', 'PROJECT Y'],
        })

        billing = pd.DataFrame({
            'cliente_origen': ['CLIENT A', 'CLIENT B'],
            'proyecto': ['PROJECT X', 'PROJECT Y'],
        })

        return presupuesto, actuals, horas, billing

    def test_validate_perfect_alignment(self, perfect_data):
        presupuesto, actuals, horas, billing = perfect_data
        report = validate_across_sources(actuals, horas, billing, presupuesto)

        assert not report.has_alerts()

    def test_validate_actuals_not_in_budget(self, perfect_data):
        presupuesto, actuals, horas, billing = perfect_data

        # Añade un cliente/proyecto en actuals que no está en presupuesto
        actuals_extra = pd.DataFrame({
            'cliente': ['CLIENT A', 'CLIENT B', 'CLIENT C'],
            'proyecto': ['PROJECT X', 'PROJECT Y', 'PROJECT Z'],
        })

        report = validate_across_sources(actuals_extra, horas, billing, presupuesto)

        assert report.has_alerts()
        summary = report.summary()
        assert 'ACTUALS_NOT_IN_BUDGET' in summary
        assert summary['ACTUALS_NOT_IN_BUDGET'] == 1

    def test_validate_billing_not_in_budget(self, perfect_data):
        presupuesto, actuals, horas, billing = perfect_data

        billing_extra = pd.DataFrame({
            'cliente_origen': ['CLIENT A', 'CLIENT B', 'CLIENT D'],
            'proyecto': ['PROJECT X', 'PROJECT Y', 'PROJECT W'],
        })

        report = validate_across_sources(actuals, horas, billing_extra, presupuesto)

        assert report.has_alerts()
        summary = report.summary()
        assert 'BILLING_NOT_IN_BUDGET' in summary

    def test_validate_horas_not_in_budget(self, perfect_data):
        presupuesto, actuals, horas, billing = perfect_data

        horas_extra = pd.DataFrame({
            'cliente': ['CLIENT A', 'CLIENT B', 'CLIENT E'],
            'proyecto': ['PROJECT X', 'PROJECT Y', 'PROJECT V'],
        })

        report = validate_across_sources(actuals, horas_extra, billing, presupuesto)

        assert report.has_alerts()
        summary = report.summary()
        assert 'HORAS_NOT_IN_BUDGET' in summary

    def test_validate_budget_no_data(self, perfect_data):
        presupuesto, actuals, horas, billing = perfect_data

        # Presupuesto con un proyecto sin datos en ninguna fuente
        presupuesto_extra = presupuesto.copy()
        presupuesto_extra = pd.concat([
            presupuesto_extra,
            pd.DataFrame({
                'cliente_origen': ['CLIENT F'],
                'proyecto': ['PROJECT U'],
                'to_launch': [True],
            })
        ], ignore_index=True)

        # Usa datos vacíos para actuals, horas, billing
        empty_df = pd.DataFrame({'cliente': [], 'proyecto': []})
        empty_billing = pd.DataFrame({'cliente_origen': [], 'proyecto': []})

        report = validate_across_sources(empty_df, empty_df, empty_billing, presupuesto_extra)

        assert report.has_alerts()
        summary = report.summary()
        assert 'BUDGET_NO_DATA' in summary

    def test_validate_to_launch_false_ignored(self, perfect_data):
        presupuesto, actuals, horas, billing = perfect_data

        # Presupuesto con un proyecto pero TO_LAUNCH=False
        presupuesto_mixed = presupuesto.copy()
        presupuesto_mixed = pd.concat([
            presupuesto_mixed,
            pd.DataFrame({
                'cliente_origen': ['CLIENT G'],
                'proyecto': ['PROJECT T'],
                'to_launch': [False],
            })
        ], ignore_index=True)

        # Añade datos para CLIENT G en actuals
        actuals_with_g = pd.concat([
            actuals,
            pd.DataFrame({
                'cliente': ['CLIENT G'],
                'proyecto': ['PROJECT T'],
            })
        ], ignore_index=True)

        report = validate_across_sources(actuals_with_g, horas, billing, presupuesto_mixed)

        # No debe alertar por CLIENT G porque TO_LAUNCH=False
        assert not report.has_alerts()


class TestGetValidKeys:
    """Tests para obtener las claves válidas."""

    def test_get_valid_keys_basic(self):
        presupuesto = pd.DataFrame({
            'cliente_origen': ['CLIENT A', 'CLIENT B', 'CLIENT C'],
            'proyecto': ['PROJECT X', 'PROJECT Y', 'PROJECT Z'],
            'to_launch': [True, False, True],
        })

        # Los otros pueden estar vacíos
        empty_df = pd.DataFrame({'cliente': [], 'proyecto': []})
        empty_billing = pd.DataFrame({'cliente_origen': [], 'proyecto': []})

        keys = get_valid_keys(empty_df, empty_df, empty_billing, presupuesto)

        # Solo debe incluir los con TO_LAUNCH=True
        assert len(keys) == 2
        assert ('CLIENT A', 'PROJECT X') in keys
        assert ('CLIENT C', 'PROJECT Z') in keys
        assert ('CLIENT B', 'PROJECT Y') not in keys

    def test_get_valid_keys_empty_presupuesto(self):
        presupuesto = pd.DataFrame({
            'cliente_origen': [],
            'proyecto': [],
            'to_launch': [],
        })

        empty_df = pd.DataFrame({'cliente': [], 'proyecto': []})
        empty_billing = pd.DataFrame({'cliente_origen': [], 'proyecto': []})

        keys = get_valid_keys(empty_df, empty_df, empty_billing, presupuesto)

        assert len(keys) == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
