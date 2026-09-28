# 120-Day Creator Workflow Session & Unit Costing Analysis

**Target Application:** Vertex AI Creative Studio (`genmedia-veo2` / Deployed as `creative-studio-aaie`)
**Google Cloud Project ID:** `creative-studio-867`
**Cloud Run Service:** `creative-studio-aaie`
**Analysis Period:** Last 120 Days (2026-03-24 to 2026-07-22)
**Report Generated:** 2026-07-22 17:37:11 UTC
**Author:** AI Engineering & Financial Operations Team

---

## Executive Summary

This study analyzes **120 days of historical creator usage data** across `199` distinct creator accounts within `genmedia-veo2` (deployed as Cloud Run service `creative-studio-aaie` in project `creative-studio-867`). By segmenting individual generation events into **Creator Sessions** (inactivity gap > 30 minutes), we identified **2344 total workflow sessions** comprising **5223 generative operations**.

Using standard benchmark cloud unit rates for multi-modal AI generation, total gross cloud compute spend across the 120-day period reached **$3,154.48**.

### Key Findings & Strategic Insights:
1. **Dominant Workflow Volume:** **Standalone Video (T2V/I2V)** and **Iterative Refinement** account for over **55%** of all creator sessions.
2. **Highest Cost Per Session:** **Post-Production Editing Workflows** (incorporating 4K upscaling tools) and **Multi-Turn Deep Stacking** command the highest unit costs at **$1.85** and **$2.61** per session respectively.
3. **Image-to-Video Convergence:** **Image-to-Video Pipelines** represent **20.6%** of total sessions and serve as a high-conversion gateway where creators preview image compositions ($0.03/gen) before committing to video generation ($0.60/video).

---

## Benchmark Reference Rate Sheet

The costing engine applies the following standardized rate card based on Google Cloud Vertex AI & GenMedia infrastructure pricing:

| Resource Type | Model / Provider | Unit Basis | Benchmark Rate | Standard Unit Example |
| :--- | :--- | :--- | :--- | :--- |
| **Video Generation** | Veo 2 / Omni Video | Per second of generated video | **$0.12 / sec** | 5s video = $0.60 |
| **Image Generation** | Imagen 3 / Nano Banana | Per generation request | **$0.03 / gen** | 1 image = $0.03 |
| **Audio Generation** | Chirp 3 / Lyria | Per second of generated audio | **$0.01 / sec** | 10s audio = $0.10 |
| **Upscaler / Video Tools** | Video Tooling / 4K Upscaler | Per second of processed output | **$0.25 / sec** | 5s upscale = $1.25 |

---

## 120-Day High-Level Usage Metrics

- **Total Active Creators:** `199`
- **Total Creator Sessions:** `2,344`
- **Total Generation Turns:** `5,223`
- **Average Turns per Session:** `2.23`
- **Total Gross Spend:** `$3,154.48`
- **Average Cost per Creator Session:** `$1.35`

---

## Creator Workflow Archetype Breakdown

Below is the comprehensive unit costing and session volume breakdown across the 6 discovered creator workflow archetypes:

| Workflow Archetype | Session Count | Session Share % | Avg Turns / Sess | Avg Elapsed Duration | Avg Cost ($) / Session | Total Spend ($) | Spend Share % |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Standalone Video (T2V / I2V)** | 730 | 31.14% | 1.0 | 1s | **$0.81** | **$592.32** | 18.78% |
| **Iterative Refinement** | 384 | 16.38% | 2.51 | 6m 53s | **$1.91** | **$734.07** | 23.27% |
| **Image-to-Video Pipeline** | 484 | 20.65% | 2.0 | 5m 27s | **$0.83** | **$400.02** | 12.68% |
| **Multi-Turn Deep Stacking** | 416 | 17.75% | 4.81 | 15m 56s | **$2.61** | **$1,087.68** | 34.48% |
| **Post-Production Editing Workflow** | 176 | 7.51% | 2.0 | 6m 59s | **$1.85** | **$325.60** | 10.32% |
| **Standalone Image Generation** | 154 | 6.57% | 1.38 | 57s | **$0.10** | **$14.79** | 0.47% |

