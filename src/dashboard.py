"""
Streamlit dashboard for IT Ticket Analytics.
"""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

from config.settings import DATA_DIR, TICKET_CATEGORIES, PRIORITY_LEVELS, TEAMS
from src.data_loader import load_tickets
from src.analysis import (
    tickets_by_category,
    tickets_by_priority,
    tickets_by_status,
    avg_resolution_time_by_priority,
    tickets_over_time,
    team_performance,
    technician_performance,
    sla_compliance,
    generate_summary_stats
)


# Page configuration
st.set_page_config(
    page_title="IT Ticket Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)


@st.cache_data
def load_data(filepath=None):
    """Load and cache ticket data."""
    if filepath is None:
        filepath = DATA_DIR / "tickets.csv"
    return load_tickets(filepath)


def create_metric_card(label, value, delta=None, delta_color="normal"):
    """Create a styled metric display."""
    st.metric(label=label, value=value, delta=delta, delta_color=delta_color)


def plot_category_distribution(df):
    """Create interactive bar chart for category distribution."""
    category_df = tickets_by_category(df)

    fig = px.bar(
        category_df,
        x='category',
        y='count',
        title='Tickets by Category',
        labels={'count': 'Number of Tickets', 'category': 'Category'},
        color='count',
        color_continuous_scale='Blues',
        text='count'
    )
    fig.update_traces(textposition='outside')
    fig.update_layout(showlegend=False, height=400)
    return fig


def plot_priority_pie(df):
    """Create pie chart for priority distribution."""
    priority_df = tickets_by_priority(df)

    fig = px.pie(
        priority_df,
        values='count',
        names='priority',
        title='Tickets by Priority',
        color='priority',
        color_discrete_map={
            'Critical': '#dc3545',
            'High': '#fd7e14',
            'Medium': '#ffc107',
            'Low': '#28a745'
        }
    )
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(height=400)
    return fig


def plot_status_distribution(df):
    """Create bar chart for status distribution."""
    status_df = tickets_by_status(df)

    fig = px.bar(
        status_df,
        x='status',
        y='count',
        title='Tickets by Status',
        labels={'count': 'Number of Tickets', 'status': 'Status'},
        color='status',
        color_discrete_map={
            'Resolved': '#28a745',
            'In Progress': '#ffc107',
            'Open': '#dc3545'
        },
        text='count'
    )
    fig.update_traces(textposition='outside')
    fig.update_layout(showlegend=False, height=400)
    return fig


def plot_resolution_time(df):
    """Create bar chart for average resolution time by priority."""
    resolution_df = avg_resolution_time_by_priority(df)

    fig = go.Figure()

    # Add actual average resolution time
    fig.add_trace(go.Bar(
        name='Average Resolution Time',
        x=resolution_df['priority'],
        y=resolution_df['avg_hours'],
        marker_color='lightblue',
        text=resolution_df['avg_hours'].round(1),
        textposition='outside'
    ))

    # Add SLA threshold line
    fig.add_trace(go.Scatter(
        name='SLA Threshold',
        x=resolution_df['priority'],
        y=resolution_df['sla_threshold'],
        mode='lines+markers',
        line=dict(color='red', width=2, dash='dash'),
        marker=dict(size=8)
    ))

    fig.update_layout(
        title='Average Resolution Time vs SLA Threshold by Priority',
        xaxis_title='Priority',
        yaxis_title='Hours',
        barmode='group',
        height=400,
        showlegend=True
    )

    return fig


def plot_team_performance(df):
    """Create bar chart for team performance."""
    team_df = team_performance(df)

    fig = go.Figure()

    fig.add_trace(go.Bar(
        name='Total Tickets',
        x=team_df['assigned_team'],
        y=team_df['total_tickets'],
        marker_color='lightblue'
    ))

    fig.add_trace(go.Bar(
        name='Resolved Tickets',
        x=team_df['assigned_team'],
        y=team_df['resolved_count'],
        marker_color='darkblue'
    ))

    fig.update_layout(
        title='Team Performance: Total vs Resolved Tickets',
        xaxis_title='Team',
        yaxis_title='Number of Tickets',
        barmode='group',
        height=400
    )

    return fig


def plot_trend_over_time(df, period='D'):
    """Create line chart for ticket trends over time."""
    trend_df = tickets_over_time(df, period)

    period_labels = {'D': 'Daily', 'W': 'Weekly', 'M': 'Monthly'}

    fig = px.line(
        trend_df,
        x='period',
        y='ticket_count',
        title=f'{period_labels.get(period, "Daily")} Ticket Volume Trend',
        labels={'ticket_count': 'Number of Tickets', 'period': 'Date'},
        markers=True
    )

    fig.update_traces(line_color='#0066cc', line_width=3)
    fig.update_layout(height=400)

    return fig


def plot_sla_compliance(df):
    """Create bar chart for SLA compliance."""
    sla_df = sla_compliance(df)

    fig = px.bar(
        sla_df,
        x='priority',
        y='sla_compliance_pct',
        title='SLA Compliance by Priority',
        labels={'sla_compliance_pct': 'Compliance %', 'priority': 'Priority'},
        color='sla_compliance_pct',
        color_continuous_scale='RdYlGn',
        text=sla_df['sla_compliance_pct'].round(1)
    )

    fig.update_traces(texttemplate='%{text}%', textposition='outside')
    fig.update_layout(showlegend=False, height=400)
    fig.add_hline(y=85, line_dash="dash", line_color="red",
                  annotation_text="Target: 85%")

    return fig


def plot_technician_performance(df):
    """Create bar chart for technician performance."""
    if 'assigned_technician' not in df.columns:
        return None

    tech_df = technician_performance(df)

    if tech_df.empty:
        return None

    # Sort by total tickets for better visualization
    tech_df = tech_df.sort_values("total_tickets", ascending=True).tail(15)  # Show top 15

    fig = go.Figure()

    fig.add_trace(go.Bar(
        name='Total Tickets',
        y=tech_df['assigned_technician'],
        x=tech_df['total_tickets'],
        orientation='h',
        marker_color='lightblue',
        text=tech_df['total_tickets'],
        textposition='outside'
    ))

    fig.update_layout(
        title='Top 15 Technicians by Ticket Volume',
        xaxis_title='Number of Tickets',
        yaxis_title='Technician',
        height=500,
        showlegend=False
    )

    return fig


def plot_technician_resolution_time(df):
    """Create scatter plot for technician resolution times."""
    if 'assigned_technician' not in df.columns:
        return None

    tech_df = technician_performance(df)

    if tech_df.empty:
        return None

    # Filter out technicians with no resolution data
    tech_df = tech_df.dropna(subset=['avg_resolution_hours'])

    fig = px.scatter(
        tech_df,
        x='total_tickets',
        y='avg_resolution_hours',
        size='resolved_count',
        color='assigned_team',
        hover_data=['assigned_technician', 'resolution_rate_pct'],
        title='Technician Performance: Tickets vs Resolution Time',
        labels={
            'total_tickets': 'Total Tickets',
            'avg_resolution_hours': 'Avg Resolution Time (hours)',
            'assigned_team': 'Team'
        }
    )

    fig.update_layout(height=500)

    return fig


def main():
    """Main dashboard application."""

    # Header
    st.title("📊 IT Ticket Analytics Dashboard")
    st.markdown("---")

    # Sidebar
    st.sidebar.header("Filters & Options")

    # Load data
    try:
        df = load_data()
    except FileNotFoundError:
        st.error("❌ Data file not found!")
        st.info("Please run `python src/generate_mock_data.py` to create sample data.")
        return

    # Date range filter
    min_date = df['created_date'].min().date()
    max_date = df['created_date'].max().date()

    date_range = st.sidebar.date_input(
        "Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

    # === DASHBOARD CONFIGURATION ===
    st.sidebar.header("⚙️ Dashboard Configuration")

    # Preset configurations
    preset = st.sidebar.selectbox(
        "Dashboard Preset",
        options=["Custom", "Executive Summary", "Detailed Analysis", "Technician View", "Visual Only"],
        index=0
    )

    # Apply preset configurations
    if preset == "Executive Summary":
        show_key_metrics = True
        show_detailed_data = False
        show_technician_perf = False
        show_trend_analysis = True
        show_visualizations = True
        show_category_chart = True
        show_priority_chart = True
        show_status_chart = False
        show_resolution_chart = False
        show_team_chart = True
        show_sla_chart = True
    elif preset == "Detailed Analysis":
        show_key_metrics = True
        show_detailed_data = True
        show_technician_perf = True
        show_trend_analysis = True
        show_visualizations = True
        show_category_chart = True
        show_priority_chart = True
        show_status_chart = True
        show_resolution_chart = True
        show_team_chart = True
        show_sla_chart = True
    elif preset == "Technician View":
        show_key_metrics = True
        show_detailed_data = True
        show_technician_perf = True
        show_trend_analysis = False
        show_visualizations = False
        show_category_chart = False
        show_priority_chart = False
        show_status_chart = False
        show_resolution_chart = False
        show_team_chart = False
        show_sla_chart = False
    elif preset == "Visual Only":
        show_key_metrics = False
        show_detailed_data = False
        show_technician_perf = False
        show_trend_analysis = True
        show_visualizations = True
        show_category_chart = True
        show_priority_chart = True
        show_status_chart = True
        show_resolution_chart = True
        show_team_chart = True
        show_sla_chart = True
    else:  # Custom
        with st.sidebar.expander("Display Sections", expanded=False):
            show_key_metrics = st.checkbox("Key Metrics", value=True)
            show_detailed_data = st.checkbox("Detailed Data Tables", value=True)
            show_technician_perf = st.checkbox("Technician Performance", value=True)
            show_trend_analysis = st.checkbox("Trend Analysis", value=True)
            show_visualizations = st.checkbox("Visualizations", value=True)

    # Individual visualization toggles (only for Custom preset)
    if preset == "Custom":
        if show_visualizations:
            with st.sidebar.expander("Visualization Options", expanded=False):
                show_category_chart = st.checkbox("Category Distribution", value=True)
                show_priority_chart = st.checkbox("Priority Distribution", value=True)
                show_status_chart = st.checkbox("Status Breakdown", value=True)
                show_resolution_chart = st.checkbox("Resolution Time vs SLA", value=True)
                show_team_chart = st.checkbox("Team Performance", value=True)
                show_sla_chart = st.checkbox("SLA Compliance", value=True)
        else:
            # Set defaults if visualizations section is hidden
            show_category_chart = show_priority_chart = show_status_chart = True
            show_resolution_chart = show_team_chart = show_sla_chart = True

    st.sidebar.markdown("---")

    # Filter by Category dropdown with radio buttons for fields
    st.sidebar.subheader("Filter Options")

    filter_type = st.sidebar.selectbox(
        "Select Filter Category",
        options=["All Data", "Category", "Priority", "Team", "Technician", "Status"]
    )

    # Initialize filter variables with defaults
    categories = df['category'].unique()
    priorities = df['priority'].unique()
    teams = df['assigned_team'].unique()
    technicians = df['assigned_technician'].unique() if 'assigned_technician' in df.columns else []
    statuses = df['status'].unique()

    # Apply specific filters based on selection
    if filter_type == "Category":
        selected_category = st.sidebar.radio(
            "Select Category",
            options=sorted(df['category'].unique())
        )
        categories = [selected_category]

    elif filter_type == "Priority":
        selected_priority = st.sidebar.radio(
            "Select Priority",
            options=["Critical", "High", "Medium", "Low"]
        )
        priorities = [selected_priority]

    elif filter_type == "Team":
        selected_team = st.sidebar.radio(
            "Select Team",
            options=sorted(df['assigned_team'].unique())
        )
        teams = [selected_team]

    elif filter_type == "Technician":
        if 'assigned_technician' in df.columns:
            selected_technician = st.sidebar.radio(
                "Select Technician",
                options=sorted(df['assigned_technician'].unique())
            )
            technicians = [selected_technician]

    elif filter_type == "Status":
        selected_status = st.sidebar.radio(
            "Select Status",
            options=sorted(df['status'].unique())
        )
        statuses = [selected_status]

    # Apply filters
    filtered_df = df.copy()

    if len(date_range) == 2:
        start_date, end_date = date_range
        filtered_df = filtered_df[
            (filtered_df['created_date'].dt.date >= start_date) &
            (filtered_df['created_date'].dt.date <= end_date)
        ]

    # Apply categorical filters
    filter_conditions = (
        (filtered_df['category'].isin(categories)) &
        (filtered_df['priority'].isin(priorities)) &
        (filtered_df['assigned_team'].isin(teams)) &
        (filtered_df['status'].isin(statuses))
    )

    # Add technician filter if column exists
    if 'assigned_technician' in filtered_df.columns and len(technicians) > 0:
        filter_conditions = filter_conditions & (filtered_df['assigned_technician'].isin(technicians))

    filtered_df = filtered_df[filter_conditions]

    # Summary statistics
    stats = generate_summary_stats(filtered_df)

    # ===== 1. KEY METRICS =====
    if show_key_metrics:
        st.header("📈 Key Metrics")
        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            create_metric_card("Total Tickets", stats['total_tickets'])

        with col2:
            create_metric_card("Resolved", stats['resolved_tickets'])

        with col3:
            create_metric_card("In Progress", stats['in_progress_tickets'])

        with col4:
            create_metric_card("Open", stats['open_tickets'])

        with col5:
            create_metric_card("Resolution Rate", f"{stats['resolution_rate_pct']}%")

        col6, col7, col8 = st.columns(3)

        with col6:
            create_metric_card("Avg Resolution Time", f"{stats['avg_resolution_hours']:.1f}h")

        with col7:
            create_metric_card("Median Resolution Time", f"{stats['median_resolution_hours']:.1f}h")

        with col8:
            create_metric_card("Top Category", stats['top_category'])

    # ===== 2. DETAILED DATA =====
    if show_detailed_data:
        st.markdown("---")
        st.header("📋 Detailed Data")

        # Create tabs based on whether technician data exists
        if 'assigned_technician' in filtered_df.columns:
            tab1, tab2, tab3, tab4, tab5 = st.tabs([
                "Team Performance",
                "Technician Performance",
                "SLA Compliance",
                "Resolution Times",
                "Raw Data"
            ])

            with tab1:
                st.dataframe(
                    team_performance(filtered_df),
                    use_container_width=True,
                    hide_index=True
                )

            with tab2:
                tech_perf_df = technician_performance(filtered_df)
                if not tech_perf_df.empty:
                    st.dataframe(
                        tech_perf_df,
                        use_container_width=True,
                        hide_index=True
                    )
                else:
                    st.info("No technician data available")

            with tab3:
                st.dataframe(
                    sla_compliance(filtered_df),
                    use_container_width=True,
                    hide_index=True
                )

            with tab4:
                st.dataframe(
                    avg_resolution_time_by_priority(filtered_df),
                    use_container_width=True,
                    hide_index=True
                )

            with tab5:
                # Include technician in raw data display
                raw_columns = [
                    'ticket_id', 'created_date', 'resolved_date',
                    'category', 'priority', 'assigned_team',
                    'assigned_technician', 'status', 'resolution_time_hours'
                ]
                st.dataframe(
                    filtered_df[raw_columns],
                    use_container_width=True,
                    hide_index=True
                )
        else:
            tab1, tab2, tab3, tab4 = st.tabs([
                "Team Performance",
                "SLA Compliance",
                "Resolution Times",
                "Raw Data"
            ])

            with tab1:
                st.dataframe(
                    team_performance(filtered_df),
                    use_container_width=True,
                    hide_index=True
                )

            with tab2:
                st.dataframe(
                    sla_compliance(filtered_df),
                    use_container_width=True,
                    hide_index=True
                )

            with tab3:
                st.dataframe(
                    avg_resolution_time_by_priority(filtered_df),
                    use_container_width=True,
                    hide_index=True
                )

            with tab4:
                st.dataframe(
                    filtered_df[[
                        'ticket_id', 'created_date', 'resolved_date',
                        'category', 'priority', 'assigned_team',
                        'status', 'resolution_time_hours'
                    ]],
                    use_container_width=True,
                    hide_index=True
                )

    # ===== 3. TECHNICIAN PERFORMANCE =====
    if show_technician_perf and 'assigned_technician' in filtered_df.columns:
        st.markdown("---")
        st.header("👤 Technician Performance")

        col1, col2 = st.columns(2)

        with col1:
            tech_perf_chart = plot_technician_performance(filtered_df)
            if tech_perf_chart:
                st.plotly_chart(tech_perf_chart, use_container_width=True)

        with col2:
            tech_time_chart = plot_technician_resolution_time(filtered_df)
            if tech_time_chart:
                st.plotly_chart(tech_time_chart, use_container_width=True)

    # ===== 4. TREND ANALYSIS =====
    if show_trend_analysis:
        st.markdown("---")
        st.header("📈 Trend Analysis")

        trend_period = st.radio(
            "Select Time Period",
            options=['Daily', 'Weekly', 'Monthly'],
            horizontal=True,
            index=0
        )

        period_map = {'Daily': 'D', 'Weekly': 'W', 'Monthly': 'M'}
        st.plotly_chart(
            plot_trend_over_time(filtered_df, period_map[trend_period]),
            use_container_width=True
        )

    # ===== 5. VISUALIZATIONS =====
    if show_visualizations:
        st.markdown("---")
        st.header("📊 Visualizations")

        # Row 1: Category and Priority
        charts_row1 = []
        if show_category_chart:
            charts_row1.append(("category", plot_category_distribution(filtered_df)))
        if show_priority_chart:
            charts_row1.append(("priority", plot_priority_pie(filtered_df)))

        if charts_row1:
            cols = st.columns(len(charts_row1))
            for idx, (chart_type, chart) in enumerate(charts_row1):
                with cols[idx]:
                    st.plotly_chart(chart, use_container_width=True)

        # Row 2: Status and Resolution Time
        charts_row2 = []
        if show_status_chart:
            charts_row2.append(("status", plot_status_distribution(filtered_df)))
        if show_resolution_chart:
            charts_row2.append(("resolution", plot_resolution_time(filtered_df)))

        if charts_row2:
            cols = st.columns(len(charts_row2))
            for idx, (chart_type, chart) in enumerate(charts_row2):
                with cols[idx]:
                    st.plotly_chart(chart, use_container_width=True)

        # Row 3: Team Performance and SLA Compliance
        charts_row3 = []
        if show_team_chart:
            charts_row3.append(("team", plot_team_performance(filtered_df)))
        if show_sla_chart:
            charts_row3.append(("sla", plot_sla_compliance(filtered_df)))

        if charts_row3:
            cols = st.columns(len(charts_row3))
            for idx, (chart_type, chart) in enumerate(charts_row3):
                with cols[idx]:
                    st.plotly_chart(chart, use_container_width=True)

    # Footer
    st.markdown("---")
    st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Total records: {len(filtered_df)}")


if __name__ == "__main__":
    main()
