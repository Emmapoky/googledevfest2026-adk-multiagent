"""marketing_agent: answers questions about ad campaigns.

The marketing queries are in marketing_queries.py. You turn them into tools,
give the tools to an agent, and plug the agent into the orchestrator.
The exercises in exercises/ walk you through it.
"""

# me: Lines starting with "# me:" are my own notes on what each bit does.
# me: Claude helped me write this file and these notes at DevFest KL 2026.

from __future__ import annotations

from typing import Any

from google.adk.agents import LlmAgent

from . import marketing_queries as queries
from devfest_agents.agents.common import GENERATION, static_instruction  # noqa: F401 - build() uses them (exercise 2)

NAME = "marketing_agent"
LABEL = "Marketing agent"
DATASOURCE = "marketing"

# Exercise 2: the pitch other agents read when deciding whether to send this agent work.
# me: The orchestrator reads this to decide if a question is a marketing one, so it says what I own
# me: (campaigns, ad channels, spend, clicks, campaign sign ups) and what I don't (ledger and all clients).
DESCRIPTION = (
    "Ad campaign analyst for Nimbus Markets. Answers questions about marketing campaigns and ad "
    "channels: campaign spend, impressions, clicks, click through rate, the new clients (sign-ups) "
    "each campaign brought in, and cost per sign-up, by campaign, channel, entity or month, "
    "including the Nimbus Go launch campaigns. It does not know booked ledger expenses or the total "
    "number of new clients across the business."
)


# Exercise 1: write two tools here, one per campaign and one per ad channel.

# me: Tool 1. The model never sees the body, only the name, the type hints and the docstring,
# me: so the docstring says what comes back, when to pick this tool and how to fill each argument.
async def campaign_performance(start_date: str, end_date: str, entity_id: str | None = None) -> dict:
    """How each ad campaign did over a date range: spend, reach and the new clients it brought in.

    One row per campaign that spent money or brought in a sign-up in the range: campaign_id, name,
    entity_id, channel, spend_usd, impressions, clicks, signups (new clients from that campaign)
    and cost_per_signup_usd, biggest spender first. Use it for questions about a particular
    campaign, the best or worst campaign, or "which campaign brought in the most new clients?".
    Use campaign_list first if you only know part of a campaign's name.

    Args:
        start_date: First day, YYYY-MM-DD.
        end_date: Last day (inclusive), YYYY-MM-DD.
        entity_id: Only this entity: NM-UK, NM-SG, NM-AE or NM-INTL. Omit for all.
    """
    # me: Pass the same three values straight to the tested query and hand its rows back.
    return await queries.fetch_campaign_performance(start_date, end_date, entity_id)


# me: Tool 2. Same pattern, but grouped by ad channel instead of by campaign.
async def channel_summary(start_date: str, end_date: str, entity_id: str | None = None) -> dict:
    """How each ad channel did over a date range, with all its campaigns added together.

    One row per channel ("search ads", "social ads", "video ads", "app-store ads",
    "affiliate network"): spend_usd, impressions, clicks, click_through_pct, signups and
    cost_per_signup_usd, biggest spender first. Use it to compare channels, for example
    "which channel had the cheapest sign-ups?" or "what was the click through rate on social ads?".

    Args:
        start_date: First day, YYYY-MM-DD.
        end_date: Last day (inclusive), YYYY-MM-DD.
        entity_id: Only this entity: NM-UK, NM-SG, NM-AE or NM-INTL. Omit for all.
    """
    # me: Call the channel query with the range and entity, and return its rows as they are.
    return await queries.fetch_channel_summary(start_date, end_date, entity_id)


# me: Extra tool for the competition. It wraps the one query the exercises leave unused, so the
# me: agent can say honestly when a date range falls outside the data instead of reporting zeros.
async def data_coverage() -> dict:
    """The first and last dates that have any campaign spend or sign-up data.

    One row: first_spend_date, last_spend_date, first_signup_date and last_signup_date. Use it
    when a question asks about dates that might be outside the data, or when another tool
    returns no rows, to tell "nothing happened" apart from "no data recorded".
    """
    # me: No arguments needed, it just reads the min and max dates.
    return await queries.fetch_data_coverage()


# ---------------------------------------------------------------------------
# Ready-made tools. They wrap the other queries the same way yours do,
# so you don't have to type them out. Give them to your agent in exercise 2.
# ---------------------------------------------------------------------------
async def monthly_spend(start_date: str, end_date: str, entity_id: str | None = None,
                        channel: str | None = None) -> dict:
    """Campaign spend, impressions, clicks and sign-ups per calendar month.

    One row per month that had spend: month (first day of the month), spend_usd, impressions,
    clicks, signups and cost_per_signup_usd. Use it for trends and month-by-month questions,
    such as "what did NM-SG spend each month this year?".

    Args:
        start_date: First day, YYYY-MM-DD.
        end_date: Last day (inclusive), YYYY-MM-DD.
        entity_id: Only this entity: NM-UK, NM-SG, NM-AE or NM-INTL. Omit for all.
        channel: Only this channel: "search ads", "social ads", "video ads", "app-store ads" or
            "affiliate network". Omit for all.
    """
    return await queries.fetch_monthly_spend(start_date, end_date, entity_id, channel)


async def entity_summary(start_date: str, end_date: str) -> dict:
    """Campaign spend, clicks and sign-ups per entity for a date range.

    One row per entity that ran campaigns: entity_id, spend_usd, clicks, signups and
    cost_per_signup_usd, biggest spender first. Use it for "which entity spent the most?".

    Args:
        start_date: First day, YYYY-MM-DD.
        end_date: Last day (inclusive), YYYY-MM-DD.
    """
    return await queries.fetch_entity_summary(start_date, end_date)


async def campaign_list(entity_id: str | None = None, name_contains: str | None = None) -> dict:
    """The campaigns themselves, with no figures: who ran them, on which channel, and when.

    One row per campaign: campaign_id, name, entity_id, channel, start_date and end_date (the
    planned dates). Use it to find campaigns by name, for example name_contains="Nimbus Go".

    Args:
        entity_id: Only this entity: NM-UK, NM-SG, NM-AE or NM-INTL. Omit for all.
        name_contains: Part of the campaign name, any case. Omit for all campaigns.
    """
    return await queries.fetch_campaigns(entity_id, name_contains)


READY_MADE_TOOLS = [monthly_spend, entity_summary, campaign_list]


# Exercise 2: build the agent. Every specialist has this same build(services, model) signature,
# so the team can build them all the same way. Finance and trading use `services` to reach the
# tool registry in the database; your agent doesn't need it.
def build(services: Any, model: Any) -> LlmAgent:
    # me: An agent is a model plus a job description. This builds mine and hands it to the team.
    return LlmAgent(
        # me: The name other agents use to call me, "marketing_agent".
        name=NAME,
        # me: Whichever model the app was started with (Gemini 3.7 Flash here).
        model=model,
        # me: The outward pitch the orchestrator reads, written above.
        description=DESCRIPTION,
        # me: The inward rules, loaded from prompts/marketing_agent.md.
        instruction=static_instruction(NAME),
        # me: My three tools first, then the three ready made ones.
        tools=[campaign_performance, channel_summary, data_coverage, *READY_MADE_TOOLS],
        # me: Low temperature, so the same question gets the same answer each run.
        generate_content_config=GENERATION,
    )
