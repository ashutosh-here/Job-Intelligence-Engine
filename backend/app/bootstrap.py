from alembic import command
from alembic.config import Config

from app.config import get_settings
from app.utils.logging import configure_logging, get_logger


configure_logging("INFO")
logger = get_logger("bootstrap")
settings = get_settings()


def bootstrap() -> None:
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", settings.database_url)
    command.upgrade(alembic_cfg, "head")
    logger.info("Database migrations complete")


if __name__ == "__main__":
    bootstrap()
