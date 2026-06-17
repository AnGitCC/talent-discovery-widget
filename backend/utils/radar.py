"""Plotly radar chart and bar chart — green accent, 'quiet power' aesthetic."""
import plotly.graph_objects as go

GREEN = "#22c55e"
GREEN_FILL = "rgba(34, 197, 94, 0.12)"
GREEN_LINE = "rgba(34, 197, 94, 0.6)"


def create_radar_chart(
    dimensions: dict[str, float],
    title: str = "",
    max_score: float = 100,
) -> go.Figure:
    """Create a radar/spider chart for match dimension scores."""
    categories = list(dimensions.keys())
    values = list(dimensions.values())

    categories_closed = categories + [categories[0]]
    values_closed = values + [values[0]]

    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=values_closed,
        theta=categories_closed,
        fill='toself',
        fillcolor=GREEN_FILL,
        line=dict(color=GREEN, width=2),
        name='Match',
    ))

    fig.add_trace(go.Scatterpolar(
        r=[75] * len(categories_closed),
        theta=categories_closed,
        line=dict(color='#D1D1D6', width=0.5, dash='dash'),
        name='A Grade (75)',
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, max_score],
                tickvals=[0, 25, 50, 60, 75, 90, 100],
                ticktext=['0', '25', '50', 'B', 'A', 'S', '100'],
                gridcolor='#E5E5EA',
                linecolor='#D1D1D6',
                tickfont=dict(size=10, color='#86868B', family='Inter'),
            ),
            angularaxis=dict(
                gridcolor='#E5E5EA',
                linecolor='#D1D1D6',
                tickfont=dict(size=13, color='#1D1D1F', family='Inter'),
            ),
        ),
        showlegend=True,
        legend=dict(font=dict(size=11, color='#86868B', family='Inter')),
        height=500,
        margin=dict(l=40, r=40, t=20, b=40),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
    )

    return fig


def create_score_bar_chart(
    dimensions: dict[str, float],
    title: str = "",
) -> go.Figure:
    """Create a horizontal bar chart for dimension scores."""
    categories = list(dimensions.keys())
    values = list(dimensions.values())

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=categories[::-1],
        x=values[::-1],
        orientation='h',
        marker=dict(color=GREEN, line=dict(width=0)),
        text=[f'{v}' for v in values[::-1]],
        textposition='outside',
        textfont=dict(size=13, color='#86868B', family='Inter'),
        hovertemplate='%{y}: %{x}<extra></extra>',
    ))

    fig.update_layout(
        xaxis=dict(
            range=[0, 105],
            showgrid=True,
            gridcolor='#E5E5EA',
            tickfont=dict(size=10, color='#86868B'),
        ),
        yaxis=dict(tickfont=dict(size=13, color='#1D1D1F', family='Inter')),
        height=350,
        showlegend=False,
        margin=dict(l=40, r=20, t=20, b=20),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
    )

    return fig
