"""
Chart generation using Plotly — returns JSON-serializable chart specs
"""
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import plotly.figure_factory as ff
from loguru import logger


class ChartService:
    def generate_all(self, df: pd.DataFrame, eda_result: dict) -> list[dict]:
        charts = []
        num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        cat_cols = df.select_dtypes(include="object").columns.tolist()
        target = eda_result.get("target_candidate")

        # Histograms for numeric columns (first 6)
        for col in num_cols[:6]:
            fig = px.histogram(df, x=col, title=f"Distribution of {col}",
                               nbins=40, template="plotly_white")
            charts.append({"title": f"Distribution: {col}", "chart_type": "histogram",
                            "plotly_json": fig.to_dict()})

        # Box plots for numeric columns
        if len(num_cols) >= 2:
            melt = df[num_cols[:8]].melt(var_name="Feature", value_name="Value")
            fig = px.box(melt, x="Feature", y="Value", title="Box Plot — Numeric Features",
                         template="plotly_white")
            charts.append({"title": "Box Plots: Numeric Features", "chart_type": "boxplot",
                            "plotly_json": fig.to_dict()})

        # Correlation heatmap
        if len(num_cols) >= 2:
            corr = df[num_cols].corr().round(3)
            fig = go.Figure(data=go.Heatmap(
                z=corr.values.tolist(),
                x=corr.columns.tolist(),
                y=corr.index.tolist(),
                colorscale="RdBu",
                zmid=0,
            ))
            fig.update_layout(title="Correlation Heatmap", template="plotly_white")
            charts.append({"title": "Correlation Heatmap", "chart_type": "heatmap",
                            "plotly_json": fig.to_dict()})

        # Target distribution
        if target and target in df.columns:
            if eda_result.get("task_type") == "classification":
                vc = df[target].value_counts().reset_index()
                vc.columns = [target, "count"]
                fig = px.bar(vc, x=target, y="count",
                             title=f"Target Class Distribution: {target}",
                             template="plotly_white")
            else:
                fig = px.histogram(df, x=target, title=f"Target Distribution: {target}",
                                   nbins=40, template="plotly_white")
            charts.append({"title": f"Target Distribution: {target}", "chart_type": "bar",
                            "plotly_json": fig.to_dict()})

        # Scatter matrix (top 4 numeric features vs target)
        scatter_cols = [c for c in num_cols[:4] if c != target]
        if target and target in df.columns and scatter_cols:
            fig = px.scatter_matrix(df, dimensions=scatter_cols, color=target,
                                    title="Scatter Matrix", template="plotly_white")
            charts.append({"title": "Scatter Matrix", "chart_type": "scatter_matrix",
                            "plotly_json": fig.to_dict()})

        # Top categorical column counts
        for col in cat_cols[:3]:
            vc = df[col].value_counts().head(15).reset_index()
            vc.columns = [col, "count"]
            fig = px.bar(vc, x=col, y="count", title=f"Top Values: {col}",
                         template="plotly_white")
            charts.append({"title": f"Top Values: {col}", "chart_type": "bar",
                            "plotly_json": fig.to_dict()})

        logger.info(f"Generated {len(charts)} charts")
        return charts
