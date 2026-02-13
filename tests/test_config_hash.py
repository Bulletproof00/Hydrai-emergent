from packages.core.config_hash import compute_config_hash


def test_config_hash_stable() -> None:
    a = {"x": 1, "y": [1, 2, 3]}
    b = {"y": [1, 2, 3], "x": 1}
    assert compute_config_hash(a) == compute_config_hash(b)
