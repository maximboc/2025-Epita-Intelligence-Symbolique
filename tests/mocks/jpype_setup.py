import sys
import os
import pytest
from unittest.mock import MagicMock
import importlib.util
from argumentation_analysis.core.jvm_setup import shutdown_jvm_if_needed
import logging

# --- Configuration du Logger ---
logger = logging.getLogger(__name__)
# Configuration basique si le logger n'est pas déjà configuré par pytest ou autre
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO) # Ou logging.DEBUG pour plus de détails
    logger.propagate = False

# --- Détermination de la disponibilité du vrai JPype via variable d'environnement ---
# Cette variable est utilisée par les décorateurs skipif dans les fichiers de test.
logger.info(f"jpype_setup.py: Évaluation de _REAL_JPYPE_AVAILABLE...")
logger.info(f"jpype_setup.py: Valeur brute de os.environ.get('USE_REAL_JPYPE', 'false'): '{os.environ.get('USE_REAL_JPYPE', 'false')}'")
_REAL_JPYPE_AVAILABLE = os.environ.get('USE_REAL_JPYPE', 'false').lower() in ('true', '1')
logger.info(f"jpype_setup.py: _REAL_JPYPE_AVAILABLE évalué à: {_REAL_JPYPE_AVAILABLE}")
# Les prints de débogage précédents ont confirmé que _REAL_JPYPE_AVAILABLE est correctement évalué.
# La cause du skip était une erreur dans la fixture integration_jvm (chemin des libs).


# --- Sauvegarde du module JPype potentiellement pré-importé ou import frais ---
_REAL_JPYPE_MODULE = None
_PRE_EXISTING_JPYPE_IN_SYS_MODULES = sys.modules.get('jpype')

if _PRE_EXISTING_JPYPE_IN_SYS_MODULES:
    _REAL_JPYPE_MODULE = _PRE_EXISTING_JPYPE_IN_SYS_MODULES
    logger.info(f"jpype_setup.py: _REAL_JPYPE_MODULE initialisé à partir de _PRE_EXISTING_JPYPE_IN_SYS_MODULES (ID: {id(_REAL_JPYPE_MODULE)}).")
else:
    logger.info("jpype_setup.py: JPype non préchargé, tentative d'import frais.")
    try:
        import jpype as r_jpype_fresh_import
        _REAL_JPYPE_MODULE = r_jpype_fresh_import
        logger.info(f"jpype_setup.py: Vrai module JPype importé fraîchement (ID: {id(_REAL_JPYPE_MODULE)}).")
    except ImportError as e_fresh_import:
        logger.warning(f"jpype_setup.py: Le vrai module JPype n'a pas pu être importé fraîchement: {e_fresh_import}")
        _REAL_JPYPE_MODULE = None
    except NameError as e_name_error_fresh_import:
        logger.error(f"jpype_setup.py: NameError lors de l'import frais de JPype: {e_name_error_fresh_import}.")
        _REAL_JPYPE_MODULE = None

if _REAL_JPYPE_MODULE is None:
    logger.error("jpype_setup.py: _REAL_JPYPE_MODULE EST NONE après la tentative d'initialisation.")
else:
    logger.info(f"jpype_setup.py: _REAL_JPYPE_MODULE est initialisé (ID: {id(_REAL_JPYPE_MODULE)}) avant la définition des fixtures.")

# --- Mock JPype ---
try:
    from tests.mocks import jpype_mock # Importer le module via son chemin de package
    # Importer le vrai module mock d'imports depuis le sous-package jpype_components
    from tests.mocks.jpype_components.imports import imports_module as actual_mock_jpype_imports_module

    jpype_module_mock_obj = MagicMock(name="jpype_module_mock")
    jpype_module_mock_obj.__path__ = []
    jpype_module_mock_obj.isJVMStarted = jpype_mock.isJVMStarted
    jpype_module_mock_obj.startJVM = jpype_mock.startJVM
    jpype_module_mock_obj.getJVMPath = jpype_mock.getJVMPath
    jpype_module_mock_obj.getJVMVersion = jpype_mock.getJVMVersion
    jpype_module_mock_obj.getDefaultJVMPath = jpype_mock.getDefaultJVMPath
    jpype_module_mock_obj.JClass = jpype_mock.JClass
    jpype_module_mock_obj.JException = jpype_mock.JException
    jpype_module_mock_obj.JObject = jpype_mock.JObject
    jpype_module_mock_obj.JVMNotFoundException = jpype_mock.JVMNotFoundException
    jpype_module_mock_obj.__version__ = '1.4.1.mock' # ou jpype_mock.__version__ si défini
    jpype_module_mock_obj.imports = actual_mock_jpype_imports_module
    _JPYPE_MODULE_MOCK_OBJ_GLOBAL = jpype_module_mock_obj
    _MOCK_DOT_JPYPE_MODULE_GLOBAL = jpype_mock._jpype # Accéder à _jpype depuis le module jpype_mock importé
    logger.info("jpype_setup.py: Mock JPype préparé.")
