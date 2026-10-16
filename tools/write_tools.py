"""Write-type tools: never executed without an explicit approval.

These tools exist to demonstrate the least-privilege permission system. In
demo mode the context only allows READ, so calling them returns a permission
denied result. Even in production, they should be gated behind the approval
queue and an explicit ``allowed_permission=WRITE`` context.
"""

from __future__ import annotations

from typing import Any

from ai_marketing_shared.tools import BaseTool, PermissionLevel, ToolResult


class ExecuteCampaignChangeTool(BaseTool):
    """Apply a campaign change (pause, budget shift, bid update).

    Deliberately a no-op in this repo: real execution would target an external
    ads API and MUST only happen after approval. The tool records the intended
    change so audits are possible.
    """

    name = "execute_campaign_change"
    description = "Apply a campaign change after human approval (pause / budget shift / bid update)."
    permission = PermissionLevel.WRITE
    max_arguments = 4

    def _run(self, **arguments: Any) -> ToolResult:
        campaign = arguments.get("campaign", "unknown")
        change = arguments.get("change", "noop")
        return ToolResult(
            summary=f"Recorded approved campaign change '{change}' for '{campaign}' (dry run)",
            data={"campaign": campaign, "change": change, "applied": False},
        )
