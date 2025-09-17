#!/usr/bin/env python3
"""
Create comprehensive visualizations for FRER test results
"""

import json
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.io as pio

# Load test data
with open('test_results_detailed.json', 'r') as f:
    data = json.load(f)

def create_throughput_chart():
    """Create interactive throughput over time chart"""

    df = pd.DataFrame(data['time_series'])

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df['timestamps'],
        y=df['throughput_mbps'],
        mode='lines+markers',
        name='Throughput',
        line=dict(color='#667eea', width=3),
        marker=dict(size=6),
        hovertemplate='<b>Time:</b> %{x}<br><b>Throughput:</b> %{y:.1f} Mbps<extra></extra>'
    ))

    # Add target line
    fig.add_hline(y=950, line_dash="dash", line_color="green",
                  annotation_text="Target: 950 Mbps")

    fig.update_layout(
        title="Throughput Performance Over Time",
        xaxis_title="Time",
        yaxis_title="Throughput (Mbps)",
        height=500,
        hovermode='x unified',
        showlegend=True,
        template='plotly_white'
    )

    return fig

def create_latency_histogram():
    """Create latency distribution histogram"""

    latency_data = data['latency_distribution']

    fig = go.Figure()

    fig.add_trace(go.Histogram(
        x=latency_data,
        nbinsx=50,
        name='Latency Distribution',
        marker=dict(
            color='#764ba2',
            line=dict(color='#4a2d6e', width=1)
        ),
        hovertemplate='<b>Latency Range:</b> %{x}<br><b>Count:</b> %{y}<extra></extra>'
    ))

    # Add normal distribution overlay
    import numpy as np
    from scipy import stats

    mean = np.mean(latency_data)
    std = np.std(latency_data)
    x_norm = np.linspace(min(latency_data), max(latency_data), 100)
    y_norm = stats.norm.pdf(x_norm, mean, std) * len(latency_data) * (max(latency_data) - min(latency_data)) / 50

    fig.add_trace(go.Scatter(
        x=x_norm,
        y=y_norm,
        mode='lines',
        name='Normal Distribution',
        line=dict(color='red', width=2, dash='dash')
    ))

    fig.update_layout(
        title="Latency Distribution Analysis",
        xaxis_title="Latency (ms)",
        yaxis_title="Frequency",
        height=500,
        showlegend=True,
        template='plotly_white',
        bargap=0.05
    )

    # Add statistics box
    fig.add_annotation(
        x=0.95, y=0.95,
        xref="paper", yref="paper",
        text=f"<b>Statistics:</b><br>Mean: {mean:.2f} ms<br>Std Dev: {std:.2f} ms<br>Min: {min(latency_data):.2f} ms<br>Max: {max(latency_data):.2f} ms",
        showarrow=False,
        bordercolor="#c7c7c7",
        borderwidth=1,
        bgcolor="white",
        align="left"
    )

    return fig

def create_elimination_rate_gauge():
    """Create gauge chart for elimination rate"""

    elimination_rate = data['statistics']['receiver_stats']['compound_stream_0']['elimination_rate']

    fig = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = elimination_rate,
        title = {'text': "Duplicate Elimination Rate"},
        delta = {'reference': 99.5, 'increasing': {'color': "green"}},
        gauge = {
            'axis': {'range': [95, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [95, 97], 'color': '#ffcccc'},
                {'range': [97, 99], 'color': '#ffffcc'},
                {'range': [99, 100], 'color': '#ccffcc'}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 99.5
            }
        }
    ))

    fig.update_layout(
        height=400,
        font={'size': 16}
    )

    return fig

def create_packet_flow_sankey():
    """Create Sankey diagram for packet flow"""

    stats = data['statistics']

    # Define nodes
    labels = ["Sender", "Path 1 (eth1)", "Path 2 (eth2)", "Receiver Input", "Eliminated", "Output"]

    # Define links
    source = [0, 0, 1, 2, 3, 3]
    target = [1, 2, 3, 3, 4, 5]
    value = [
        stats['sender_stats']['eth1_transmitted'],
        stats['sender_stats']['eth2_transmitted'],
        stats['receiver_stats']['member_stream_eth1']['received'],
        stats['receiver_stats']['member_stream_eth2']['received'],
        stats['receiver_stats']['compound_stream_0']['discarded_packets'],
        stats['receiver_stats']['compound_stream_0']['passed_packets']
    ]

    fig = go.Figure(data=[go.Sankey(
        node = dict(
            pad = 15,
            thickness = 20,
            line = dict(color = "black", width = 0.5),
            label = labels,
            color = ["#667eea", "#9f7aea", "#9f7aea", "#764ba2", "#dc3545", "#28a745"]
        ),
        link = dict(
            source = source,
            target = target,
            value = value,
            color = ["rgba(159, 122, 234, 0.4)"] * len(source)
        )
    )])

    fig.update_layout(
        title="FRER Packet Flow Analysis",
        height=500,
        font_size=12
    )

    return fig

