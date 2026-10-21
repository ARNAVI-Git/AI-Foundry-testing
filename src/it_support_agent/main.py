"""
main.py
Entry point for local development and testing of the IT Support Assistant.

This module is NOT the hosted-agent entry point — Azure AI Foundry manages
the hosted agent lifecycle directly. Use this for:
  - Local interactive testing before committing
  - Debugging agent responses during development
  - Running against a dev Foundry project from your workstation

Usage:
    export FOUNDRY_PROJECT_ENDPOINT=https://<project>.openai.azure.com/
    export MODEL_DEPLOYMENT_NAME=gpt-4o
    export AGENT_NAME=it-support-assistant
    python -m src.it_support_agent.main
"""
from __future__ import annotations

import logging
import sys

from .agent import create_client, get_or_create_agent, send_message
from .config import load_config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> None:
    """Run the IT Support Assistant in interactive mode."""
    print("\n" + "=" * 60)
    print("  IT Support Assistant — Local Development Mode")
    print("  Type 'exit' or press Ctrl+C to quit.")
    print("=" * 60 + "\n")

    config = load_config()
    logger.info("Loaded configuration for agent: %s", config.agent_name)

    client = create_client(config)
    agent = get_or_create_agent(client, config)
    logger.info("Agent ready: %s", agent.name)

    print(f"Connected to: {config.foundry_project_endpoint}")
    print(f"Agent: {agent.name}  |  Model: {config.model_deployment_name}\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            sys.exit(0)

        if not user_input:
            continue
        if user_input.lower() in {"exit", "quit", "q"}:
            print("Goodbye.")
            sys.exit(0)

        try:
            response = send_message(client, agent, user_input, config)
            print(f"\nAssistant: {response}\n")
        except RuntimeError as exc:
            logger.error("Agent error: %s", exc)
            print(f"\n[Error] {exc}\n")


if __name__ == "__main__":
    main()
