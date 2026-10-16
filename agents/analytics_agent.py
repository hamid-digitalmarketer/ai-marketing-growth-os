"""Analytics agent: session, conversion, bounce, and search-position trends."""

from __future__ import annotations

from statistics import mean
from typing import Any

from ai_marketing_shared.schemas import AgentRun, Confidence, Effort, Priority, Recommendation

from agents.base import BaseAgent


class AnalyticsAgent(BaseAgent):
    name = "analytics"
    description = "Finds conversion declines, high bounce, mobile issues, and ranking opportunities."

    tools = ("fetch_ga_sessions", "fetch_gsc_keywords")

    def _collect(self, run: AgentRun) -> dict[str, Any]:
        return {
            "ga": self._call_tool(run, "fetch_ga_sessions").get("rows", []),
            "gsc": self._call_tool(run, "fetch_gsc_keywords").get("rows", []),
        }

    def _analyze(self, data: dict[str, Any]) -> list[Recommendation]:
        recs: list[Recommendation] = []
        ga_rows = [r for r in data["ga"] if str(r.get("device", "all")) == "all"]
        mobile_rows = [r for r in data["ga"] if str(r.get("device", "")) == "mobile"]

        if ga_rows:
            latest = ga_rows[-1]
            bounce = float(latest.get("bounce_rate", 0))
            if bounce > 0.6:
                recs.append(
                    self._recommendation(
                        agent=self.name,
                        issue="Bounce rate above 60% on latest sessions",
                        evidence=[
                            self._evidence("ga_sessions", "bounce_rate", bounce),
                            self._evidence("ga_sessions", "sessions", float(latest.get("sessions", 0))),
                        ],
                        proposed_action="Improve landing page content and on-site navigation",
                        priority=Priority.MEDIUM,
                        confidence=Confidence.MEDIUM,
                        expected_impact="Lower bounce and lift engaged sessions",
                        effort=Effort.MEDIUM,
                        next_steps=["Audit top landing pages", "Add internal links and CTAs"],
                    )
                )

            mid = len(ga_rows) // 2
            first_half = mean(float(r.get("conversion_rate", 0)) for r in ga_rows[:mid])
            second_half = mean(float(r.get("conversion_rate", 0)) for r in ga_rows[mid:])
            if first_half and second_half < first_half * 0.95:
                recs.append(
                    self._recommendation(
                        agent=self.name,
                        issue="Conversion rate declining week over week",
                        evidence=[
                            self._evidence("ga_sessions", "conversion_rate", first_half),
                            self._evidence("ga_sessions", "conversion_rate", second_half),
                        ],
                        proposed_action="Investigate funnel drop-off and run a landing page experiment",
                        priority=Priority.HIGH,
                        confidence=Confidence.MEDIUM,
                        expected_impact="Reverse conversion decline within two weeks",
                        effort=Effort.MEDIUM,
                        next_steps=["Segment by traffic source", "Check recent campaign changes"],
                    )
                )

        if mobile_rows:
            mobile_bounce = mean(float(r.get("bounce_rate", 0)) for r in mobile_rows)
            if mobile_bounce > 0.65:
                recs.append(
                    self._recommendation(
                        agent=self.name,
                        issue="Mobile bounce rate elevated",
                        evidence=[
                            self._evidence("ga_sessions", "bounce_rate", mobile_bounce),
                            self._evidence("ga_sessions", "sessions", float(sum(r.get("sessions", 0) for r in mobile_rows))),
                        ],
                        proposed_action="Optimize mobile experience (speed, layout, CTAs)",
                        priority=Priority.MEDIUM,
                        confidence=Confidence.MEDIUM,
                        expected_impact="Recover mobile sessions and conversions",
                        effort=Effort.MEDIUM,
                        next_steps=["Test mobile page variants", "Review page speed on 4G"],
                    )
                )

        for row in data["gsc"]:
            impressions = float(row.get("impressions", 0))
            position = float(row.get("position", 0))
            if impressions >= 2000 and position > 10:
                query = str(row.get("query", ""))
                recs.append(
                    self._recommendation(
                        agent=self.name,
                        issue=f"Ranking opportunity for query '{query}'",
                        evidence=[
                            self._evidence("gsc_keywords", "position", position),
                            self._evidence("gsc_keywords", "impressions", impressions),
                        ],
                        proposed_action=f"Improve relevance and internal links for '{query}'",
                        priority=Priority.LOW,
                        confidence=Confidence.MEDIUM,
                        expected_impact="Move from page 2 toward top-5 positions",
                        effort=Effort.HIGH,
                        next_steps=["Refresh content around intent", "Build supporting internal links"],
                    )
                )
        return recs
