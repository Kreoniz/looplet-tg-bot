from looplet.utils.cooldowns import CooldownManager


def test_cooldown_hit_returns_remaining_time() -> None:
    cooldowns = CooldownManager(default_seconds=10)

    assert cooldowns.hit("weather", now=100.0) is None
    assert cooldowns.hit("weather", now=104.0) == 6.0
    assert cooldowns.hit("weather", now=111.0) is None

