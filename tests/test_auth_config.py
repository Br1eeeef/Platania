from api.app.core.config import Settings


def test_development_auth_bypass_is_ignored_in_production() -> None:
    settings = Settings(
        PLATANIA_ENV="production",
        PLATANIA_DEV_AUTH_BYPASS=True,
        SUPABASE_URL="https://example.supabase.co",
        SUPABASE_SECRET_KEY="server-secret",
    )
    assert settings.supabase_enabled is True
    assert settings.demo_auth_enabled is False
