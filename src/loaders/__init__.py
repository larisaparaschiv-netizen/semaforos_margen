"""Loaders para diferentes fuentes de datos."""

from .actuals import load_actuals
from .horas import load_horas
from .billing import load_billing
from .presupuesto import load_presupuesto

__all__ = ['load_actuals', 'load_horas', 'load_billing', 'load_presupuesto']