except ImportError as e_jpype:
    logger.error(f"jpype_setup.py: ERREUR CRITIQUE lors de l'import de jpype_mock ou ses composants: {e_jpype}. Utilisation de mocks de fallback pour JPype.")
    _fb_jpype_mock = MagicMock(name="jpype_fallback_mock")
    _fb_jpype_mock.imports = MagicMock(name="jpype.imports_fallback_mock")
    _fb_dot_jpype_mock = MagicMock(name="_jpype_fallback_mock")

    _JPYPE_MODULE_MOCK_OBJ_GLOBAL = _fb_jpype_mock
    _MOCK_DOT_JPYPE_MODULE_GLOBAL = _fb_dot_jpype_mock
    logger.info("jpype_setup.py: Mock JPype de FALLBACK préparé et assigné aux variables globales de mock.")


@pytest.fixture(scope="function", autouse=True)
def activate_jpype_mock_if_needed(request):
    global _JPYPE_MODULE_MOCK_OBJ_GLOBAL, _MOCK_DOT_JPYPE_MODULE_GLOBAL, _REAL_JPYPE_MODULE

    # Déterminer si le vrai JPype doit être utilisé
    env_use_real_jpype = os.environ.get('USE_REAL_JPYPE', 'false').lower() in ('true', '1')
    
    use_real_jpype_marker = False
    if request.node.get_closest_marker("real_jpype"):
        use_real_jpype_marker = True
        
    use_real_jpype_path = False
    path_str = str(request.node.fspath).replace(os.sep, '/')
    if 'tests/integration/' in path_str or 'tests/minimal_jpype_tweety_tests/' in path_str:
        use_real_jpype_path = True
        
    final_use_real_jpype = False
    if env_use_real_jpype:
        final_use_real_jpype = True
        logger.info(f"Test {request.node.name}: REAL JPype forcé par la variable d'environnement USE_REAL_JPYPE.")
    elif use_real_jpype_marker:
        final_use_real_jpype = True
        logger.info(f"Test {request.node.name}: REAL JPype demandé par le marqueur 'real_jpype'.")
    elif use_real_jpype_path:
        final_use_real_jpype = True
        logger.info(f"Test {request.node.name}: REAL JPype activé par chemin ({path_str}).")
    # else: final_use_real_jpype reste False

    if final_use_real_jpype:
        logger.info(f"Test {request.node.name} demande REAL JPype. Configuration de sys.modules pour utiliser le vrai JPype.")
        if _REAL_JPYPE_MODULE:
            sys.modules['jpype'] = _REAL_JPYPE_MODULE
            if hasattr(_REAL_JPYPE_MODULE, '_jpype'):
                sys.modules['_jpype'] = _REAL_JPYPE_MODULE._jpype
            elif '_jpype' in sys.modules and sys.modules.get('_jpype') is not getattr(_REAL_JPYPE_MODULE, '_jpype', None) :
                del sys.modules['_jpype']
            if hasattr(_REAL_JPYPE_MODULE, 'imports'):
                sys.modules['jpype.imports'] = _REAL_JPYPE_MODULE.imports
            elif 'jpype.imports' in sys.modules and sys.modules.get('jpype.imports') is not getattr(_REAL_JPYPE_MODULE, 'imports', None):
                del sys.modules['jpype.imports']
            logger.debug(f"REAL JPype (ID: {id(_REAL_JPYPE_MODULE)}) est maintenant sys.modules['jpype'].")
        else:
            logger.error(f"Test {request.node.name} demande REAL JPype, mais _REAL_JPYPE_MODULE n'est pas disponible. Test échouera probablement.")
        yield
    else:
        logger.info(f"Test {request.node.name} utilise MOCK JPype.")
        try:
            jpype_components_jvm_module = sys.modules.get('tests.mocks.jpype_components.jvm')
            if jpype_components_jvm_module:
                if hasattr(jpype_components_jvm_module, '_jvm_started'):
                    jpype_components_jvm_module._jvm_started = False
                if hasattr(jpype_components_jvm_module, '_jvm_path'):
                    jpype_components_jvm_module._jvm_path = None
                if hasattr(_JPYPE_MODULE_MOCK_OBJ_GLOBAL, 'config') and hasattr(_JPYPE_MODULE_MOCK_OBJ_GLOBAL.config, 'jvm_path'):
                    _JPYPE_MODULE_MOCK_OBJ_GLOBAL.config.jvm_path = None
                logger.info("État (_jvm_started, _jvm_path, config.jvm_path) du mock JPype réinitialisé pour le test.")
            else:
                logger.warning("Impossible de réinitialiser l'état du mock JPype: module 'tests.mocks.jpype_components.jvm' non trouvé.")
        except Exception as e_reset_mock:
            logger.error(f"Erreur lors de la réinitialisation de l'état du mock JPype: {e_reset_mock}")

        original_modules = {}
        modules_to_handle = ['jpype', '_jpype', 'jpype._core', 'jpype.imports', 'jpype.types', 'jpype.config', 'jpype.JProxy']

        if 'jpype.imports' in sys.modules and \
           hasattr(sys.modules['jpype.imports'], '_jpype') and \
           _MOCK_DOT_JPYPE_MODULE_GLOBAL is not None and \
           hasattr(_MOCK_DOT_JPYPE_MODULE_GLOBAL, 'isStarted'):
            if sys.modules['jpype.imports']._jpype is not _MOCK_DOT_JPYPE_MODULE_GLOBAL:
                if 'jpype.imports._jpype_original' not in original_modules:
                     original_modules['jpype.imports._jpype_original'] = sys.modules['jpype.imports']._jpype
                logger.debug(f"Patch direct de sys.modules['jpype.imports']._jpype avec notre mock _jpype.")
                sys.modules['jpype.imports']._jpype = _MOCK_DOT_JPYPE_MODULE_GLOBAL
            else:
                logger.debug("sys.modules['jpype.imports']._jpype est déjà notre mock.")

        for module_name in modules_to_handle:
            if module_name in sys.modules:
                is_current_module_our_mock = False
                if module_name == 'jpype' and sys.modules[module_name] is _JPYPE_MODULE_MOCK_OBJ_GLOBAL: is_current_module_our_mock = True
                elif module_name in ['_jpype', 'jpype._core'] and sys.modules[module_name] is _MOCK_DOT_JPYPE_MODULE_GLOBAL: is_current_module_our_mock = True
                elif module_name == 'jpype.imports' and hasattr(_JPYPE_MODULE_MOCK_OBJ_GLOBAL, 'imports') and sys.modules[module_name] is _JPYPE_MODULE_MOCK_OBJ_GLOBAL.imports: is_current_module_our_mock = True
                elif module_name == 'jpype.config' and hasattr(_JPYPE_MODULE_MOCK_OBJ_GLOBAL, 'config') and sys.modules[module_name] is _JPYPE_MODULE_MOCK_OBJ_GLOBAL.config: is_current_module_our_mock = True

                if not is_current_module_our_mock and module_name not in original_modules:
                    original_modules[module_name] = sys.modules.pop(module_name)
                    logger.debug(f"Supprimé et sauvegardé sys.modules['{module_name}']")
                elif module_name in sys.modules and is_current_module_our_mock:
                    del sys.modules[module_name]
                    logger.debug(f"Supprimé notre mock préexistant pour sys.modules['{module_name}'].")
                elif module_name in sys.modules:
                    del sys.modules[module_name]
                    logger.debug(f"Supprimé sys.modules['{module_name}'] (sauvegarde prioritaire existante).")

        sys.modules['jpype'] = _JPYPE_MODULE_MOCK_OBJ_GLOBAL
        sys.modules['_jpype'] = _MOCK_DOT_JPYPE_MODULE_GLOBAL
        sys.modules['jpype._core'] = _MOCK_DOT_JPYPE_MODULE_GLOBAL
        if hasattr(_JPYPE_MODULE_MOCK_OBJ_GLOBAL, 'imports'):
            sys.modules['jpype.imports'] = _JPYPE_MODULE_MOCK_OBJ_GLOBAL.imports
        else:
            sys.modules['jpype.imports'] = MagicMock(name="jpype.imports_fallback_in_fixture")

        if hasattr(_JPYPE_MODULE_MOCK_OBJ_GLOBAL, 'config'):
            sys.modules['jpype.config'] = _JPYPE_MODULE_MOCK_OBJ_GLOBAL.config
        else:
            sys.modules['jpype.config'] = MagicMock(name="jpype.config_fallback_in_fixture")

        mock_types_module = MagicMock(name="jpype.types_mock_module_dynamic_in_fixture")
        for type_name in ["JString", "JArray", "JObject", "JBoolean", "JInt", "JDouble", "JLong", "JFloat", "JShort", "JByte", "JChar"]:
            if hasattr(_JPYPE_MODULE_MOCK_OBJ_GLOBAL, type_name):
                setattr(mock_types_module, type_name, getattr(_JPYPE_MODULE_MOCK_OBJ_GLOBAL, type_name))
            else:
                setattr(mock_types_module, type_name, MagicMock(name=f"Mock{type_name}_in_fixture"))
        sys.modules['jpype.types'] = mock_types_module

        sys.modules['jpype.JProxy'] = MagicMock(name="jpype.JProxy_mock_module_dynamic_in_fixture")
        logger.debug(f"Mocks JPype (principal, _jpype/_core, imports, config, types, JProxy) mis en place.")
        yield
        logger.debug(f"Nettoyage après test {request.node.name} (utilisation du mock).")

        if 'jpype.imports._jpype_original' in original_modules:
            if 'jpype.imports' in sys.modules and hasattr(sys.modules['jpype.imports'], '_jpype'):
                sys.modules['jpype.imports']._jpype = original_modules['jpype.imports._jpype_original']
                logger.debug("Restauré jpype.imports._jpype à sa valeur originale.")
            del original_modules['jpype.imports._jpype_original']

        modules_we_set_up_in_fixture = ['jpype', '_jpype', 'jpype._core', 'jpype.imports', 'jpype.config', 'jpype.types', 'jpype.JProxy']
        for module_name in modules_we_set_up_in_fixture:
            current_module_in_sys = sys.modules.get(module_name)
            is_our_specific_mock_from_fixture = False
            if module_name == 'jpype' and current_module_in_sys is _JPYPE_MODULE_MOCK_OBJ_GLOBAL: is_our_specific_mock_from_fixture = True
            elif module_name in ['_jpype', 'jpype._core'] and current_module_in_sys is _MOCK_DOT_JPYPE_MODULE_GLOBAL: is_our_specific_mock_from_fixture = True
            elif module_name == 'jpype.imports' and hasattr(_JPYPE_MODULE_MOCK_OBJ_GLOBAL, 'imports') and current_module_in_sys is _JPYPE_MODULE_MOCK_OBJ_GLOBAL.imports: is_our_specific_mock_from_fixture = True
            elif module_name == 'jpype.config' and hasattr(_JPYPE_MODULE_MOCK_OBJ_GLOBAL, 'config') and current_module_in_sys is _JPYPE_MODULE_MOCK_OBJ_GLOBAL.config: is_our_specific_mock_from_fixture = True
            elif module_name == 'jpype.types' and current_module_in_sys is mock_types_module: is_our_specific_mock_from_fixture = True
            elif module_name == 'jpype.JProxy' and isinstance(current_module_in_sys, MagicMock) and hasattr(current_module_in_sys, 'name') and "jpype.JProxy_mock_module_dynamic_in_fixture" in current_module_in_sys.name : is_our_specific_mock_from_fixture = True

            if is_our_specific_mock_from_fixture:
                if module_name in sys.modules:
                    del sys.modules[module_name]
                    logger.debug(f"Supprimé notre mock pour sys.modules['{module_name}']")

        for module_name, original_module in original_modules.items():
            sys.modules[module_name] = original_module
            logger.debug(f"Restauré sys.modules['{module_name}'] à {original_module}")

        logger.info(f"État de JPype restauré après test {request.node.name} (utilisation du mock).")

