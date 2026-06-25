import pytest
import yaml
from guardian.policy.loader import load_policy_file
from guardian.policy.models import PolicyConfig, RuleConfig


def test_load_valid_yaml():
    config = load_policy_file("tests/fixtures/guardian-policy-valid.yml")
    assert isinstance(config, PolicyConfig)
    assert config.version == 1
    assert config.mode == "advisory"
    assert config.detection == "marker"
    assert len(config.rules) == 3


def test_load_valid_yaml_rule_fields():
    config = load_policy_file("tests/fixtures/guardian-policy-valid.yml")
    rule_names = [r.name for r in config.rules]
    assert "hallucinated-api" in rule_names
    assert "missing-error-handling" in rule_names
    assert "hardcoded-secrets" in rule_names

    hallucinated = next(r for r in config.rules if r.name == "hallucinated-api")
    assert hallucinated.severity == "critical"
    assert hallucinated.enabled is True


def test_missing_file_returns_default():
    config = load_policy_file("tests/fixtures/nonexistent-policy.yml")
    assert config.version == 1
    assert config.mode == "advisory"
    assert len(config.rules) == 3
    assert config.rules[0].name == "hallucinated-api"


def test_invalid_yaml_syntax():
    with open("/tmp/invalid_syntax.yml", "w") as f:
        f.write("version: 1\n  invalid_indent: true\n")
    with pytest.raises(ValueError, match="YAML parse error"):
        load_policy_file("/tmp/invalid_syntax.yml")


def test_bad_severity_raises_error():
    with pytest.raises(ValueError, match="severity"):
        load_policy_file("tests/fixtures/guardian-policy-invalid.yml")


def test_duplicate_rule_names_raises_error():
    with pytest.raises(ValueError):
        load_policy_file("tests/fixtures/guardian-policy-invalid.yml")


def test_duplicate_rule_names_only():
    import yaml
    from guardian.policy.models import PolicyConfig
    data = yaml.safe_load(open("tests/fixtures/guardian-policy-valid.yml"))
    data["rules"].append(data["rules"][0])
    with pytest.raises(ValueError, match="Duplicate"):
        PolicyConfig(**data)


def test_non_dict_yaml():
    with open("/tmp/not_a_dict.yml", "w") as f:
        f.write(yaml.dump(["just", "a", "list"]))
    with pytest.raises(ValueError, match="Expected a YAML mapping"):
        load_policy_file("/tmp/not_a_dict.yml")


def test_default_policy_is_deep_copy():
    config1 = load_policy_file("tests/fixtures/nonexistent-policy.yml")
    config2 = load_policy_file("tests/fixtures/nonexistent-policy.yml")
    assert config1 is not config2
    assert config1.rules[0] is not config2.rules[0]
