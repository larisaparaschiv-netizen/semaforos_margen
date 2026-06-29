"""Tests para el módulo de métricas."""

import sys
import os
import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.metrics import (
    calculate_margin_eur,
    calculate_margin_pct,
    calculate_traffic_light,
    aggregate_by_proyecto_mes,
    aggregate_by_proyecto,
    TrafficLight,
)


class TestCalculateMarginEur:
    """Tests para cálculo de margen en EUR."""

    def test_positive_margin(self):
        assert calculate_margin_eur(1000, 600) == 400

    def test_negative_margin(self):
        assert calculate_margin_eur(500, 800) == -300

    def test_zero_margin(self):
        assert calculate_margin_eur(1000, 1000) == 0

    def test_zero_ingreso(self):
        assert calculate_margin_eur(0, 500) == -500

    def test_zero_coste(self):
        assert calculate_margin_eur(1000, 0) == 1000

    def test_example_from_spec(self):
        # Del SPEC: ingresos 450.589 €, costes 150.000 €
        ingreso = 450589.0
        coste = 150000.0
        margen = calculate_margin_eur(ingreso, coste)
        assert margen == 300589.0


class TestCalculateMarginPct:
    """Tests para cálculo de margen en porcentaje."""

    def test_positive_margin_pct(self):
        margen = calculate_margin_pct(1000, 600)
        assert margen == 40.0

    def test_negative_margin_pct(self):
        margen = calculate_margin_pct(500, 800)
        assert margen == -60.0

    def test_zero_margin_pct(self):
        margen = calculate_margin_pct(1000, 1000)
        assert margen == 0.0

    def test_zero_ingreso(self):
        # Con ingreso 0, margen % es 0 por defecto
        margen = calculate_margin_pct(0, 500)
        assert margen == 0.0

    def test_example_from_spec(self):
        # Del SPEC: ingresos 450.589 €, costes 150.000 €
        ingreso = 450589.0
        coste = 150000.0
        margen_pct = calculate_margin_pct(ingreso, coste)
        # (450589 - 150000) / 450589 * 100 = 66.73%
        assert abs(margen_pct - 66.73) < 0.1

    def test_50_percent_margin(self):
        margen = calculate_margin_pct(200, 100)
        assert margen == 50.0

    def test_25_percent_margin(self):
        margen = calculate_margin_pct(800, 600)
        assert margen == 25.0


class TestCalculateTrafficLight:
    """Tests para el cálculo del semáforo."""

    def test_green_no_deviation(self):
        light = calculate_traffic_light(20.0, 20.0)
        assert light == TrafficLight.GREEN

    def test_green_small_deviation(self):
        light = calculate_traffic_light(22.0, 20.0)
        assert light == TrafficLight.GREEN

    def test_green_exact_threshold(self):
        light = calculate_traffic_light(22.5, 20.0)
        assert light == TrafficLight.GREEN

    def test_amber_below_amber_threshold(self):
        light = calculate_traffic_light(24.0, 20.0)
        assert light == TrafficLight.AMBER

    def test_amber_mid_range(self):
        light = calculate_traffic_light(23.0, 20.0)
        assert light == TrafficLight.AMBER

    def test_amber_exact_amber_threshold(self):
        light = calculate_traffic_light(25.0, 20.0)
        assert light == TrafficLight.AMBER

    def test_red_over_threshold(self):
        light = calculate_traffic_light(26.0, 20.0)
        assert light == TrafficLight.RED

    def test_red_large_deviation(self):
        light = calculate_traffic_light(35.0, 20.0)
        assert light == TrafficLight.RED

    def test_negative_real_margin(self):
        # Margen real negativo pero presupuestado positivo
        light = calculate_traffic_light(-10.0, 15.0)
        # Desviación = |−10 − 15| = 25, es rojo
        assert light == TrafficLight.RED

    def test_custom_thresholds(self):
        # Con umbrales diferentes
        light = calculate_traffic_light(23.0, 20.0, green_threshold=5.0, amber_threshold=10.0)
        assert light == TrafficLight.GREEN

    def test_symmetrical_deviation(self):
        # Desviación en ambos sentidos
        light1 = calculate_traffic_light(22.0, 20.0)
        light2 = calculate_traffic_light(18.0, 20.0)
        assert light1 == light2 == TrafficLight.GREEN


