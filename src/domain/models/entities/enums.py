from enum import Enum


class GroupRole(Enum):
    """Roles a user can hold within a group."""

    ADMIN = "admin"
    USER = "user"