def create_multi_metric_dashboard():
    """Create comprehensive dashboard with multiple metrics"""

    # Create subplots
    fig = make_subplots(
        rows=3, cols=2,
        subplot_titles=("Throughput Over Time", "Latency Over Time",
                       "CPU Usage", "Memory Usage",
                       "Packet Loss Events", "Elimination Rate"),
        specs=[[{'type': 'scatter'}, {'type': 'scatter'}],
               [{'type': 'scatter'}, {'type': 'scatter'}],
               [{'type': 'bar'}, {'type': 'scatter'}]],
        vertical_spacing=0.12,
        horizontal_spacing=0.15
    )

    df = pd.DataFrame(data['time_series'])

    # Throughput
    fig.add_trace(
        go.Scatter(x=df['timestamps'], y=df['throughput_mbps'],
                  mode='lines', name='Throughput',
                  line=dict(color='#667eea', width=2)),
        row=1, col=1
    )

    # Latency
    fig.add_trace(
        go.Scatter(x=df['timestamps'], y=df['latency_ms'],
                  mode='lines+markers', name='Latency',
                  line=dict(color='#764ba2', width=2),
                  marker=dict(size=4)),
        row=1, col=2
    )

    # CPU Usage
    fig.add_trace(
        go.Scatter(x=df['timestamps'], y=df['cpu_usage_percent'],
                  mode='lines', name='CPU Usage',
                  line=dict(color='#00a86b', width=2)),
        row=2, col=1
    )

    # Memory Usage
    fig.add_trace(
        go.Scatter(x=df['timestamps'], y=df['memory_usage_mb'],
                  mode='lines', name='Memory',
                  line=dict(color='#ffa500', width=2)),
        row=2, col=2
    )

    # Packet Loss
    fig.add_trace(
        go.Bar(x=df['timestamps'], y=df['packet_loss'],
               name='Packet Loss',
               marker_color='#dc3545'),
        row=3, col=1
    )

    # Elimination Rate
    fig.add_trace(
        go.Scatter(x=df['timestamps'], y=df['elimination_rate_percent'],
                  mode='lines', name='Elimination Rate',
                  line=dict(color='#28a745', width=2),
                  fill='tozeroy'),
        row=3, col=2
    )

    # Update layout
    fig.update_layout(
        height=1200,
        showlegend=False,
        title_text="FRER Performance Dashboard",
        template='plotly_white'
    )

    # Update axes labels
    fig.update_xaxes(title_text="Time", row=3, col=1)
    fig.update_xaxes(title_text="Time", row=3, col=2)
    fig.update_yaxes(title_text="Mbps", row=1, col=1)
    fig.update_yaxes(title_text="ms", row=1, col=2)
    fig.update_yaxes(title_text="%", row=2, col=1)
    fig.update_yaxes(title_text="MB", row=2, col=2)
    fig.update_yaxes(title_text="Packets", row=3, col=1)
    fig.update_yaxes(title_text="%", row=3, col=2)

    return fig

def create_test_scenarios_chart():
    """Create test scenarios comparison chart"""

    scenarios = data['test_scenarios']

    fig = go.Figure()

    # Extract scenario names and durations
    names = [s['name'] for s in scenarios]
    durations = [s['duration'] for s in scenarios]
    results = [100 if s['result'] == 'PASS' else 0 for s in scenarios]

    fig.add_trace(go.Bar(
        name='Duration (s)',
        x=names,
        y=durations,
        yaxis='y',
        marker_color='#667eea',
        text=durations,
        textposition='auto'
    ))

    fig.add_trace(go.Scatter(
        name='Success Rate',
        x=names,
        y=results,
        yaxis='y2',
        mode='lines+markers',
        line=dict(color='#28a745', width=3),
        marker=dict(size=10)
    ))

    fig.update_layout(
        title='Test Scenarios Overview',
        xaxis=dict(title='Test Scenario'),
        yaxis=dict(title='Duration (seconds)', side='left'),
        yaxis2=dict(title='Success Rate (%)', overlaying='y', side='right', range=[0, 110]),
        height=500,
        hovermode='x',
        template='plotly_white'
    )

    return fig

def save_all_charts():
    """Generate and save all charts"""

    charts = {
        'throughput': create_throughput_chart(),
        'latency': create_latency_histogram(),
        'elimination': create_elimination_rate_gauge(),
        'flow': create_packet_flow_sankey(),
        'dashboard': create_multi_metric_dashboard(),
        'scenarios': create_test_scenarios_chart()
    }

    # Save as HTML files
    for name, fig in charts.items():
        fig.write_html(f'docs/chart_{name}.html')
        print(f"✅ Created chart: chart_{name}.html")

    # Also save as static images if needed (requires kaleido)
    # for name, fig in charts.items():
    #     fig.write_image(f'docs/chart_{name}.png')

    return charts

if __name__ == "__main__":
    print("📊 Creating visualizations...")
    charts = save_all_charts()
    print(f"\n✨ Successfully created {len(charts)} interactive charts in docs/")