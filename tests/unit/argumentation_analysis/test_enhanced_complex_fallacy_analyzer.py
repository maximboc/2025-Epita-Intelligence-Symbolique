# -*- coding: utf-8 -*-
"""
Tests unitaires pour le module EnhancedComplexFallacyAnalyzer.
"""

import unittest
from unittest.mock import patch, MagicMock
import json
from argumentation_analysis.agents.tools.analysis.enhanced.complex_fallacy_analyzer import EnhancedComplexFallacyAnalyzer


class TestEnhancedComplexFallacyAnalyzer(unittest.TestCase):
    """Tests pour la classe EnhancedComplexFallacyAnalyzer."""

    def setUp(self):
        """Initialisation avant chaque test."""
        # Créer une instance de l'analyseur
        self.analyzer = EnhancedComplexFallacyAnalyzer()
        
        # Données de test
        self.test_arguments = [
            "Les experts affirment que ce produit est sûr.",
            "Ce produit est utilisé par des millions de personnes.",
            "Par conséquent, vous devriez faire confiance aux experts et utiliser ce produit.",
            "Si vous n'utilisez pas ce produit, vous risquez de souffrir de problèmes de santé graves."
        ]
        self.test_context = "commercial"

    def test_init(self):
        """Teste l'initialisation de l'analyseur."""
        # Vérifier que l'analyseur est correctement initialisé
        self.assertIsNotNone(self.analyzer)
        self.assertIsNotNone(self.analyzer.contextual_analyzer)
        self.assertIsNotNone(self.analyzer.severity_evaluator)
        self.assertIsNotNone(self.analyzer.argument_structure_patterns)
        self.assertIsNotNone(self.analyzer.advanced_fallacy_combinations)
        self.assertEqual(len(self.analyzer.analysis_history), 0)

    def test_define_argument_structure_patterns(self):
        """Teste la définition des modèles de structure argumentative."""
        patterns = self.analyzer._define_argument_structure_patterns()
        
        # Vérifier que les modèles sont correctement définis
        self.assertIsInstance(patterns, dict)
        self.assertIn("chaîne_causale", patterns)
        self.assertIn("structure_conditionnelle", patterns)
        self.assertIn("structure_comparative", patterns)
        self.assertIn("structure_autorité", patterns)
        self.assertIn("structure_généralisation", patterns)
        
        # Vérifier la structure d'un modèle
        pattern = patterns["chaîne_causale"]
        self.assertIn("description", pattern)
        self.assertIn("detection_pattern", pattern)
        self.assertIn("fallacy_risk", pattern)
        self.assertIn("complexity_score", pattern)

    def test_define_advanced_fallacy_combinations(self):
        """Teste la définition des modèles de sophismes composés avancés."""
        combinations = self.analyzer._define_advanced_fallacy_combinations()
        
        # Vérifier que les combinaisons sont correctement définies
        self.assertIsInstance(combinations, dict)
        self.assertIn("cascade_émotionnelle", combinations)
        self.assertIn("cercle_autoritaire", combinations)
        self.assertIn("diversion_complexe", combinations)
        self.assertIn("fausse_causalité_composée", combinations)
        self.assertIn("manipulation_cognitive", combinations)
        
        # Vérifier la structure d'une combinaison
        combo = combinations["cascade_émotionnelle"]
        self.assertIn("description", combo)
        self.assertIn("components", combo)
        self.assertIn("pattern", combo)
        self.assertIn("severity_modifier", combo)
        self.assertIn("detection_threshold", combo)

    def test_detect_circular_reasoning(self):
        """Teste la détection de raisonnement circulaire."""
        # Graphe sans cycle
        graph_no_cycle = {
            1: [2, 3],
            2: [4],
            3: [4],
            4: []
        }
        self.assertFalse(self.analyzer._detect_circular_reasoning(graph_no_cycle))
        
        # Graphe avec cycle
        graph_with_cycle = {
            1: [2],
            2: [3],
            3: [1]
        }
        self.assertTrue(self.analyzer._detect_circular_reasoning(graph_with_cycle))

    def test_calculate_simple_similarity(self):
        """Teste le calcul de similarité simple entre deux textes."""
        # Textes identiques
        text1 = "Ce texte est un exemple."
        text2 = "Ce texte est un exemple."
        similarity = self.analyzer._calculate_simple_similarity(text1, text2)
        self.assertEqual(similarity, 1.0)
        
        # Textes complètement différents
        text3 = "Ce texte est un exemple."
        text4 = "Autre chose complètement différente."
        similarity = self.analyzer._calculate_simple_similarity(text3, text4)
        self.assertLess(similarity, 0.5)
        
        # Textes partiellement similaires
        text5 = "Ce texte est un exemple."
        text6 = "Ce texte est un autre exemple."
        similarity = self.analyzer._calculate_simple_similarity(text5, text6)
        self.assertGreater(similarity, 0.5)
        self.assertLess(similarity, 1.0)

    @patch('argumentation_analysis.agents.tools.analysis.enhanced.complex_fallacy_analyzer.EnhancedComplexFallacyAnalyzer._identify_argument_structures')
    @patch('argumentation_analysis.agents.tools.analysis.enhanced.complex_fallacy_analyzer.EnhancedComplexFallacyAnalyzer._identify_argument_relations')
    @patch('argumentation_analysis.agents.tools.analysis.enhanced.complex_fallacy_analyzer.EnhancedComplexFallacyAnalyzer._evaluate_argument_coherence')
    def test_analyze_argument_structure(self, mock_evaluate_coherence, mock_identify_relations, mock_identify_structures):
        """Teste l'analyse de la structure argumentative."""
        # Configurer les mocks
        mock_identify_structures.return_value = [{"structure_type": "chaîne_causale", "confidence": 0.8}]
        mock_identify_relations.return_value = [{"relation_type": "support", "source_argument_index": 0, "target_argument_index": 1}]
        mock_evaluate_coherence.return_value = {"coherence_score": 0.7, "coherence_level": "Modéré"}
        
        # Appeler la méthode à tester
        result = self.analyzer.analyze_argument_structure(self.test_arguments, self.test_context)
        
        # Vérifier les résultats
        self.assertEqual(result["argument_count"], len(self.test_arguments))
        self.assertEqual(result["context"], self.test_context)
        self.assertIn("identified_structures", result)
        self.assertIn("argument_relations", result)
        self.assertIn("coherence_evaluation", result)
        self.assertIn("vulnerability_analysis", result)
        self.assertIn("analysis_timestamp", result)
        
        # Vérifier que les mocks ont été appelés correctement
        mock_identify_structures.assert_called()
        mock_identify_relations.assert_called_once_with(self.test_arguments)
        mock_evaluate_coherence.assert_called_once()
        
        # Vérifier que l'analyse a été ajoutée à l'historique
        self.assertEqual(len(self.analyzer.analysis_history), 1)
        self.assertEqual(self.analyzer.analysis_history[0]["type"], "structure_analysis")

    @patch('argumentation_analysis.agents.tools.analysis.enhanced.complex_fallacy_analyzer.EnhancedComplexFallacyAnalyzer.contextual_analyzer')
    @patch('argumentation_analysis.agents.tools.analysis.enhanced.complex_fallacy_analyzer.EnhancedComplexFallacyAnalyzer.identify_combined_fallacies')
    @patch('argumentation_analysis.agents.tools.analysis.enhanced.complex_fallacy_analyzer.EnhancedComplexFallacyAnalyzer._identify_advanced_fallacy_combinations')
    @patch('argumentation_analysis.agents.tools.analysis.enhanced.complex_fallacy_analyzer.EnhancedComplexFallacyAnalyzer.identify_fallacy_patterns')
    @patch('argumentation_analysis.agents.tools.analysis.enhanced.complex_fallacy_analyzer.EnhancedComplexFallacyAnalyzer._evaluate_composite_severity')
    def test_detect_composite_fallacies(
        self,
        mock_evaluate_severity,
        mock_identify_patterns,
        mock_identify_advanced,
        mock_identify_combined,
        mock_contextual_analyzer
    ):
        """Teste la détection des sophismes composés."""
        # Configurer les mocks
        mock_contextual_analyzer.identify_contextual_fallacies.return_value = [
            {"fallacy_type": "Appel à l'autorité", "confidence": 0.8}
        ]
        mock_identify_combined.return_value = [{"combination_type": "autorité_popularité", "severity": 0.7}]
        mock_identify_advanced.return_value = [{"combination_name": "cercle_autoritaire", "severity": 0.8}]
        mock_identify_patterns.return_value = [{"pattern_type": "escalation", "severity": 0.6}]
        mock_evaluate_severity.return_value = {
            "composite_severity": 0.75,
            "adjusted_severity": 0.85,
            "severity_level": "Élevé"
        }
        
        # Appeler la méthode à tester
        result = self.analyzer.detect_composite_fallacies(self.test_arguments, self.test_context)
        
        # Vérifier les résultats
        self.assertIn("individual_fallacies_count", result)
        self.assertIn("basic_combinations", result)
        self.assertIn("advanced_combinations", result)
        self.assertIn("fallacy_patterns", result)
        self.assertIn("composite_severity", result)
        self.assertIn("context", result)
        self.assertIn("analysis_timestamp", result)
        
        # Vérifier que les mocks ont été appelés correctement
        mock_contextual_analyzer.identify_contextual_fallacies.assert_called()
        mock_identify_combined.assert_called_once()
        mock_identify_advanced.assert_called_once()
        mock_identify_patterns.assert_called_once()
        mock_evaluate_severity.assert_called_once()
        
        # Vérifier que l'analyse a été ajoutée à l'historique
        self.assertEqual(len(self.analyzer.analysis_history), 1)
        self.assertEqual(self.analyzer.analysis_history[0]["type"], "composite_fallacy_detection")

    @patch('argumentation_analysis.agents.tools.analysis.enhanced.complex_fallacy_analyzer.EnhancedComplexFallacyAnalyzer.analyze_argument_structure')
    @patch('argumentation_analysis.agents.tools.analysis.enhanced.complex_fallacy_analyzer.EnhancedComplexFallacyAnalyzer._analyze_thematic_coherence')
    @patch('argumentation_analysis.agents.tools.analysis.enhanced.complex_fallacy_analyzer.EnhancedComplexFallacyAnalyzer._analyze_logical_coherence')
    @patch('argumentation_analysis.agents.tools.analysis.enhanced.complex_fallacy_analyzer.EnhancedComplexFallacyAnalyzer._detect_contradictions')
    @patch('argumentation_analysis.agents.tools.analysis.enhanced.complex_fallacy_analyzer.EnhancedComplexFallacyAnalyzer._evaluate_overall_coherence')
    def test_analyze_inter_argument_coherence(
        self,
        mock_evaluate_overall,
        mock_detect_contradictions,
        mock_analyze_logical,
        mock_analyze_thematic,
        mock_analyze_structure
    ):
        """Teste l'analyse de la cohérence inter-arguments."""
        # Configurer les mocks
        mock_analyze_structure.return_value = {
            "argument_relations": [{"relation_type": "support", "source_argument_index": 0, "target_argument_index": 1}]
        }
        mock_analyze_thematic.return_value = {"coherence_score": 0.8, "coherence_level": "Élevé"}
        mock_analyze_logical.return_value = {"coherence_score": 0.7, "coherence_level": "Modéré"}
        mock_detect_contradictions.return_value = []
        mock_evaluate_overall.return_value = {
            "overall_score": 0.75,
            "coherence_level": "Modéré",
            "recommendations": ["Recommandation 1", "Recommandation 2"]
        }
        
        # Appeler la méthode à tester
        result = self.analyzer.analyze_inter_argument_coherence(self.test_arguments, self.test_context)
        
        # Vérifier les résultats
        self.assertEqual(result["argument_count"], len(self.test_arguments))
        self.assertEqual(result["context"], self.test_context)
        self.assertIn("thematic_coherence", result)
        self.assertIn("logical_coherence", result)
        self.assertIn("contradictions", result)
        self.assertIn("overall_coherence", result)
        self.assertIn("analysis_timestamp", result)
        
        # Vérifier que les mocks ont été appelés correctement
        mock_analyze_structure.assert_called_once_with(self.test_arguments, self.test_context)
        mock_analyze_thematic.assert_called_once_with(self.test_arguments)
        mock_analyze_logical.assert_called_once()
        mock_detect_contradictions.assert_called_once_with(self.test_arguments)
        mock_evaluate_overall.assert_called_once()
        
        # Vérifier que l'analyse a été ajoutée à l'historique
        self.assertEqual(len(self.analyzer.analysis_history), 1)
        self.assertEqual(self.analyzer.analysis_history[0]["type"], "inter_argument_coherence")

    def test_circular_reasoning_detection_specific_case(self):
        """Teste la détection spécifique de raisonnement circulaire."""
        # Cas spécifique de raisonnement circulaire
        circular_arguments = [
            "La Bible est la parole de Dieu",
            "La Bible dit qu'elle est la parole de Dieu"
        ]
        
        # Appeler la méthode à tester
        result = self.analyzer.analyze_inter_argument_coherence(circular_arguments, "religieux")
        
        # Vérifier que le raisonnement circulaire est détecté
        self.assertIn("overall_coherence", result)
        self.assertLess(result["overall_coherence"]["overall_score"], 0.5)


if __name__ == '__main__':
    unittest.main()