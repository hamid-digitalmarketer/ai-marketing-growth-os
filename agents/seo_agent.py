"""SEO agent: crawl + Search Console + PageSpeed signals."""

from __future__ import annotations

from typing import Any

from ai_marketing_shared.schemas import AgentRun, Confidence, Effort, Priority, Recommendation

from agents.base import BaseAgent


class SeoAgent(BaseAgent):
    name = "seo"
    description = "Finds technical SEO issues, low-CTR queries, and slow pages."

    tools = ("fetch_website_crawl", "fetch_gsc_keywords", "fetch_pagespeed")

    def _collect(self, run: AgentRun) -> dict[str, Any]:
        return {
            "crawl": self._call_tool(run, "fetch_website_crawl").get("rows", []),
            "gsc": self._call_tool(run, "fetch_gsc_keywords").get("rows", []),
            "pagespeed": self._call_tool(run, "fetch_pagespeed").get("rows", []),
        }

    def _analyze(self, data: dict[str, Any]) -> list[Recommendation]:
        recs: list[Recommendation] = []
        for page in data["crawl"]:
            url = str(page.get("url", ""))
            if int(page.get("broken_links", 0)) > 0:
                recs.append(
                    self._recommendation(
                        agent=self.name,
                        issue=f"Broken links on {url}",
                        evidence=[
                            self._evidence("website_crawl", "broken_links", float(page["broken_links"])),
                            self._evidence("website_crawl", "load_speed_ms", float(page["load_speed_ms"])),
                        ],
                        proposed_action=f"Fix broken links on {url} and re-crawl",
                        priority=Priority.HIGH,
                        confidence=Confidence.HIGH,
                        expected_impact="Recover crawl equity and avoid ranking loss",
                        effort=Effort.MEDIUM,
                        next_steps=["Re-run crawl after fixes", "Monitor 404 log for one week"],
                    )
                )
            if not bool(page.get("has_meta_description", True)):
                recs.append(
                    self._recommendation(
                        agent=self.name,
                        issue=f"Missing meta description on {url}",
                        evidence=[
                            self._evidence("website_crawl", "meta_description_length", float(page["meta_description_length"]))
                        ],
                        proposed_action=f"Write a compelling meta description for {url}",
                        priority=Priority.MEDIUM,
                        confidence=Confidence.HIGH,
                        expected_impact="Improve CTR from search results",
                        effort=Effort.LOW,
                        next_steps=["Draft 150-160 char description", "Update CMS and re-crawl"],
                    )
                )
        for row in data["gsc"]:
            impressions = float(row.get("impressions", 0))
            ctr = float(row.get("ctr", 0))
            if impressions >= 2000 and ctr < 0.01:
                query = str(row.get("query", ""))
                recs.append(
                    self._recommendation(
                        agent=self.name,
                        issue=f"Low CTR for query '{query}' despite {int(impressions)} impressions",
                        evidence=[
                            self._evidence("gsc_keywords", "ctr", ctr),
                            self._evidence("gsc_keywords", "impressions", impressions),
                            self._evidence("gsc_keywords", "position", float(row.get("position", 0))),
                        ],
                        proposed_action=f"Improve title/meta for query '{query}'",
                        priority=Priority.MEDIUM,
                        confidence=Confidence.MEDIUM,
                        expected_impact="Gain incremental clicks without new queries",
                        effort=Effort.LOW,
                        next_steps=["A/B test two title variants", "Measure CTR change in 2 weeks"],
                    )
                )
        for row in data["pagespeed"]:
            url = str(row.get("url", ""))
            lcp = float(row.get("lcp_ms", 0))
            tbt = float(row.get("tbt_ms", 0))
            if lcp > 2500:
                recs.append(
                    self._recommendation(
                        agent=self.name,
                        issue=f"Slow LCP on {url}",
                        evidence=[
                            self._evidence("pagespeed_metrics", "lcp_ms", lcp),
                            self._evidence("pagespeed_metrics", "lighthouse_performance", float(row.get("lighthouse_performance", 0))),
                        ],
                        proposed_action=f"Optimize LCP on {url} (compress images, preload hero)",
                        priority=Priority.MEDIUM,
                        confidence=Confidence.MEDIUM,
                        expected_impact="Improve Core Web Vitals and ranking",
                        effort=Effort.MEDIUM,
                        next_steps=["Identify largest contentful paint element", "Re-test with Lighthouse"],
                    )
                )
            if tbt > 600:
                recs.append(
                    self._recommendation(
                        agent=self.name,
                        issue=f"High Total Blocking Time on {url}",
                        evidence=[
                            self._evidence("pagespeed_metrics", "tbt_ms", tbt),
                            self._evidence("pagespeed_metrics", "total_bytes_kb", float(row.get("total_bytes_kb", 0))),
                        ],
                        proposed_action=f"Reduce long tasks and JS bundle size on {url}",
                        priority=Priority.LOW,
                        confidence=Confidence.MEDIUM,
                        expected_impact="Improve interactivity score",
                        effort=Effort.HIGH,
                        next_steps=["Code-split main bundle", "Defer third-party scripts"],
                    )
                )
        return recs
