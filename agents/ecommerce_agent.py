"""E-commerce agent: inventory, pricing, and PDP conversion signals."""

from __future__ import annotations

from typing import Any

from ai_marketing_shared.schemas import AgentRun, Confidence, Effort, Priority, Recommendation

from agents.base import BaseAgent


class EcommerceAgent(BaseAgent):
    name = "ecommerce"
    description = "Finds stock-out risk, low inventory, weak PDP conversion, and pricing outliers."

    tools = ("fetch_product_catalog",)

    def _collect(self, run: AgentRun) -> dict[str, Any]:
        return {"catalog": self._call_tool(run, "fetch_product_catalog").get("rows", [])}

    def _analyze(self, data: dict[str, Any]) -> list[Recommendation]:
        recs: list[Recommendation] = []
        for row in data["catalog"]:
            sku = str(row.get("sku", ""))
            name = str(row.get("name", ""))
            inventory = float(row.get("inventory_level", 0))
            reorder_point = float(row.get("reorder_point", 0))
            backordered = bool(row.get("backordered", False))
            out_of_stock_days = float(row.get("out_of_stock_days", 0))
            conv_rate = float(row.get("conversion_rate", 0))
            views = float(row.get("views_last_30d", 0))

            if backordered or out_of_stock_days > 0:
                recs.append(
                    self._recommendation(
                        agent=self.name,
                        issue=f"Stock-out risk for {name} ({sku})",
                        evidence=[
                            self._evidence("product_catalog", "inventory_level", inventory),
                            self._evidence("product_catalog", "out_of_stock_days", out_of_stock_days),
                        ],
                        proposed_action=f"Prioritize restock for {name} ({sku})",
                        priority=Priority.CRITICAL,
                        confidence=Confidence.HIGH,
                        expected_impact="Avoid lost sales from unavailable best-sellers",
                        effort=Effort.MEDIUM,
                        next_steps=["Confirm lead time with supplier", "Split order across warehouses"],
                    )
                )
            if inventory < reorder_point:
                recs.append(
                    self._recommendation(
                        agent=self.name,
                        issue=f"Low inventory for {name} ({sku})",
                        evidence=[
                            self._evidence("product_catalog", "inventory_level", inventory),
                            self._evidence("product_catalog", "reorder_point", reorder_point),
                        ],
                        proposed_action=f"Place reorder for {name} ({sku}) above reorder point",
                        priority=Priority.HIGH,
                        confidence=Confidence.HIGH,
                        expected_impact="Keep top products in stock",
                        effort=Effort.LOW,
                        next_steps=["Trigger purchase order", "Review weekly sell-through"],
                    )
                )
            if conv_rate < 0.015 and views > 5000:
                recs.append(
                    self._recommendation(
                        agent=self.name,
                        issue=f"Weak PDP conversion for {name} ({sku})",
                        evidence=[
                            self._evidence("product_catalog", "conversion_rate", conv_rate),
                            self._evidence("product_catalog", "views_last_30d", views),
                        ],
                        proposed_action=f"Optimize product page for {name} ({sku})",
                        priority=Priority.MEDIUM,
                        confidence=Confidence.MEDIUM,
                        expected_impact="Convert existing traffic more efficiently",
                        effort=Effort.MEDIUM,
                        next_steps=["Add reviews and lifestyle imagery", "A/B test PDP copy"],
                    )
                )
            price = float(row.get("price_usd", 0))
            avg_price = float(row.get("avg_category_price_usd", 0))
            if avg_price and price > avg_price * 1.15:
                recs.append(
                    self._recommendation(
                        agent=self.name,
                        issue=f"Price above category average for {name} ({sku})",
                        evidence=[
                            self._evidence("product_catalog", "price_usd", price),
                            self._evidence("product_catalog", "avg_category_price_usd", avg_price),
                        ],
                        proposed_action=f"Review pricing and value communication for {name} ({sku})",
                        priority=Priority.LOW,
                        confidence=Confidence.MEDIUM,
                        expected_impact="Maintain price competitiveness without margin loss",
                        effort=Effort.MEDIUM,
                        next_steps=["Benchmark competitor prices", "Test bundle offer"],
                    )
                )
        return recs