def pytest_sessionstart(session):
    global _REAL_JPYPE_MODULE, _JPYPE_MODULE_MOCK_OBJ_GLOBAL, logger
    logger.info("jpype_setup.py: pytest_sessionstart hook triggered.")
    if not hasattr(logger, 'info'):
        import logging
        logger = logging.getLogger(__name__)

    if _REAL_JPYPE_MODULE and _REAL_JPYPE_MODULE is not _JPYPE_MODULE_MOCK_OBJ_GLOBAL:
        logger.info("   pytest_sessionstart: Real JPype module is available.")
        # try:
            # La logique de configuration de destroy_jvm et l'import de jpype.config
            # sont maintenant gérés de manière centralisée par initialize_jvm lors du premier démarrage réel.
            # Commenter cette section pour éviter les conflits ou les configurations prématurées.
            # original_sys_jpype_module = sys.modules.get('jpype')
            # if sys.modules.get('jpype') is not _REAL_JPYPE_MODULE:
            #     sys.modules['jpype'] = _REAL_JPYPE_MODULE
            #     logger.info("   pytest_sessionstart: Temporarily set sys.modules['jpype'] to _REAL_JPYPE_MODULE for config import.")

            # if not hasattr(_REAL_JPYPE_MODULE, 'config') or _REAL_JPYPE_MODULE.config is None:
            #     logger.info("   pytest_sessionstart: Attempting to import jpype.config explicitly.")
            #     import jpype.config # This might be problematic if called before JVM start or with wrong classpath context
            
            # if original_sys_jpype_module is not None and sys.modules.get('jpype') is not original_sys_jpype_module:
            #     sys.modules['jpype'] = original_sys_jpype_module
            #     logger.info("   pytest_sessionstart: Restored original sys.modules['jpype'].")
            # elif original_sys_jpype_module is None and 'jpype' in sys.modules and sys.modules['jpype'] is _REAL_JPYPE_MODULE:
            #     pass # It was correctly set
            
            # Tentative d'assurer que jpype.config est le vrai config, si possible.
            # initialize_jvm s'occupera de mettre destroy_jvm à False.
            # Bloc try/except correctement indenté :
        try:
            if not hasattr(_REAL_JPYPE_MODULE, 'config') or _REAL_JPYPE_MODULE.config is None:
                logger.info("   pytest_sessionstart: _REAL_JPYPE_MODULE.config non trouvé, tentative d'import de jpype.config.")
                _current_sys_jpype = sys.modules.get('jpype')
                sys.modules['jpype'] = _REAL_JPYPE_MODULE
                import jpype.config
                sys.modules['jpype'] = _current_sys_jpype
                logger.info(f"   pytest_sessionstart: Import de jpype.config tenté. hasattr(config): {hasattr(_REAL_JPYPE_MODULE, 'config')}")

            if hasattr(_REAL_JPYPE_MODULE, 'config') and _REAL_JPYPE_MODULE.config is not None:
                if 'jpype.config' not in sys.modules or sys.modules.get('jpype.config') is not _REAL_JPYPE_MODULE.config:
                    sys.modules['jpype.config'] = _REAL_JPYPE_MODULE.config
                    logger.info("   pytest_sessionstart: Assuré que sys.modules['jpype.config'] est _REAL_JPYPE_MODULE.config.")
            else:
                logger.warning("   pytest_sessionstart: _REAL_JPYPE_MODULE.config toujours non disponible après tentative d'import.")

        except ImportError as e_cfg_imp_sess_start:
            logger.error(f"   pytest_sessionstart: ImportError lors de la tentative d'import de jpype.config: {e_cfg_imp_sess_start}")
        except Exception as e_sess_start_cfg:
            logger.error(f"   pytest_sessionstart: Erreur inattendue lors de la manipulation de jpype.config: {e_sess_start_cfg}", exc_info=True)

        logger.info("   pytest_sessionstart: La configuration de jpype.config.destroy_jvm est gérée par initialize_jvm.")
    elif _JPYPE_MODULE_MOCK_OBJ_GLOBAL and _REAL_JPYPE_MODULE is _JPYPE_MODULE_MOCK_OBJ_GLOBAL:
        logger.info("   pytest_sessionstart: JPype module is the MOCK. No changes to destroy_jvm needed for the mock.")
    else:
        logger.info("   pytest_sessionstart: Real JPype module not definitively available or identified as mock. La configuration de jpype.config est gérée par initialize_jvm.")

