"""Configuración de la herramienta de margen de proyectos."""

# Umbrales del semáforo (en puntos porcentuales)
SEMAFORO_VERDE = 2.5  # desviación <= 2.5 pp
SEMAFORO_AMBAR_MAX = 5.0  # desviación > 2.5 pp y <= 5 pp
# > 5 pp es rojo

# Mes actual (YYYYMM format) - se puede sobrescribir en runtime
CURRENT_MONTH = "202406"  # placeholder

# Moneda
CURRENCY = "EUR"

# Categorías de billing que cuentan
BILLING_VALID_STATUS = []  # se define en origen / a configurar

# Categorías de actuals
ACTUALS_REVENUE_CONCEPT = "Revenue Labor"
ACTUALS_COSTS_CONCEPT = "Costs"
