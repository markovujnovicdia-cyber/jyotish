"""
Yoga Engine - deterministički, pravilima-vođen sustav za otkrivanje
klasičnih Jyotish yoga u D1 (Rāśi) karti.

Vidi core/yoga_engine/registry.py za katalog i core/yoga_engine/context.py
za zajedničke helper funkcije. Javno sučelje:

    from core.yoga_engine.context import ChartContext
    from core.yoga_engine.registry import run_all_yogas

    chart = ChartContext(ascendant_longitude=..., ascendant_sign_index=...,
                          positions=..., special_points=...)
    results = run_all_yogas(chart)  # List[YogaResult]
"""