---

## Deep Dive into Creator Workflow Archetypes

### 1. Standalone Video (T2V / I2V)
- **Profile:** Fast prompt-to-video testing or quick concept validation. The user generates a single 5–10s video and exits the session.
- **Session Share:** `31.14%` | **Avg Cost:** `$0.81`
- **Cost Driver:** Direct Veo 2 inference cost ($0.12/sec).
- **Optimization Strategy:** Introduce low-cost low-resolution preview mode (e.g. 360p fast preview) before committing to full 1080p generation.

### 2. Iterative Refinement
- **Profile:** Pro creators tuning text prompts, camera motions, or seeds across 2 to 4 consecutive video attempts.
- **Session Share:** `16.38%` | **Avg Cost:** `$1.91`
- **Cost Driver:** Sequential video calls compounding generation costs ($1.20 - $2.40 per session).
- **Optimization Strategy:** Implement prompt modification caching or latent seed re-use to reduce compute steps on secondary turns.

### 3. Image-to-Video Pipeline
- **Profile:** High-quality visual storytellers generating 1-2 Imagen 3 concept images first, selecting the optimal frame, and animating it via Veo 2 I2V.
- **Session Share:** `20.65%` | **Avg Cost:** `$0.83`
- **Cost Driver:** $0.03 image setup fee + $0.60+ video animation cost.
- **Optimization Strategy:** Highly cost-effective pipeline; encourage image pre-vis to reduce wasted full video renders.

### 4. Multi-Turn Deep Stacking
- **Profile:** Power creators crafting complex multi-modal narratives, chaining image assets, voiceovers (Chirp/Lyria), and multiple video clips (4+ turns).
- **Session Share:** `17.75%` | **Avg Cost:** `$2.61`
- **Cost Driver:** High turn count across heterogeneous media models.
- **Optimization Strategy:** Offer Creator Pro subscription bundles with bundled multi-turn quotas.

### 5. Post-Production Editing Workflow
- **Profile:** Enterprise or agency workflows generating a base video clip and subsequently applying 4K upscaling, spatial object rotation, or try-on tools.
- **Session Share:** `7.51%` | **Avg Cost:** `$1.85`
- **Cost Driver:** High tool processing cost ($0.25/sec for upscaler).
- **Optimization Strategy:** Add client-side pre-filtering and resolution checks before sending video streams to cloud upscaling workers.

### 6. Standalone Image Generation
- **Profile:** Graphic designers and concept artists generating standalone text-to-image variations.
- **Session Share:** `6.57%` | **Avg Cost:** `$0.10`
- **Cost Driver:** Fixed per-image rate ($0.03/gen).
- **Optimization Strategy:** Very low unit cost per session; ideal candidate for free tier allocation to drive user acquisition.

---

## Unit Costing & Pricing Tier Recommendations

Based on these findings, we recommend the following pricing tiers for product monetization:

1. **Free Creator Tier:**
   - 10 Standalone Image Generations ($0.30 credit value)
   - 2 Standalone Video Generations ($1.20 credit value)
   - *Target Unit Cost:* **<$1.50 / user / month**

2. **Pro Creator Plan ($29/month):**
   - Unlimited Image Generations
   - 35 Video Generations / Iterative Refinement Sessions (up to $21.00 compute value)
   - 5 Post-Production 4K Upscales (up to $6.25 compute value)
   - *Expected Margin:* **~25-30%** over raw cloud compute cost.

3. **Agency / Enterprise Studio ($99/month):**
   - Full access to Multi-Turn Deep Stacking & Post-Production Editing Workflows
   - Priority queueing for Veo 2 / Omni Video models.
   - *Expected Margin:* **~45%** with volume usage caps.

---

*Report compiled automatically by `tools/analyze_workflow_costing.py`.*
