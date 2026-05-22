from app import iniciar_aplicacion
from comun.configuracion.gestor_rutas import GestorRutas
from comun.logs import configurar_logs_basicos, obtener_logger_sicap


logger = obtener_logger_sicap("main")


if __name__ == "__main__":
    configurar_logs_basicos(GestorRutas())
    try:
        raise SystemExit(iniciar_aplicacion())
    except Exception:
        logger.exception("Error no controlado al iniciar SICAP.")
        raise