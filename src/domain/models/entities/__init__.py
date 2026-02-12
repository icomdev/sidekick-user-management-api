# Import all ORM models here so Base.metadata registers them before create_all.
# Add new models to this list as they are created.
from src.domain.models.entities.user import User

__all__ = ["User"]
