"""Ads agent: Google Ads + Meta Ads campaign performance."""

from __future__ import annotations

from typing import Any

from ai_marketing_shared.schemas import AgentRun, Confidence, Effort, Priority, Recommendation

from agents.base import BaseAgent


class AdsAgent(BaseAgent):
    name = "ads"
    description = "Finds high-CPA, low-CTR, and low-ROAS campaigns across paid channels."

    tools = ("fetch_google_ads", "fetch_meta_ads")

    def _collect(self, run: AgentRun) -> dict[str, Any]:
        return {
            "google_ads": self._call_tool(run, "fetch_google_ads").get("rows", []),
            "meta_ads": self._call_tool(run, "fetch_meta_ads").get("rows", []),
        }

    def _analyze(self, data: dict[str, Any]) -> list[Recommendation]:
        recs: list[Recommendation] = []
        for channel, rows in (("google_ads", data["google_ads"]), ("meta_ads", data["meta_ads"])):
            for row in rows:
                if str(row.get("status", "active")) != "active":
                    continue
                campaign = str(row.get("campaign", ""))
                cpa = float(row.get("cpa_usd", 0))
                target_cpa = float(row.get("target_cpa_usd", 0))
                ctr = float(row.get("ctr", 0))
                roas = float(row.get("roas", 0))

                if target_cpa and cpa > target_cpa * 1.5:
                    recs.append(
                        self._recommendation(
                            agent=self.name,
                            issue=f"High CPA on {channel} campaign '{campaign}'",
                            evidence=[
                                self._evidence(channel, "cpa_usd", cpa),
                                self._evidence(channel, "target_cpa_usd", target_cpa),
                            ],
                            proposed_action=f"Pause underperforming placements in '{campaign}' and reallocate to top performers",
                            priority=Priority.HIGH,
                            confidence=Confidence.HIGH,
                            expected_impact="Lower blended CPA toward target",
                            effort=Effort.LOW,
                            next_steps=["Review placement-level CPA", "Shift 20% budget to best ROAS campaign"],
                        )
                    )
                if ctr < 0.01:
                    recs.append(
                        self._recommendation(
                            agent=self.name,
                            issue=f"Low CTR on {channel} campaign '{campaign}'",
                            evidence=[
                                self._evidence(channel, "ctr", ctr),
                                self._evidence(channel, "impressions", float(row.get("impressions", 0))),
                            ],
                            proposed_action=f"Refresh creative and A/B test new headlines for '{campaign}'",
                            priority=Priority.MEDIUM,
                            confidence=Confidence.MEDIUM,
                            expected_impact="Increase CTR and reduce wasted impressions",
                            effort=Effort.MEDIUM,
                            next_steps=["Create 2 new ad variants", "Pause the worst 20% of ads"],
                        )
                    )
                if roas < 1.5:
                    recs.append(
                        self._recommendation(
                            agent=self.name,
                            issue=f"Low ROAS on {channel} campaign '{campaign}'",
                            evidence=[
                                self._evidence(channel, "roas", roas),
                                self._evidence(channel, "spend_usd", float(row.get("spend_usd", 0))),
                            ],
                            proposed_action=f"Tighten audience targeting and review placements for '{campaign}'",
                            priority=Priority.HIGH,
                            confidence=Confidence.HIGH,
                            expected_impact="Protect margin on paid spend",
                            effort=Effort.MEDIUM,
                            next_steps=["Remove lowest-converting audiences", "Set frequency capping"],
                        )
                    )
        return recs
