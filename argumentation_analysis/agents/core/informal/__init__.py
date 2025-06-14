# src/argumentation_analysis/agents/core/informal/__init__.py
"""
Package `informal` pour l'analyse informelle des arguments.

Ce package contient les composants relatifs à l'analyse des arguments
en langage naturel, en se concentrant sur les aspects informels tels que
l'identification des types de sophismes, l'évaluation de la force persuasive,
et d'autres analyses rhétoriques qui ne reposent pas sur une logique formelle stricte.

Modules et classes clés :
    - `InformalAgent`: L'agent principal pour l'analyse informelle.
    - `informal_definitions`: Structures de données et taxonomies pour l'analyse informelle.
    - `prompts`: Templates de prompts pour guider le LLM dans les tâches d'analyse informelle.
"""

try:
    from .informal_agent import InformalAnalysisAgent as InformalAgent
    # from .informal_definitions import (
    #     # FallacyDefinition, # Commenté car non défini dans informal_definitions.py
    #     # RhetoricalStrategy, # Commenté car non défini dans informal_definitions.py
    #     # InformalArgument, # Commenté car non défini dans informal_definitions.py
    #     # AnalysisResult, # Commenté car non défini dans informal_definitions.py
    #     # FALLACY_TAXONOMY_SYSTEM_PROMPT, # Commenté car non défini dans informal_definitions.py (ni prompts.py)
    #     # FALLACY_ANALYSIS_PROMPT_TEMPLATE, # Commenté car non défini dans informal_definitions.py (ni prompts.py)
    #     # RHETORICAL_STRATEGY_PROMPT_TEMPLATE # Commenté car non défini dans informal_definitions.py (ni prompts.py)
    # )
    # Les prompts spécifiques sont souvent dans leur propre module,
    # mais s'ils sont définis ici ou dans informal_definitions, ils seraient listés.

    __all__ = [
        "InformalAgent",
        # "FallacyDefinition", # Commenté car non défini dans informal_definitions.py
        # "RhetoricalStrategy", # Commenté car non défini dans informal_definitions.py
        # "InformalArgument", # Commenté car non défini dans informal_definitions.py
        # "AnalysisResult", # Commenté car non défini dans informal_definitions.py
        # "FALLACY_TAXONOMY_SYSTEM_PROMPT", # Commenté
        # "FALLACY_ANALYSIS_PROMPT_TEMPLATE", # Commenté
        # "RHETORICAL_STRATEGY_PROMPT_TEMPLATE" # Commenté
    ]
except ImportError as e:
    import logging
    logging.warning(f"Certains composants de 'agents.core.informal' n'ont pas pu être importés/exposés: {e}")
    __all__ = []