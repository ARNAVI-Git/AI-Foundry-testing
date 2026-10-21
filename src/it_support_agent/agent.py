"""
agent.py
Azure AI Foundry hosted agent definition — IT Support Assistant.

This module creates or retrieves the hosted agent using the Azure AI
Projects SDK. The agent is configured with a system prompt, the approved
model deployment, and optional tool definitions.

The hosted agent lifecycle (create, version, activate) is managed by
`azd deploy` as part of the CI/CD pipeline, not by this module directly.
This module is used for local testing and evaluation only.
"""
from __future__ import annotations

import logging
from pathlib import Path

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import Agent
from azure.identity import DefaultAzureCredential

from .config import AgentConfig

logger = logging.getLogger(__name__)

# Path to the system prompt (version-controlled alongside code)
_PROMPTS_DIR = Path(__file__).parent / "prompts"
_SYSTEM_PROMPT_PATH = _PROMPTS_DIR / "system.md"


def load_system_prompt() -> str:
    """Read the system prompt from the version-controlled file.

    Returns:
        The full text of the system prompt.

    Raises:
        FileNotFoundError: If the system prompt file does not exist.
    """
    if not _SYSTEM_PROMPT_PATH.exists():
        raise FileNotFoundError(
            f"System prompt not found at: {_SYSTEM_PROMPT_PATH}\n"
            "Ensure prompts/system.md is committed to the repository."
        )
    return _SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")


def create_client(config: AgentConfig) -> AIProjectClient:
    """Create an authenticated Azure AI Projects client.

    Uses DefaultAzureCredential which supports:
      - Managed Identity (in Azure / hosted agent runtime)
      - Workload Identity Federation (in Azure DevOps)
      - Azure CLI credentials (for local development)
      - Environment credentials (AZURE_CLIENT_ID / AZURE_CLIENT_SECRET)

    Args:
        config: Loaded agent configuration.

    Returns:
        Authenticated AIProjectClient.
    """
    credential = DefaultAzureCredential()
    client = AIProjectClient(
        endpoint=config.foundry_project_endpoint,
        credential=credential,
        api_version=config.api_version,
    )
    logger.info("Azure AI Projects client created for: %s", config.foundry_project_endpoint)
    return client


def get_or_create_agent(client: AIProjectClient, config: AgentConfig) -> Agent:
    """Retrieve the named agent if it exists, otherwise create it.

    This function is intended for local testing. In CI/CD, the agent is
    created and versioned by `azd deploy` using the azure.yaml service
    definition.

    Args:
        client: Authenticated AIProjectClient.
        config: Loaded agent configuration.

    Returns:
        The existing or newly created Agent object.
    """
    system_prompt = load_system_prompt()

    # Search for an existing agent with the same name
    existing_agents = client.agents.list_agents()
    for agent in existing_agents.data:
        if agent.name == config.agent_name:
            logger.info("Found existing agent: %s (id=%s)", agent.name, agent.id)
            return agent

    # Create a new agent
    logger.info("Creating new agent: %s", config.agent_name)
    agent = client.agents.create_agent(
        model=config.model_deployment_name,
        name=config.agent_name,
        instructions=system_prompt,
    )
    logger.info("Agent created: %s (id=%s)", agent.name, agent.id)
    return agent


def send_message(
    client: AIProjectClient,
    agent: Agent,
    user_message: str,
    config: AgentConfig,
) -> str:
    """Send a message to the agent and return the response text.

    Creates a new thread for each invocation (stateless).

    Args:
        client: Authenticated AIProjectClient.
        agent: The agent to invoke.
        user_message: The user's input message.
        config: Loaded agent configuration.

    Returns:
        The agent's text response.

    Raises:
        RuntimeError: If the agent run fails or returns no text content.
    """
    thread = client.agents.create_thread()
    client.agents.create_message(
        thread_id=thread.id,
        role="user",
        content=user_message,
    )

    run = client.agents.create_and_process_run(
        thread_id=thread.id,
        agent_id=agent.id,
    )

    if run.status != "completed":
        raise RuntimeError(
            f"Agent run failed with status '{run.status}'. "
            f"Run ID: {run.id}. Check Foundry diagnostics for details."
        )

    messages = client.agents.list_messages(thread_id=thread.id)

    # The last assistant message is the response
    for msg in reversed(messages.data):
        if msg.role == "assistant":
            for content_block in msg.content:
                if hasattr(content_block, "text") and content_block.text:
                    return content_block.text.value

    raise RuntimeError(
        f"Agent run completed (id={run.id}) but returned no text content."
    )
