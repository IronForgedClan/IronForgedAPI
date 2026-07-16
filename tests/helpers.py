from unittest.mock import AsyncMock

from sqlalchemy.ext.asyncio import AsyncSession


def create_mock_db_session() -> AsyncMock:
    """Build a mock AsyncSession with the correct sync/async method split.

    AsyncMock(spec=AsyncSession) makes sync session methods (add, merge,
    expire, ...) return sync MagicMock, and async methods (commit,
    execute, flush, refresh, delete, rollback, ...) return AsyncMock.
    Use this anywhere a test needs to mock a database session.
    """
    return AsyncMock(spec=AsyncSession)


def setup_database_service_mocks(
    mock_db, mock_service_factory, mock_service_instance=None
):
    """Sets up common database and service mocking pattern used across many tests.

    Args:
        mock_db: Mock of the database module
        mock_service_factory: Mock of the service factory function
        mock_service_instance: Optional mock service instance to return
    """
    mock_session = create_mock_db_session()

    mock_context_manager = AsyncMock()
    mock_context_manager.__aenter__.return_value = mock_session
    mock_context_manager.__aexit__.return_value = None
    mock_db.get_session.return_value = mock_context_manager

    if mock_service_instance is None:
        mock_service_instance = AsyncMock()

    mock_service_factory.return_value = mock_service_instance

    return mock_session, mock_service_instance
