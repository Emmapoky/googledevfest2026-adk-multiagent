"""The team: the specialist agents the orchestrator can call.

Every agent in SPECIALISTS becomes a tool for the orchestrator. Exercise 3: add yours.
"""

# me: Lines starting with "# me:" are my own notes. Claude helped write them at DevFest KL 2026.

from devfest_agents.agents import finance_agent, news_agent, trading_agent

# me: Bring in my marketing agent module from this same folder.
from . import marketing_agent

# me: Every agent on this list turns into a function the orchestrator can call, so adding mine
# me: here is what lets marketing questions reach it.
SPECIALISTS = [finance_agent, trading_agent, news_agent, marketing_agent]
