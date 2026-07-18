"""
VisualizationAgent — chart and visualization generation.

Responsibilities (Single Responsibility: visualization only):
- Generate histograms for numeric columns
- Generate boxplots for numeric columns
- Generate heatmaps for correlations
- Generate scatter matrices
- Generate bar charts for categorical columns

Returns Plotly JSON for each chart.
"""
from __future__ import annotations

import pandas as pd
from loguru import logger

from agents.schemas import VisualizationInput, VisualizationOutput, ChartSpec
from services.chart_service import ChartService


class VisualizationAgent:
    """
    Wraps ChartService to produce typed VisualizationOutput.
    Maintains single responsibility while providing agent interface.
    """

    def generate(self, df: pd.DataFrame, eda: dict, input_: VisualizationInput) -> VisualizationOutput:
        logger.info(f"[{input_.job_id[:8]}] VisualizationAgent generating charts")

        # Use existing service for core logic
        chart_service = ChartService()
        charts_dict = chart_service.generate_all(df, eda)

        # Convert to typed format
        charts = []
        for chart_dict in charts_dict:
            chart = ChartSpec(
                title=chart_dict["title"],
                chart_type=chart_dict["chart_type"],
                plotly_json=chart_dict["plotly_json"],
            )
            charts.append(chart)

        output = VisualizationOutput(
            job_id=input_.job_id,
            charts=charts,
            chart_count=len(charts),
        )

        logger.info(f"[{input_.job_id[:8]}] Generated {len(charts)} charts")
        return output
