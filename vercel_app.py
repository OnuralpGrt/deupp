import logging
from app import app

# Loglama ayarları
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    # Vercel için gerekli
    app = app
    logger.info("Uygulama başarıyla başlatıldı")
except Exception as e:
    logger.error(f"Uygulama başlatma hatası: {e}")
    raise 