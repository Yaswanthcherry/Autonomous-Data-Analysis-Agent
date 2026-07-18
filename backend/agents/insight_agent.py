"""
InsightAgent — AI-powered insights generation.

Responsibilities (Single Responsibility: insights only):
- Generate AI findings from analysis results
- Generate feature recommendations
- Generate business insights
- Generate executive summary

Uses OpenAI GPT-4o for natural language generation.
"""
from __future__ import annotations

import pandas as pd
from loguru import logger

from agents.schemas import InsightInput, InsightOutput
from services.ai_service import AIService


class InsightAgent:
    """
    Wraps AIService to produce typed InsightOutput.
    Maintains single responsibility while providing agent interface.
    """

    def generate(self, profile: dict, cleaning: dict, anomalies: dict, eda: dict,
                 model_results: list, input_: InsightInput) -> InsightOutput:
        logger.info(f"[{input_.job_id[:8]}] InsightAgent generating AI insights")

        # Use existing service for core logic
        ai_service = AIService()

        # Generate all insights (async operations)
        import asyncio

        async def _generate_all():
            findings = await ai_service.explain_findings(profile, cleaning, anomalies)
            feature_recs = await ai_service.recommend_features(eda, profile)
            business_insights = await ai_service.generate_business_insights(eda, model_results)
            executive_summary = await ai_service.generate_executive_summary(
                profile, eda, model_results, findings, business_insights
            )
            return findings, feature_recs, business_insights, executive_summary

        findings, feature_recs, business_insights, executive_summary = asyncio.run(_generate_all())

        output = InsightOutput(
            job_id=input_.job_id,
            findings=findings,
            feature_recommendations=feature_recs,
            business_insights=business_insights,
            executive_summary=executive_summary,
        )

        logger.info(f"[{input_.job_id[:8]}] Insights generated: {len(executive_summary)} chars summary")
        return output
