"""
AI/LLM service — findings, features, insights, summary, chat Q&A
"""
import json

from openai import AsyncOpenAI
from core.config import settings
from core.error_handling import retry, openai_circuit_breaker
from loguru import logger


class AIService:
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=settings.GROQ_API_KEY,
            base_url="https://api.groq.com/openai/v1",
        )
        self.model = settings.GROQ_MODEL

    async def explain_findings(
        self,
        profile: dict,
        cleaning: dict,
        anomalies: dict
    ) -> str:

        prompt = f"""You are a senior data scientist. Analyze the following dataset profile and cleaning report.
Provide clear, concise findings in plain English (3-5 bullet points).

Profile summary:
- Rows: {profile.get('rows', 'N/A')}, Columns: {profile.get('cols', 'N/A')}
- Duplicate rows: {profile.get('duplicate_rows', 0)}
- Columns with >10% nulls: {
    [
        c.get('name')
        for c in profile.get('columns', [])
        if c.get('null_pct', 0) > 10
    ]
}

Cleaning actions taken:
{json.dumps(cleaning.get('actions', [])[:5], indent=2)}

IQR outlier summary (top 3 columns):
{json.dumps(
    dict(list(anomalies.get('iqr', {}).items())[:3]),
    indent=2
)}
"""

        return await self._complete(prompt)

    async def recommend_features(
        self,
        eda: dict,
        profile: dict
    ) -> str:

        prompt = f"""You are a machine learning expert. Based on the EDA below, recommend:
1. Which features are most promising for modeling
2. Which features to drop or transform
3. Any feature engineering ideas

Task type: {eda.get('task_type')}
Target column: {eda.get('target_candidate')}
Skewed columns: {
    [
        c.get('column')
        for c in eda.get('skewed_columns', [])
    ]
}
High cardinality columns: {
    [
        c.get('column')
        for c in eda.get('high_cardinality_columns', [])
    ]
}
Top correlations with target available in correlation matrix.

Be specific and actionable. Use bullet points.
"""

        return await self._complete(prompt)

    async def generate_business_insights(
        self,
        eda: dict,
        model_results: list[dict]
    ) -> str:

        best = next(
            (
                m for m in model_results
                if m.get("is_best")
            ),
            model_results[0] if model_results else {}
        )

        top_features = list(
            best.get("feature_importance", {}).keys()
        )[:5] if best else []

        prompt = f"""You are a business intelligence analyst. Generate 5-7 actionable business insights based on:

Task type: {eda.get('task_type')}
Target variable: {eda.get('target_candidate')}
Best model: {best.get('model_name', 'N/A')}
Model metrics: {best.get('metrics', {})}
Most important features: {top_features}
Class distribution: {eda.get('class_balance', {})}

Write insights a business stakeholder can act on.
No technical jargon.
Use numbered list.
"""

        return await self._complete(prompt)

    async def generate_executive_summary(
        self,
        profile: dict,
        eda: dict,
        model_results: list[dict],
        findings: str,
        insights: str
    ) -> str:

        best = next(
            (
                m for m in model_results
                if m.get("is_best")
            ),
            {}
        )

        prompt = f"""Write a concise executive summary (200-300 words) for a data analysis report.

Dataset: {profile.get('rows', 'N/A')} rows, {profile.get('cols', 'N/A')} columns

Analysis type: {eda.get('task_type', 'exploratory')}

Target variable: {eda.get('target_candidate', 'N/A')}

Best performing model: {best.get('model_name', 'N/A')}

Model performance: {best.get('metrics', {})}

Key findings:
{findings[:500]}

Business insights:
{insights[:500]}

The summary should cover:
- what was analyzed
- key patterns found
- model performance
- top recommendations
"""

        return await self._complete(prompt)

    async def answer_question(
        self,
        question: str,
        context: dict,
        history: list[dict]
    ) -> str:

        system = """You are an expert AI Data Analyst assistant.
Answer questions about the dataset analysis concisely and accurately.
Use data from the context provided.
If something isn't in the context, say so rather than guessing.
"""

        messages = [
            {
                "role": "system",
                "content": system
            }
        ]

        context_str = json.dumps(
            {
                "profile": (
                    context.get("results", [{}])[0].get(
                        "data",
                        {}
                    )
                    if context.get("results")
                    else {}
                ),

                "task_type": next(
                    (
                        r["data"].get("task_type")
                        for r in context.get("results", [])
                        if r.get("type") == "eda"
                    ),
                    None
                ),

                "best_model": next(
                    (
                        m
                        for m in context.get("models", [])
                        if m.get("is_best")
                    ),
                    {}
                ),

                "executive_summary": context.get("summary"),
            },
            indent=2
        )[:3000]

        messages.append(
            {
                "role": "user",
                "content": f"Context from analysis:\n{context_str}"
            }
        )

        for msg in history[-6:]:
            messages.append(
                {
                    "role": msg["role"],
                    "content": msg["content"]
                }
            )

        messages.append(
            {
                "role": "user",
                "content": question
            }
        )

        return await self._complete_messages(messages)

    async def _complete(self, prompt: str) -> str:
        return await self._complete_messages(
            [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

    @retry(
        max_attempts=3,
        delay=1.0,
        backoff=2.0,
        exceptions=(Exception,)
    )
    @openai_circuit_breaker.call
    async def _complete_messages(
        self,
        messages: list[dict]
    ) -> str:

        try:
            resp = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=1000,
                temperature=0.4,
            )

            return resp.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise