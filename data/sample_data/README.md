# Sample data

This directory holds **precomputed, realistic-but-synthetic** marketing data used by the
rule-based demo mode and the evaluation suite. No API keys are required: every tool reads
these CSVs through `data/connectors/csv_loader.py`.

| File | Contents | Consumers |
| --- | --- | --- |
| `website_crawl.csv` | Crawled site pages: meta, broken links, load speed | SEO agent |
| `gsc_keywords.csv` | Google Search Console keyword rows (clicks, impressions, CTR, position) | SEO + Analytics agents |
| `pagespeed_metrics.csv` | Lighthouse-style PageSpeed metrics per URL | SEO agent |
| `ga_sessions.csv` | GA-style session/revenue/conversion series by device | Analytics agent |
| `google_ads_campaigns.csv` | Google Ads campaign performance | Ads agent |
| `meta_ads_campaigns.csv` | Meta Ads campaign performance | Ads agent |
| `product_catalog.csv` | Product catalog: inventory, pricing, PDP conversion | E-commerce agent |

All files are regenerable from the source-of-truth fixtures committed here; no derived files
are stored elsewhere.
