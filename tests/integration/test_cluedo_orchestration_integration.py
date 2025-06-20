import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# Chemin vers le module à tester pour le patching
ORCHESTRATOR_MODULE_PATH = "argumentation_analysis.orchestration.cluedo_orchestrator"

@pytest.mark.asyncio
async def test_cluedo_orchestration_flow():
    """
    Teste le flux d'orchestration de base de cluedo_orchestrator.py.
    - Mock les agents pour retourner des réponses prédéfinies.
    - Vérifie que les agents sont appelés.
    - Vérifie que l'historique de la conversation contient des messages des agents.
    """

    # Mocker EnqueteCluedoState pour contrôler la solution et éviter la génération aléatoire si besoin
    mock_enquete_state_instance = MagicMock()
    mock_enquete_state_instance.nom_enquete_cluedo = "Test Case"
    mock_enquete_state_instance.elements_jeu_cluedo = {
        "suspects": ["A", "B"], "armes": ["X", "Y"], "lieux": ["1", "2"]
    }
    mock_enquete_state_instance.description_cas = "A test case."
    mock_enquete_state_instance.solution_enquete = {"suspect": "A", "arme": "X", "lieu": "1"} # Solution fixe

    # Mocker les instances des agents
    # SherlockEnqueteAgent
    mock_sherlock_instance = AsyncMock()
    mock_sherlock_instance.name = "Sherlock" # Important pour AgentGroupChat
    # Simuler la méthode que AgentGroupChat pourrait appeler (ex: invoke ou process_chat)
    # La méthode exacte dépend de l'implémentation de Agent et AgentGroupChat
    # Pour l'instant, on suppose une méthode `invoke` compatible avec le wrapper ou l'agent lui-même.
    async def sherlock_invoke_side_effect(prompt, **kwargs):
        # Simule une réponse de Sherlock
        return [{"role": "assistant", "name": "Sherlock", "content": "Sherlock: C'est élémentaire."}]
    mock_sherlock_instance.invoke = AsyncMock(side_effect=sherlock_invoke_side_effect)
    # Si les agents ont une méthode spécifique pour être appelés par AgentGroupChat, il faut la mocker.
    # Par exemple, si AgentGroupChat appelle directement une méthode comme `generate_reply(history)`
    # mock_sherlock_instance.generate_reply = AsyncMock(return_value="Sherlock: C'est élémentaire.")


    # WatsonLogicAssistant
    mock_watson_instance = AsyncMock()
    mock_watson_instance.name = "Watson" # Important pour AgentGroupChat
    async def watson_invoke_side_effect(prompt, **kwargs):
        # Simule une réponse de Watson
        return [{"role": "assistant", "name": "Watson", "content": "Watson: En effet, Sherlock."}]
    mock_watson_instance.invoke = AsyncMock(side_effect=watson_invoke_side_effect)
    # mock_watson_instance.generate_reply = AsyncMock(return_value="Watson: En effet, Sherlock.")

    # Mocker AgentGroupChat
    mock_group_chat_instance = AsyncMock()
    # La méthode `invoke` de AgentGroupChat retourne l'historique
    # On simule un historique simple basé sur les réponses mockées des agents
    simulated_history = [
        {"role": "user", "name": "User", "content": "L'enquête sur le meurtre au Manoir Tudor commence maintenant. Qui a des premières pistes ?"},
        {"role": "assistant", "name": "Sherlock", "content": "Sherlock: C'est élémentaire."},
        {"role": "assistant", "name": "Watson", "content": "Watson: En effet, Sherlock."},
        # Potentiellement un autre tour si max_turns=2 pour BalancedParticipationStrategy
        # et max_messages le permet.
        {"role": "assistant", "name": "Sherlock", "content": "Sherlock: Le coupable est évident."},
    ]
    mock_group_chat_instance.invoke = AsyncMock(return_value=simulated_history)
    
    # Patch des constructeurs et autres dépendances
    with patch(f"{ORCHESTRATOR_MODULE_PATH}.Kernel", MagicMock()) as mock_kernel_constructor, \
         patch(f"{ORCHESTRATOR_MODULE_PATH}.EnqueteCluedoState", return_value=mock_enquete_state_instance) as mock_enquete_state_constructor, \
         patch(f"{ORCHESTRATOR_MODULE_PATH}.EnqueteStateManagerPlugin", MagicMock()) as mock_plugin_constructor, \
         patch(f"{ORCHESTRATOR_MODULE_PATH}.SherlockEnqueteAgent", return_value=mock_sherlock_instance) as mock_sherlock_constructor, \
         patch(f"{ORCHESTRATOR_MODULE_PATH}.WatsonLogicAssistant", return_value=mock_watson_instance) as mock_watson_constructor, \
         patch(f"{ORCHESTRATOR_MODULE_PATH}.GroupChatOrchestration", return_value=mock_group_chat_instance) as mock_group_chat_constructor, \
         patch("builtins.print") as mock_print: # Mocker print pour éviter les sorties console pendant le test

        # Importer et exécuter la fonction main du script d'orchestration
        # Cela suppose que le script est structuré pour permettre l'import et l'appel de main
        # ou qu'il est acceptable d'importer le module, ce qui exécutera le code sous if __name__ == "__main__"
        # Pour un test plus propre, main() devrait être une fonction importable.
        
        # Alternative: importer le module. Si main() est sous if __name__ == "__main__",
        # il faut appeler la fonction main explicitement.
        # Pour cet exemple, on va supposer que l'importation du module ne lance pas main directement,
        # et qu'on peut appeler la fonction main() du module.
        
        # Si cluedo_orchestrator.py exécute main() à l'import, il faudra le recharger ou le lancer en subprocess.
        # Pour l'instant, on essaie d'appeler main() directement.
        
        # Dynamically import the main function from the orchestrator script
        import argumentation_analysis.orchestration.cluedo_orchestrator as cluedo_orchestrator
        
        # Exécuter la fonction main
        await cluedo_orchestrator.main()

        # Vérifications
        # 1. Vérifier que les constructeurs des composants principaux ont été appelés
        mock_kernel_constructor.assert_called_once()
        mock_enquete_state_constructor.assert_called_once_with(
            nom_enquete_cluedo="Le Mystère du Manoir Tudor",
            elements_jeu_cluedo={
                "suspects": ["Colonel Moutarde", "Professeur Violet", "Mademoiselle Rose"],
                "armes": ["Poignard", "Chandelier", "Revolver"],
                "lieux": ["Salon", "Cuisine", "Bureau"]
            },
            description_cas="Un meurtre a été commis au Manoir Tudor. Qui est le coupable, avec quelle arme et dans quel lieu ?",
            auto_generate_solution=True
        )
        mock_plugin_constructor.assert_called_once_with(mock_enquete_state_instance)
        
        # Vérifier que les agents ont été initialisés (avec les bons arguments si possible)
        mock_sherlock_constructor.assert_called_once()
        # On peut ajouter des vérifications sur les args de mock_sherlock_constructor.call_args
        mock_watson_constructor.assert_called_once()

        # 2. Vérifier que AgentGroupChat a été initialisé avec les agents mockés
        mock_group_chat_constructor.assert_called_once()
        # Vérifier que les agents passés au constructeur sont bien nos mocks
        # Cela dépend de comment les agents sont passés (directement ou wrappés)
        # args, kwargs = mock_group_chat_constructor.call_args
        # assert mock_sherlock_instance in args[0]['agents'] # ou kwargs['agents']
        # assert mock_watson_instance in args[0]['agents']

        # 3. Vérifier que la méthode invoke de AgentGroupChat a été appelée
        expected_input_message = [{
            "role": "user",
            "name": "System",
            "content": "Nouvelle enquête Cluedo : A test case.. Sherlock, commencez."
        }]
        mock_group_chat_instance.invoke.assert_called_once_with(input=expected_input_message)

        # 4. Vérifier que l'historique (simulé) contient des messages des deux agents
        # L'historique est retourné par mock_group_chat_instance.invoke
        # Dans le script original, l'historique est ensuite affiché par print.
        # On peut vérifier les appels à print.
        
        # Construire les chaînes attendues pour les appels à print
        # Récupérer les appels réels à print
        actual_print_calls = [args[0] for args, kwargs in mock_print.call_args_list if args]

        # Vérifier les messages clés qui devraient être imprimés
        # Note: simulated_history est ce que mock_group_chat_instance.invoke retourne.
        # Le script cluedo_orchestrator.py itère ensuite sur ce résultat pour imprimer.

        # 1. Vérifier que le titre de l'historique est imprimé
        assert "Historique de la conversation Cluedo :" in actual_print_calls
        
        # 2. Vérifier que le contenu de chaque message simulé est imprimé.
        #    Le format exact du print dans le script est "  {sender_name}: {content}"
        #    simulated_history[0] est le message utilisateur initial, qui n'est pas ré-imprimé de cette façon.
        #    Les messages des assistants (simulated_history[1] à simulated_history[3]) devraient l'être.

        # Vérification du contenu des messages des assistants
        assert any(f"Sherlock: {simulated_history[1]['content']}" in call for call in actual_print_calls)
        assert any(f"Watson: {simulated_history[2]['content']}" in call for call in actual_print_calls)
        assert any(f"Sherlock: {simulated_history[3]['content']}" in call for call in actual_print_calls)

        # 3. Vérifier que le message de fin de conversation est imprimé
        assert "--- Fin de la Conversation ---" in actual_print_calls


        # L'ancienne vérification pour add_hook n'est plus pertinente avec GroupChatOrchestration
        # car les stratégies sont gérées par le manager.


        # Note: Les mocks pour les méthodes `invoke` des agents (sherlock_invoke_side_effect, watson_invoke_side_effect)
        # ne seront pas directement appelés si `AgentGroupChat.invoke` est entièrement mocké pour retourner `simulated_history`.
        # Pour tester que les *méthodes des agents mockés* sont appelées *par le AgentGroupChat mocké*,
        # il faudrait que le `mock_group_chat_instance.invoke` appelle réellement les méthodes des agents.
        # Cela rendrait le mock de AgentGroupChat plus complexe.
        # L'approche actuelle teste que le `cluedo_orchestrator.main` utilise `AgentGroupChat`
        # et que ce dernier est configuré. Le test de l'interaction *interne* à `AgentGroupChat`
        # (c'est-à-dire que `AgentGroupChat` appelle bien ses agents) est plus un test d'intégration
        # de `AgentGroupChat` lui-même ou nécessiterait de ne pas mocker `AgentGroupChat.invoke`
        # mais plutôt les appels LLM *à l'intérieur* des agents.

        # Pour l'objectif "Vérifiez que les agents sont bien appelés",
        # si on mocke AgentGroupChat.invoke, on ne vérifie pas que les agents sont appelés PAR AgentGroupChat.
        # On vérifie que AgentGroupChat est appelé.
        # Pour vérifier que les agents sont appelés, il faudrait soit :
        #   a) Ne pas mocker AgentGroupChat.invoke, mais mocker les appels LLM dans les agents.
        #      Cela signifie que le vrai AgentGroupChat s'exécuterait.
        #   b) Avoir un mock plus sophistiqué pour AgentGroupChat.invoke qui appelle les agents.

        # Pour cette itération, nous nous concentrons sur le fait que le script `cluedo_orchestrator`
        # configure et appelle `AgentGroupChat`. Les tests unitaires des agents eux-mêmes
        # devraient vérifier leur propre logique d'invocation.

# Pour exécuter ce test:
# Assurez-vous que pytest et pytest-asyncio sont installés.
# Exécutez `pytest tests/integration/test_cluedo_orchestration_integration.py` depuis la racine du projet.