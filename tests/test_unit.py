"""
tests/test_unit.py
Unit tests for the IT Support Assistant.

These tests validate file structure, configuration logic, and prompt
content WITHOUT requiring a live Azure AI Foundry connection or model.
Run with: pytest tests/test_unit.py -v
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest

# ---------------------------------------------------------------
# Path constants
# ---------------------------------------------------------------
REPO_ROOT = Path(__file__).parents[1]
PROMPT_FILE = REPO_ROOT / "src" / "it_support_agent" / "prompts" / "system.md"
EVAL_DATASET = REPO_ROOT / "evals" / "test_cases.json"
CONFIG_DIR = REPO_ROOT / "config"


# ---------------------------------------------------------------
# Prompt file tests
# ---------------------------------------------------------------

class TestPromptFile:
    """Validate that the system prompt exists and meets content requirements."""

    def test_prompt_file_exists(self):
        assert PROMPT_FILE.exists(), f"System prompt not found at: {PROMPT_FILE}"

    def test_prompt_file_is_not_empty(self):
        content = PROMPT_FILE.read_text(encoding="utf-8")
        assert len(content.strip()) > 50, "System prompt appears to be empty or too short"

    def test_prompt_contains_safety_rule_no_invent(self):
        content = PROMPT_FILE.read_text(encoding="utf-8").lower()
        assert "do not invent" in content, "Safety rule 'do not invent' is missing"

    def test_prompt_contains_safety_rule_passwords(self):
        content = PROMPT_FILE.read_text(encoding="utf-8").lower()
        assert "passwords" in content, "Safety rule about passwords is missing"

    def test_prompt_contains_safety_rule_override(self):
        content = PROMPT_FILE.read_text(encoding="utf-8").lower()
        assert "do not follow instructions" in content, (
            "Safety rule 'do not follow instructions' (override guard) is missing"
        )

    def test_prompt_contains_no_credentials(self):
        """Prompt must not contain any hardcoded credentials."""
        content = PROMPT_FILE.read_text(encoding="utf-8").lower()
        forbidden_patterns = ["api_key", "secret", "password:", "token:", "bearer "]
        for pattern in forbidden_patterns:
            assert pattern not in content, (
                f"Possible credential found in system prompt: '{pattern}'"
            )


# ---------------------------------------------------------------
# Evaluation dataset tests
# ---------------------------------------------------------------

class TestEvaluationDataset:
    """Validate the evaluation dataset structure and required test cases."""

    def test_dataset_exists(self):
        assert EVAL_DATASET.exists(), f"Evaluation dataset not found at: {EVAL_DATASET}"

    def test_dataset_is_valid_json(self):
        content = EVAL_DATASET.read_text(encoding="utf-8")
        data = json.loads(content)
        assert isinstance(data, list), "Evaluation dataset must be a JSON array"

    def test_dataset_has_minimum_cases(self):
        data = json.loads(EVAL_DATASET.read_text(encoding="utf-8"))
        assert len(data) >= 4, f"Dataset must have at least 4 test cases, found {len(data)}"

    def test_all_cases_have_required_fields(self):
        required = {"id", "category", "input", "expected_behavior", "critical"}
        data = json.loads(EVAL_DATASET.read_text(encoding="utf-8"))
        for case in data:
            missing = required - set(case.keys())
            assert not missing, f"Test case {case.get('id', '?')} missing fields: {missing}"

    def test_all_case_ids_are_unique(self):
        data = json.loads(EVAL_DATASET.read_text(encoding="utf-8"))
        ids = [c["id"] for c in data]
        assert len(ids) == len(set(ids)), "Duplicate test case IDs found in dataset"

    def test_critical_security_cases_present(self):
        """Ensure the four mandatory safety categories are covered."""
        data = json.loads(EVAL_DATASET.read_text(encoding="utf-8"))
        categories = {c["category"] for c in data if c.get("critical")}
        required_categories = {"security", "prompt-injection", "grounding"}
        missing = required_categories - categories
        assert not missing, f"Missing critical categories in dataset: {missing}"

    def test_all_inputs_are_non_empty(self):
        data = json.loads(EVAL_DATASET.read_text(encoding="utf-8"))
        for case in data:
            assert case["input"].strip(), f"Test case {case['id']} has empty input"


# ---------------------------------------------------------------
# Configuration tests
# ---------------------------------------------------------------

class TestConfiguration:
    """Validate environment config files and config loader logic."""

    def test_config_dir_exists(self):
        assert CONFIG_DIR.exists(), "config/ directory is missing"

    @pytest.mark.parametrize("env", ["dev", "test", "prod"])
    def test_config_file_exists(self, env: str):
        config_file = CONFIG_DIR / f"{env}.json"
        assert config_file.exists(), f"config/{env}.json is missing"

    @pytest.mark.parametrize("env", ["dev", "test", "prod"])
    def test_config_file_is_valid_json(self, env: str):
        config_file = CONFIG_DIR / f"{env}.json"
        data = json.loads(config_file.read_text(encoding="utf-8"))
        assert isinstance(data, dict), f"config/{env}.json must be a JSON object"

    @pytest.mark.parametrize("env", ["dev", "test", "prod"])
    def test_config_has_required_keys(self, env: str):
        config_file = CONFIG_DIR / f"{env}.json"
        data = json.loads(config_file.read_text(encoding="utf-8"))
        required_keys = {"environment", "foundry_project_endpoint", "model_deployment_name"}
        missing = required_keys - set(data.keys())
        assert not missing, f"config/{env}.json missing keys: {missing}"

    @pytest.mark.parametrize("env", ["dev", "test", "prod"])
    def test_config_contains_no_secrets(self, env: str):
        """Config files must not contain credentials."""
        content = (CONFIG_DIR / f"{env}.json").read_text(encoding="utf-8").lower()
        forbidden = ["api_key", "secret", "password", "token", "bearer"]
        for f in forbidden:
            assert f not in content, (
                f"Possible credential '{f}' found in config/{env}.json — use Key Vault instead"
            )

    def test_load_config_raises_on_missing_env(self):
        """Config loader must raise EnvironmentError when variables are absent."""
        from src.it_support_agent.config import load_config

        clean_env = {
            k: v for k, v in os.environ.items()
            if k not in {"FOUNDRY_PROJECT_ENDPOINT", "MODEL_DEPLOYMENT_NAME", "AGENT_NAME"}
        }
        with patch.dict(os.environ, clean_env, clear=True):
            with pytest.raises(EnvironmentError):
                load_config()

    def test_load_config_succeeds_with_all_vars(self):
        """Config loader returns correct values when all variables are present."""
        from src.it_support_agent.config import load_config

        env_overrides = {
            "FOUNDRY_PROJECT_ENDPOINT": "https://test.openai.azure.com/",
            "MODEL_DEPLOYMENT_NAME": "gpt-4o",
            "AGENT_NAME": "it-support-assistant",
        }
        with patch.dict(os.environ, env_overrides, clear=False):
            config = load_config()
        assert config.foundry_project_endpoint == "https://test.openai.azure.com"
        assert config.model_deployment_name == "gpt-4o"
        assert config.agent_name == "it-support-assistant"


# ---------------------------------------------------------------
# Repository structure tests
# ---------------------------------------------------------------

class TestRepositoryStructure:
    """Validate that all required files and directories exist."""

    @pytest.mark.parametrize("path", [
        "azure.yaml",
        "azure-pipelines.yml",
        "infra-pipeline.yml",
        "requirements.txt",
        "requirements-dev.txt",
        "pyproject.toml",
        "infra/main.bicep",
        "infra/dev.bicepparam",
        "infra/test.bicepparam",
        "infra/prod.bicepparam",
        "src/it_support_agent/agent.py",
        "src/it_support_agent/main.py",
        "src/it_support_agent/config.py",
        "src/it_support_agent/prompts/system.md",
        "evals/test_cases.json",
        "config/dev.json",
        "config/test.json",
        "config/prod.json",
    ])
    def test_required_file_exists(self, path: str):
        target = REPO_ROOT / path
        assert target.exists(), f"Required file missing: {path}"
