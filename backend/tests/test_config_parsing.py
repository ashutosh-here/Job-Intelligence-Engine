from app.config import Settings


def test_comma_separated_proxy_and_resource_lists_parse() -> None:
    settings = Settings(
        source_proxies="linkedin=http://proxy1:8080,indeed=http://proxy2:8080",
        source_block_resource_types="image,font,media",
    )
    assert len(settings.source_proxies) == 2
    assert settings.source_block_resource_types == ["image", "font", "media"]