class TestAggregateByProyectoMes:
    """Tests para agregación por proyecto × mes."""

    @pytest.fixture
    def sample_presupuesto(self):
        return pd.DataFrame({
            'cliente_origen': ['CLIENT A', 'CLIENT B'],
            'proyecto': ['PROJECT X', 'PROJECT Y'],
            'to_launch': [True, True],
            'ingreso_presupuestado': [500000.0, 300000.0],
            'coste_presupuestado': [400000.0, 250000.0],
        })

    def test_aggregate_closed_month_from_actuals(self, sample_presupuesto):
        # Mes cerrado: usa actuals
        # Presupuesto: ingreso 500000, coste 400000 → margen 20%
        # Actuals: ingreso 500000, coste 400000 → margen 20% → sin desviación → verde
        actuals = pd.DataFrame({
            'cliente': ['CLIENT A', 'CLIENT A'],
            'proyecto': ['PROJECT X', 'PROJECT X'],
            'periodo': ['202404', '202404'],
            'concepto': ['Revenue', 'Costs'],
            'importe': [500000.0, 400000.0],
        })

        horas = pd.DataFrame({'cliente': [], 'proyecto': [], 'fecha': [], 'costo': []})
        billing = pd.DataFrame({'cliente_origen': [], 'proyecto': [], 'mes': [], 'importe_eur': []})

        result = aggregate_by_proyecto_mes(actuals, horas, billing, sample_presupuesto, '202406')

        assert result.shape[0] == 1
        row = result.iloc[0]
        assert row['cliente_origen'] == 'CLIENT A'
        assert row['proyecto'] == 'PROJECT X'
        assert row['mes'] == '202404'
        assert row['es_cerrado'] == True
        assert row['ingreso'] == 500000.0
        assert row['coste'] == 400000.0
        assert row['margen_eur'] == 100000.0
        assert row['semaforo'] == 'verde'

    def test_aggregate_current_month_from_billing_horas(self):
        # Mes actual (202606): usa billing + horas
        # Presupuesto solo con CLIENT A
        presupuesto = pd.DataFrame({
            'cliente_origen': ['CLIENT A'],
            'proyecto': ['PROJECT X'],
            'to_launch': [True],
            'ingreso_presupuestado': [500000.0],
            'coste_presupuestado': [400000.0],
        })

        actuals = pd.DataFrame({'cliente': [], 'proyecto': [], 'periodo': [], 'concepto': [], 'importe': []})

        # Horas en junio 2026
        horas = pd.DataFrame({
            'cliente': ['CLIENT A'],
            'proyecto': ['PROJECT X'],
            'fecha': pd.to_datetime(['2026-06-15']),
            'costo': [5000.0],
        })

        billing = pd.DataFrame({
            'cliente_origen': ['CLIENT A'],
            'proyecto': ['PROJECT X'],
            'mes': ['202606'],
            'importe_eur': [150000.0],
        })

        # Mes actual es 202606, así que es el mes en curso
        result = aggregate_by_proyecto_mes(actuals, horas, billing, presupuesto, '202606')

        assert result.shape[0] == 1
        row = result.iloc[0]
        assert row['mes'] == '202606'
        assert row['es_cerrado'] == False  # Es el mes en curso
        assert row['ingreso'] == 150000.0
        assert row['coste'] == 5000.0

    def test_aggregate_multiple_meses(self, sample_presupuesto):
        actuals = pd.DataFrame({
            'cliente': ['CLIENT A', 'CLIENT A', 'CLIENT A', 'CLIENT A'],
            'proyecto': ['PROJECT X', 'PROJECT X', 'PROJECT X', 'PROJECT X'],
            'periodo': ['202404', '202404', '202405', '202405'],
            'concepto': ['Revenue', 'Costs', 'Revenue', 'Costs'],
            'importe': [100000.0, 60000.0, 120000.0, 70000.0],
        })

        horas = pd.DataFrame({'cliente': [], 'proyecto': [], 'fecha': [], 'costo': []})
        billing = pd.DataFrame({'cliente_origen': [], 'proyecto': [], 'mes': [], 'importe_eur': []})

        result = aggregate_by_proyecto_mes(actuals, horas, billing, sample_presupuesto, '202406')

        assert result.shape[0] == 2
        # Ambos meses deben estar cerrados
        assert all(result['es_cerrado'] == True)

    def test_aggregate_multiple_proyectos(self, sample_presupuesto):
        actuals = pd.DataFrame({
            'cliente': ['CLIENT A', 'CLIENT A', 'CLIENT B', 'CLIENT B'],
            'proyecto': ['PROJECT X', 'PROJECT X', 'PROJECT Y', 'PROJECT Y'],
            'periodo': ['202404', '202404', '202404', '202404'],
            'concepto': ['Revenue', 'Costs', 'Revenue', 'Costs'],
            'importe': [100000.0, 60000.0, 80000.0, 50000.0],
        })

        horas = pd.DataFrame({'cliente': [], 'proyecto': [], 'fecha': [], 'costo': []})
        billing = pd.DataFrame({'cliente_origen': [], 'proyecto': [], 'mes': [], 'importe_eur': []})

        result = aggregate_by_proyecto_mes(actuals, horas, billing, sample_presupuesto, '202406')

        assert result.shape[0] == 2
        clientes = result['cliente_origen'].unique()
        assert 'CLIENT A' in clientes
        assert 'CLIENT B' in clientes

    def test_example_from_spec(self, sample_presupuesto):
        # Ejemplo del SPEC: ingresos 450.589, costes 150.000
        actuals = pd.DataFrame({
            'cliente': ['CLIENT A', 'CLIENT A'],
            'proyecto': ['PROJECT X', 'PROJECT X'],
            'periodo': ['202404', '202404'],
            'concepto': ['Revenue', 'Costs'],
            'importe': [450589.0, 150000.0],
        })

        horas = pd.DataFrame({'cliente': [], 'proyecto': [], 'fecha': [], 'costo': []})
        billing = pd.DataFrame({'cliente_origen': [], 'proyecto': [], 'mes': [], 'importe_eur': []})

        result = aggregate_by_proyecto_mes(actuals, horas, billing, sample_presupuesto, '202406')

        assert result.shape[0] == 1
        row = result.iloc[0]
        assert abs(row['margen_eur'] - 300589.0) < 1.0
        assert abs(row['margen_pct'] - 66.73) < 0.1