def pytest_sessionfinish(session, exitstatus):
    global _REAL_JPYPE_MODULE, _JPYPE_MODULE_MOCK_OBJ_GLOBAL, logger
    logger.info(f"jpype_setup.py: pytest_sessionfinish hook triggered. Exit status: {exitstatus}")

    # Déterminer si le vrai JPype a été utilisé pour la session ou le dernier test
    # Cela est une heuristique. Idéalement, on saurait si la JVM a été démarrée par notre code.
    real_jpype_was_potentially_used = False
    if _REAL_JPYPE_MODULE and sys.modules.get('jpype') is _REAL_JPYPE_MODULE:
        logger.info("   pytest_sessionfinish: sys.modules['jpype'] IS _REAL_JPYPE_MODULE. Le vrai JPype a potentiellement été utilisé.")
        real_jpype_was_potentially_used = True
    elif _REAL_JPYPE_MODULE and _REAL_JPYPE_MODULE is not _JPYPE_MODULE_MOCK_OBJ_GLOBAL:
        logger.info("   pytest_sessionfinish: _REAL_JPYPE_MODULE est disponible et n'est pas le mock global. Le vrai JPype a potentiellement été utilisé.")
        real_jpype_was_potentially_used = True
    else:
        logger.info("   pytest_sessionfinish: sys.modules['jpype'] n'est pas _REAL_JPYPE_MODULE ou _REAL_JPYPE_MODULE est le mock. Le mock JPype a probablement été utilisé.")

    if real_jpype_was_potentially_used:
        logger.info("   pytest_sessionfinish: Tentative d'arrêt de la JVM via shutdown_jvm_if_needed() car le vrai JPype a potentiellement été utilisé.")
        try:
            # S'assurer que le vrai jpype est dans sys.modules pour que shutdown_jvm_if_needed fonctionne correctement
            original_jpype_in_sys = sys.modules.get('jpype')
            if original_jpype_in_sys is not _REAL_JPYPE_MODULE and _REAL_JPYPE_MODULE is not None:
                logger.info(f"   pytest_sessionfinish: Temporairement, sys.modules['jpype'] = _REAL_JPYPE_MODULE (ID: {id(_REAL_JPYPE_MODULE)}) pour shutdown.")
                sys.modules['jpype'] = _REAL_JPYPE_MODULE
            
            shutdown_jvm_if_needed() # Appel de notre fonction centralisée
            
            # Restaurer l'état précédent de sys.modules['jpype'] si modifié
            if original_jpype_in_sys is not None and sys.modules.get('jpype') is not original_jpype_in_sys:
                logger.info(f"   pytest_sessionfinish: Restauration de sys.modules['jpype'] à son état original (ID: {id(original_jpype_in_sys)}).")
                sys.modules['jpype'] = original_jpype_in_sys
            elif original_jpype_in_sys is None and 'jpype' in sys.modules: # Si on l'a ajouté et qu'il n'y était pas
                del sys.modules['jpype']
                logger.info("   pytest_sessionfinish: sys.modules['jpype'] supprimé car il n'était pas là initialement.")

        except Exception as e_shutdown:
            logger.error(f"   pytest_sessionfinish: Erreur lors de l'appel à shutdown_jvm_if_needed(): {e_shutdown}", exc_info=True)
        
        # La logique ci-dessous pour restaurer sys.modules['jpype'] et sys.modules['jpype.config']
        # est importante si la JVM n'est PAS arrêtée par JPype via atexit (destroy_jvm=False).
        # Si shutdown_jvm_if_needed() a bien arrêté la JVM, cette partie est moins critique mais ne fait pas de mal.
        logger.info("   pytest_sessionfinish: Vérification de l'état de la JVM après tentative d'arrêt.")
        try:
            jvm_still_started_after_shutdown_attempt = False
            if _REAL_JPYPE_MODULE and hasattr(_REAL_JPYPE_MODULE, 'isJVMStarted'):
                 # Assurer que _REAL_JPYPE_MODULE est utilisé pour la vérification
                _current_jpype_for_check = sys.modules.get('jpype')
                if _current_jpype_for_check is not _REAL_JPYPE_MODULE and _REAL_JPYPE_MODULE is not None:
                    sys.modules['jpype'] = _REAL_JPYPE_MODULE
                jvm_still_started_after_shutdown_attempt = _REAL_JPYPE_MODULE.isJVMStarted()
                if _current_jpype_for_check is not None and _current_jpype_for_check is not _REAL_JPYPE_MODULE: # restaurer
                    sys.modules['jpype'] = _current_jpype_for_check
                elif _current_jpype_for_check is None and 'jpype' in sys.modules and sys.modules['jpype'] is _REAL_JPYPE_MODULE:
                    del sys.modules['jpype']


            logger.info(f"   pytest_sessionfinish: JVM encore démarrée après tentative d'arrêt: {jvm_still_started_after_shutdown_attempt}")

            destroy_jvm_is_false = False # Valeur par défaut si config non accessible
            if _REAL_JPYPE_MODULE and hasattr(_REAL_JPYPE_MODULE, 'config') and _REAL_JPYPE_MODULE.config is not None and hasattr(_REAL_JPYPE_MODULE.config, 'destroy_jvm'):
                destroy_jvm_is_false = not _REAL_JPYPE_MODULE.config.destroy_jvm
            logger.info(f"   pytest_sessionfinish: destroy_jvm est False (selon config): {destroy_jvm_is_false}")

            if jvm_still_started_after_shutdown_attempt and destroy_jvm_is_false:
                logger.info("   pytest_sessionfinish: JVM est toujours active et destroy_jvm est False. Assurer la présence des modules jpype pour atexit.")
                current_sys_jpype = sys.modules.get('jpype')
                if current_sys_jpype is not _REAL_JPYPE_MODULE and _REAL_JPYPE_MODULE is not None:
                    logger.warning(f"   pytest_sessionfinish: sys.modules['jpype'] (ID: {id(current_sys_jpype)}) n'est pas _REAL_JPYPE_MODULE (ID: {id(_REAL_JPYPE_MODULE)}). Restauration de _REAL_JPYPE_MODULE.")
                    sys.modules['jpype'] = _REAL_JPYPE_MODULE
                
                if _REAL_JPYPE_MODULE and hasattr(_REAL_JPYPE_MODULE, 'config') and _REAL_JPYPE_MODULE.config is not None:
                    current_sys_jpype_config = sys.modules.get('jpype.config')
                    if current_sys_jpype_config is not _REAL_JPYPE_MODULE.config:
                        logger.warning(f"   pytest_sessionfinish: sys.modules['jpype.config'] (ID: {id(current_sys_jpype_config)}) n'est pas _REAL_JPYPE_MODULE.config (ID: {id(_REAL_JPYPE_MODULE.config)}). Restauration.")
                        sys.modules['jpype.config'] = _REAL_JPYPE_MODULE.config
                else:
                    logger.warning("   pytest_sessionfinish: _REAL_JPYPE_MODULE.config non disponible, ne peut pas assurer sys.modules['jpype.config'].")
            else:
                logger.info("   pytest_sessionfinish: JVM non démarrée ou destroy_jvm est True. Pas de gestion spéciale de sys.modules pour atexit depuis ici.")
        except AttributeError as ae:
             logger.error(f"   pytest_sessionfinish: AttributeError (vérification post-arrêt): {ae}.", exc_info=True)
        except Exception as e:
            logger.error(f"   pytest_sessionfinish: Erreur inattendue (vérification post-arrêt): {type(e).__name__}: {e}", exc_info=True)
    else:
        logger.info("   pytest_sessionfinish: Le mock JPype a probablement été utilisé. Aucun arrêt de JVM nécessaire depuis ici.")