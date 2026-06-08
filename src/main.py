import logging
import webbrowser
from threading import Timer

from src.api.routes import app
from config import config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def open_browser():
    webbrowser.open("http://localhost:5500/dashboard.html")


def main():
    logger.info("=" * 70)
    logger.info("AI INCIDENT DEDUPLICATION SYSTEM - STARTING")
    logger.info("=" * 70)
    logger.info(f"OpenAI Model: {config.OPENAI_MODEL}")
    logger.info(f"Similarity Threshold: {config.SIMILARITY_THRESHOLD}")
    logger.info(f"Vector Store: {config.VECTOR_DB_PATH}")
    logger.info("=" * 70)

    Timer(2, open_browser).start()

    app.run(
        debug=True,
        host='0.0.0.0',
        port=5000
    )


if __name__ == "__main__":
    main()