class TestAggregateByProyecto:
    """Tests para agregación por proyecto (suma de todos los meses)."""

    def test_aggregate_single_proyecto_single_mes(self):
        metrics = pd.DataFrame({
            'cliente_origen': ['CLIENT A'],
            'proyecto': ['PROJECT X'],
            'ingreso': [100000.0],
            'coste': [60000.0],
            'ingreso_presupuestado': [500000.0],
            'coste_presupuestado': [400000.0],
        })

        result = aggregate_by_proyecto(metrics)

        assert result.shape[0] == 1
        row = result.iloc[0]
        assert row['ingreso'] == 100000.0
        assert row['margen_eur'] == 40000.0

    def test_aggregate_single_proyecto_multiple_meses(self):
        metrics = pd.DataFrame({
            'cliente_origen': ['CLIENT A', 'CLIENT A'],
            'proyecto': ['PROJECT X', 'PROJECT X'],
            'ingreso': [100000.0, 120000.0],
            'coste': [60000.0, 70000.0],
            'ingreso_presupuestado': [500000.0, 500000.0],
            'coste_presupuestado': [400000.0, 400000.0],
        })

        result = aggregate_by_proyecto(metrics)

        assert result.shape[0] == 1
        row = result.iloc[0]
        assert row['ingreso'] == 220000.0
        assert row['coste'] == 130000.0
        assert row['margen_eur'] == 90000.0

    def test_aggregate_multiple_proyectos(self):
        metrics = pd.DataFrame({
            'cliente_origen': ['CLIENT A', 'CLIENT B'],
            'proyecto': ['PROJECT X', 'PROJECT Y'],
            'ingreso': [100000.0, 80000.0],
            'coste': [60000.0, 50000.0],
            'ingreso_presupuestado': [500000.0, 300000.0],
            'coste_presupuestado': [400000.0, 250000.0],
        })

        result = aggregate_by_proyecto(metrics)

        assert result.shape[0] == 2

    def test_aggregate_empty_dataframe(self):
        metrics = pd.DataFrame()
        result = aggregate_by_proyecto(metrics)
        assert result.shape[0] == 0

    def test_aggregate_calculates_traffic_light(self):
        # Proyecto con margen real 30%, presupuestado 25% → desviación 5% → ámbar
        metrics = pd.DataFrame({
            'cliente_origen': ['CLIENT A'],
            'proyecto': ['PROJECT X'],
            'ingreso': [1000.0],
            'coste': [700.0],
            'ingreso_presupuestado': [1000.0],
            'coste_presupuestado': [750.0],
        })

        result = aggregate_by_proyecto(metrics)

        row = result.iloc[0]
        assert row['margen_pct'] == 30.0
        assert row['margen_pct_presupuestado'] == 25.0
        assert row['desviacion_pct'] == 5.0
        assert row['semaforo'] == 'ambar'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
