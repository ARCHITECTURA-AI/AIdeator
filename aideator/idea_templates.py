"""Built-in idea templates for new users.

Provides pre-filled idea form data for common SaaS categories
so that new users can quickly get started with validation.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class IdeaTemplate:
    """Pre-filled template for idea creation.

    Attributes:
        id: Unique template identifier
        label: Display label in the UI
        description: Pre-filled description text
        target_user: Pre-filled target user
        context: Pre-filled context
    """

    id: str
    label: str
    description: str
    target_user: str
    context: str


TEMPLATES: list[IdeaTemplate] = [
    IdeaTemplate(
        id="saas-dev-tool",
        label="SaaS Developer Tool",
        description=(
            "A developer-focused SaaS tool that streamlines a specific "
            "workflow in the software development lifecycle. It integrates "
            "with existing tools (e.g. GitHub, CI/CD, IDEs) and targets "
            "small-to-mid engineering teams seeking productivity gains."
        ),
        target_user="Software engineers and engineering leads at startups (10–100 employees)",
        context="developer-tools, B2B SaaS, bottom-up adoption, PLG",
    ),
    IdeaTemplate(
        id="infra-platform",
        label="Infra / Platform Tool",
        description=(
            "An infrastructure or platform tool that simplifies deployment, "
            "monitoring, or operations for cloud-native teams. It reduces "
            "DevOps toil and provides observability or automation for "
            "microservices, containers, or serverless workloads."
        ),
        target_user="Platform engineers, DevOps leads, and CTOs at growth-stage companies",
        context="infrastructure, cloud-native, Kubernetes, observability, IaC",
    ),
    IdeaTemplate(
        id="consumer-productivity",
        label="Consumer Productivity App",
        description=(
            "A consumer-facing productivity application that helps individuals "
            "organize tasks, manage time, or streamline personal workflows. "
            "It focuses on simplicity and daily habit integration, aiming "
            "for organic growth through word-of-mouth and community."
        ),
        target_user="Knowledge workers, freelancers, and students seeking better personal workflow",
        context="consumer, productivity, mobile-first, freemium, habit-forming",
    ),
]


def get_template(template_id: str) -> IdeaTemplate | None:
    """Get a template by its ID.

    Args:
        template_id: Template identifier

    Returns:
        IdeaTemplate or None if not found
    """
    for tpl in TEMPLATES:
        if tpl.id == template_id:
            return tpl
    return None


def list_templates() -> list[dict[str, str]]:
    """List all templates as dicts suitable for JSON/template rendering.

    Returns:
        List of template dictionaries
    """
    return [
        {
            "id": tpl.id,
            "label": tpl.label,
            "description": tpl.description,
            "target_user": tpl.target_user,
            "context": tpl.context,
        }
        for tpl in TEMPLATES
    ]
