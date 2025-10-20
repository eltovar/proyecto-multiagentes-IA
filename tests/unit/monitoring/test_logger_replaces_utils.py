'''
Test para verificar que motoring/logger.py pueda remplzar 
completamenteerror_logger
garantizando migracion
'''

import pytest
import logging


class TestMonitoringLoggerFeatures:
    """Verificar que monitoring/logger tiene todas las funcionalidades necesarias"""

    def test_get_logger_returns_standard_logger(self):
        """Verificar que get_logger retorna logger estándar de Python"""
        from app.monitoring.logger import get_logger
        
        logger = get_logger("test")
        
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test"

    def test_logger_has_all_required_methods(self):
        """Verificar que logger tiene todos los métodos necesarios"""
        from app.monitoring.logger import get_logger
        
        logger = get_logger("test")
        
        # Métodos que reemplazan log_error y log_info
        assert hasattr(logger, 'error')
        assert hasattr(logger, 'info')
        
        # Métodos adicionales del estándar
        assert hasattr(logger, 'warning')
        assert hasattr(logger, 'debug')
        assert hasattr(logger, 'critical')
        assert hasattr(logger, 'exception')

    def test_logger_error_accepts_exc_info(self):
        """Verificar que logger.error acepta exc_info (reemplazo de exception param)"""
        from app.monitoring.logger import get_logger
        
        logger = get_logger("test")
        
        try:
            # Intentar logger.error con exc_info
            raise ValueError("Test exception")
        except ValueError as e:
            # No debe lanzar error
            logger.error("Test error message", exc_info=e)
            logger.error("Test with True", exc_info=True)  # También válido

    def test_logger_supports_extra_context(self):
        """Verificar que logger soporta extra (reemplazo de context param)"""
        from app.monitoring.logger import get_logger
        
        logger = get_logger("test")
        
        # No debe lanzar error
        logger.info("Test message", extra={"key": "value", "user_id": "123"})


class TestErrorLoggerNoLongerExists:
    """Verificar que error_logger ya NO está disponible"""

    def test_error_logger_module_does_not_exist(self):
        """Verificar que app.utils.error_logger NO se puede importar"""
        with pytest.raises(ModuleNotFoundError):
            from app.utils.error_logger import log_error

    def test_utils_package_does_not_exist(self):
        """Verificar que app.utils NO existe como package"""
        with pytest.raises(ModuleNotFoundError):
            import app.utils
            
    def test_no_error_logger_references_in_services(self):
        """Verificar que ningún archivo en services/ importa error_logger"""
        import subprocess
        
        result = subprocess.run(
            ["grep", "-r", "from app.utils.error_logger import", "app/services/"],
            capture_output=True,
            text=True
        )
        
        # returncode != 0 significa que NO encontró coincidencias (✅ correcto)
        assert result.returncode != 0, \
            f"Aún existen imports de error_logger en services/: {result.stdout}"


class TestMigratedServicesUseMonitoring:
    """Verificar que servicios migrados usan monitoring/logger correctamente"""

    def test_whatsapp_service_uses_monitoring_logger(self):
        """Verificar que whatsapp_service usa monitoring/logger"""
        import inspect
        from app.services import whatsapp_service
        
        source = inspect.getsource(whatsapp_service)
        
        assert "from app.monitoring.logger import get_logger" in source
        assert "from app.utils.error_logger" not in source
        assert "logger = get_logger(__name__)" in source

    def test_llm_service_uses_monitoring_logger(self):
        """Verificar que llm_service usa monitoring/logger"""
        import inspect
        from app.services import llm_service
        
        source = inspect.getsource(llm_service)
        
        assert "from app.monitoring.logger import get_logger" in source
        assert "from app.utils.error_logger" not in source

    def test_llm_generator_uses_monitoring_logger(self):
        """Verificar que llm_generator usa monitoring/logger"""
        import inspect
        from app.services import llm_generator
        
        source = inspect.getsource(llm_generator)
        
        assert "from app.monitoring.logger import get_logger" in source
        assert "from app.utils.error_logger" not in source

    def test_llm_classifier_uses_monitoring_logger(self):
        """Verificar que llm_classifier usa monitoring/logger"""
        import inspect
        from app.services import llm_classifier
        
        source = inspect.getsource(llm_classifier)
        
        assert "from app.monitoring.logger import get_logger" in source
        assert "from app.utils.error_logger" not in source

    def test_leadsales_client_uses_monitoring_logger(self):
        """Verificar que leadsales_client usa monitoring/logger"""
        import inspect
        from app.services import leadsales_client
        
        source = inspect.getsource(leadsales_client)
        
        assert "from app.monitoring.logger import get_logger" in source
        assert "from app.utils.error_logger" not in source