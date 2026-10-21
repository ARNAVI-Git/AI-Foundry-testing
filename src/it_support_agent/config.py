"""
config.py
Environment-specific configuration loader for the IT Support Assistant.

Configuration is read from environment variables injected by AZD at
deployment time. Secrets must be stored in Azure Key Vault or AZD
secured environment variables — never in this file.
"""
from __future__ import annotations
import os
from dataclasses import dataclass, field


@dataclass
class AgentConfig:
    """Runtime configuration for the IT Support Assistant."""

    # Azure AI Foundry project endpoint (e.g. https://<name>.openai.azure.com/)
    foundry_project_endpoint: str

    # Name of the model deployment to use (e.g. gpt-4o)
    model_deployment_name: str

    # Azure AI Foundry agent name
    agent_name: str

    # Application Insights connection string for telemetry (optional)
    app_insights_connection_string: str = ""

    # Maximum tokens per response
    max_tokens: int = 1024

    # Response temperature (0 = deterministic)
    temperature: float = 0.0

    # API version for the Azure AI Foundry Agents SDK
    api_version: str = "2025-05-01"


def load_config() -> AgentConfig:
    """Load configuration from environment variables.

    Raises:
        EnvironmentError: If a required variable is missing.
    """
    required = {
        "FOUNDRY_PROJECT_ENDPOINT": "Azure AI Foundry project endpoint URL",
        "MODEL_DEPLOYMENT_NAME": "Model deployment name within the Foundry project",
        "AGENT_NAME": "Name of the hosted agent",
    }

    missing = [k for k in required if not os.environ.get(k)]
    if missing:
        raise EnvironmentError(
            f"Missing required environment variables: {missing}\n"
            "Set these in the AZD environment or as pipeline variable group values."
        )

    return AgentConfig(
        foundry_project_endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"].rstrip("/"),
        model_deployment_name=os.environ["MODEL_DEPLOYMENT_NAME"],
        agent_name=os.environ["AGENT_NAME"],
        app_insights_connection_string=os.environ.get(
            "APPLICATIONINSIGHTS_CONNECTION_STRING", ""
        ),
        max_tokens=int(os.environ.get("AGENT_MAX_TOKENS", "1024")),
        temperature=float(os.environ.get("AGENT_TEMPERATURE", "0.0")),
        api_version=os.environ.get("AZURE_AI_API_VERSION", "2025-05-01"),
    )
