# Problem and acceptance

> **With sparse ratings, can collaborative filtering recommend movies a user has not yet rated better than a popularity ranking, while keeping usable coverage for new users?**

**Why it matters:** A recommendation page is not the same as useful recommendations. The system has to show that the personalised signal improves the ranking, and that it falls back explicitly when there are too few ratings.

**Central tension:** Stricter filtering of similar users may raise relevance but shrinks the candidate set; the popularity fallback raises coverage but can also hide that the personalised part contributes nothing.

**Current evidence and gap:** [README.md](README.md) describes the Django service, user- and item-based collaborative filtering, the popularity fallback and where the reference code came from. That documents the engineering; it does not replace an offline comparison of recommendation quality.

**Smallest decisive acceptance test:** Hold out test ratings per user, and split by time when reliable timestamps exist. Fix the candidate set and compare popularity, user-CF and item-CF, reporting Recall/NDCG, coverage and cold-start groups, with fallback hits marked separately. Training must never see the held-out ratings. If the gains appear only for highly active users, restrict the claimed scope and keep the popularity baseline.

This is a proposed acceptance test; it claims no original recommendation algorithm and no new user outcomes.

中文版：[PROBLEM.zh.md](PROBLEM.zh.md)
