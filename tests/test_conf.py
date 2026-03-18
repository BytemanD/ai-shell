from ai_shell.common.conf import CONF, ProviderConfig


def test_conf_get_used_provider():
    assert CONF.get_used_provider() == CONF.providers[0]


def test_conf_get_providers():
    assert CONF.get_providers() == [provider.name for provider in CONF.providers]


def test_conf_add_provider():
    CONF.add_provider(
        ProviderConfig(
            name="test",
            base_url="https://xxxxxx",
            api_key="",
            timeout=10,
            enable_thinking=False,
        )
    )
    assert "test" in CONF.get_providers()
