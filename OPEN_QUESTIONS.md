# OPEN_QUESTIONS.md — Autonomous Agent Escalations (§0 Rule 9)

Documenting uncertainties and rights boundaries surfaced during the autonomous iteration loop for human operator review.

---

### 1. Google News RSS Feed Connector (`scripts/run_google_news_rss_connector.py`)
- **Finding:** The endpoint `https://news.google.com/rss/search` provides news mentions by query without an API key. However, inspection of `https://news.google.com/robots.txt` reveals:
  ```
  User-agent: *
  Disallow: /
  Allow: /$
  Allow: /?
  Allow: /home$
  Allow: /home?
  Allow: /home/
  Allow: /nwshp$
  Allow: /topics/
  Allow: /publications/
  Allow: /stories/
  Allow: /swg/
  Allow: /about$
  ```
  `/rss` is not included in the `Allow` rules, meaning automated requests to `/rss/search` violate Google's `robots.txt` policy.
- **Action Taken:** In accordance with §0 Rule 3 ("Never scrape a restricted platform outside an approved acquisition_mode") and §0 Rule 9, the script is **not** wired into the default production pipeline and remains tagged with `"acquisition_mode": "rights_review_experiment"` and `"rights_status": "review_required"`.
- **Question for Human:** Should Google News RSS be deemed unpublishable under the competition's strict source rights policy, or is an alternative licensed/official news feed preferred?

---

### 2. Fagfolkguiden Review Syndication (`scripts/experimental_restricted/run_fagfolkguiden_reviews_connector.py`)
- **Finding:** `fagfolkguiden.no/robots.txt` permits crawling of `/bedrift/` pages. However, the review ratings embedded on these pages (`search.google.com/local/reviews`) are syndicated from Google Local Reviews rather than native to Fagfolkguiden. Furthermore, on a random 100-company sample of Norwegian businesses, over 90% return 404 because the directory caters almost exclusively to building tradesmen (snekker, rørlegger, etc.).
- **Action Taken:** Quarantined to `scripts/experimental_restricted/` per `AGENT_MISSION.md` line 295 instructions.
- **Question for Human:** Confirm whether third-party review syndication on directory pages should remain quarantined.

---

### 3. Sentiment Model Threshold Abstention (`scripts/run_sentiment_model.py`)
- **Finding:** The pinned model (`NOSIBLE/financial-sentiment-v1.2-base`) and its runtime (`torch`, `transformers`) are operational. However, `src/signal_scrape_core/external_footprint.py` defines a strict evidentiary threshold: sentiment scores may only be emitted when a company has $\ge 10$ independently sourced observations across $\ge 2$ distinct hosts (`sentiment_ready` gate). In typical 100-company batches, companies currently average 3–5 independent observations.
- **Action Taken:** The pipeline strictly reports `sentiment.status = "abstain"` rather than emitting low-confidence or speculative sentiment scores on sparse data (§0 Rule 2 compliant).
