"""
Science module — formula derivation, hypothesis testing, theory construction.
"""
from .formula_engine import FormulaEngine, DerivedFormula
from .hypothesis_tester import HypothesisTester, HypothesisTestResult
from .theory_builder import TheoryBuilder, ScientificTheory

__all__ = [
    "FormulaEngine",
    "DerivedFormula",
    "HypothesisTester",
    "HypothesisTestResult",
    "TheoryBuilder",
    "ScientificTheory",
]
