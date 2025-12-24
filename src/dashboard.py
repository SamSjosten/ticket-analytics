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
import logging

from config.settings import DATA_DIR, TICKET_CATEGORIES, PRIORITY_LEVELS, TEAMS
from config.database import DatabaseConfig
from src.data_loader import load_tickets
from src.db_connector import SQLServerConnector
from src.auth0_manager import Auth0Manager
from src.analysis import (
    tickets_by_category,
    tickets_by_priority,
    tickets_by_status,
    avg_resolution_time_by_priority,
    tickets_over_time,
    team_performance,
    technician_performance,
    technician_detailed_breakdown,
    sla_compliance,
    generate_summary_stats
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Page configuration
st.set_page_config(
    page_title="IT Ticket Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Auth0 manager
auth_manager = Auth0Manager()
auth_manager.initialize_session_state()

# Validate Auth0 configuration
is_valid, msg = auth_manager.config.validate_config()
if not is_valid:
    st.error(f"⚠️ Auth0 Configuration Error: {msg}")
    st.info("""
    **Auth0 Setup Required:**
    1. Copy `.env.example` to `.env`
    2. Configure Auth0 settings in `.env` file
    3. Ensure callback URL matches Auth0 dashboard

    See `.env.example` for required Auth0 settings.
    """)
    st.stop()


@st.cache_data
def load_data():
    """Load and cache ticket data from SQL Server."""
    return load_tickets(source="sql")


def test_sql_connection():
    """Test SQL Server connection and return status."""
    connector = SQLServerConnector()
    return connector.test_connection()


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


def show_login_page():
    """Display login page for unauthenticated users."""
    st.title("🔒 IT Ticket Analytics Dashboard")
    st.markdown("---")

    # Center content with columns
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("""
        ### Welcome to IT Ticket Analytics

        Comprehensive insights into IT support tickets including:
        - Real-time ticket analytics
        - Team and technician performance tracking
        - SLA compliance monitoring
        - Interactive visualizations

        Please log in to access the dashboard.
        """)

        st.markdown("<br>", unsafe_allow_html=True)

        # Login button
        col_a, col_b, col_c = st.columns([1, 2, 1])
        with col_b:
            if st.button("🔐 Login with Auth0", use_container_width=True, type="primary"):
                auth_url = auth_manager.login()
                st.markdown(f'<meta http-equiv="refresh" content="0; url={auth_url}">',
                          unsafe_allow_html=True)
                st.info("Redirecting to Auth0...")

        st.markdown("<br><br>", unsafe_allow_html=True)

        st.info("""
        **First Time Users:**
        - You'll be redirected to Auth0 for secure authentication
        - Your account will be created automatically upon first login
        - All data is stored securely
        """)


def show_user_profile_sidebar():
    """Display user profile in sidebar."""
    user_info = st.session_state.get('user_info', {})

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 👤 User Profile")

    # Profile picture
    if user_info.get('picture'):
        st.sidebar.image(user_info['picture'], width=80)

    # User details
    st.sidebar.markdown(f"**{user_info.get('name', 'User')}**")
    st.sidebar.caption(user_info.get('email', ''))

    # Role badge (from database)
    db_user = auth_manager.get_user_from_database(user_info.get('sub'))
    if db_user:
        role = db_user.get('role', 'user')
        role_badge = {
            'admin': '🔴 Admin',
            'analyst': '🟡 Analyst',
            'user': '🟢 User'
        }.get(role, '🟢 User')
        st.sidebar.caption(f"Role: {role_badge}")

    # Logout button
    st.sidebar.markdown("<br>", unsafe_allow_html=True)
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        logout_url = auth_manager.get_logout_url()
        auth_manager.logout()
        st.markdown(f'<meta http-equiv="refresh" content="0; url={logout_url}">',
                  unsafe_allow_html=True)
        st.rerun()


def main():
    """Main dashboard application."""

    # ===== AUTHENTICATION GATE =====

    # Check for OAuth callback
    query_params = st.query_params

    if 'code' in query_params and 'state' in query_params:
        # Handle OAuth callback
        with st.spinner("Completing authentication..."):
            success, message = auth_manager.handle_callback(
                query_params['code'],
                query_params['state']
            )

        if success:
            st.success("Login successful!")
            st.query_params.clear()
            st.rerun()
        else:
            st.error(f"Authentication failed: {message}")
            st.info("Please try logging in again. If the problem persists, check your Auth0 configuration.")
            st.query_params.clear()
            st.stop()

    # Check authentication
    if not auth_manager.is_authenticated():
        show_login_page()
        st.stop()

    # ===== AUTHENTICATED DASHBOARD =====

    # Header
    st.title("📊 IT Ticket Analytics Dashboard")

    # Show user profile
    show_user_profile_sidebar()

    st.markdown("---")

    # Sidebar
    st.sidebar.header("🔌 Database Connection")

    # SQL Server connection status
    st.sidebar.markdown("### Connection Status")
    with st.sidebar:
        with st.spinner("Testing SQL Server connection..."):
            success, message = test_sql_connection()

        if success:
            st.success("✅ " + message)

            # Show database info
            try:
                connector = SQLServerConnector()
                info = connector.get_table_info()
                st.info(f"📊 {info['row_count']:,} records available")
                st.caption(f"Date range: {info['min_date']:%Y-%m-%d} to {info['max_date']:%Y-%m-%d}")
            except Exception as e:
                st.warning(f"Could not retrieve table info: {e}")
        else:
            st.error("❌ " + message)
            st.info("""
            **Configuration Required:**
            1. Copy `.env.example` to `.env`
            2. Update connection settings
            3. Ensure SQL Server is accessible
            """)
            return

    st.sidebar.markdown("---")
    st.sidebar.header("Filters & Options")

    # Load data from SQL Server
    try:
        df = load_data()
    except Exception as e:
        st.error(f"❌ Error loading data: {e}")
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

        # Technician selector at the top
        available_technicians = sorted(filtered_df['assigned_technician'].unique())

        # Add "All Technicians" option
        tech_options = ["All Technicians"] + available_technicians

        selected_tech = st.selectbox(
            "Select a technician to view performance",
            options=tech_options,
            index=0
        )

        # Filter data based on selection
        if selected_tech == "All Technicians":
            tech_filtered_df = filtered_df
            show_overview = True
            show_individual = False
        else:
            tech_filtered_df = filtered_df[filtered_df['assigned_technician'] == selected_tech]
            show_overview = False
            show_individual = True

        # Overview Charts (shown when "All Technicians" is selected)
        if show_overview:
            st.subheader("Overview - All Technicians")
            col1, col2 = st.columns(2)

            with col1:
                tech_perf_chart = plot_technician_performance(tech_filtered_df)
                if tech_perf_chart:
                    st.plotly_chart(tech_perf_chart, use_container_width=True)

            with col2:
                tech_time_chart = plot_technician_resolution_time(tech_filtered_df)
                if tech_time_chart:
                    st.plotly_chart(tech_time_chart, use_container_width=True)

        # Individual Technician Breakdown (shown when specific technician is selected)
        if show_individual and selected_tech != "All Technicians":
            tech_details = technician_detailed_breakdown(filtered_df, selected_tech)

            if tech_details:
                # Display technician header
                st.markdown(f"### {tech_details['technician_name']} - {tech_details['team']}")

                # Key metrics row
                col1, col2, col3, col4, col5 = st.columns(5)

                with col1:
                    st.metric("Total Tickets", tech_details['total_tickets'])

                with col2:
                    st.metric("Resolved", tech_details['resolved'])

                with col3:
                    st.metric("In Progress", tech_details['in_progress'])

                with col4:
                    st.metric("Open", tech_details['open'])

                with col5:
                    st.metric("Resolution Rate", f"{tech_details['resolution_rate_pct']}%")

                # Resolution time metrics
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    avg_time = tech_details['avg_resolution_hours']
                    st.metric("Avg Resolution Time", f"{avg_time:.1f}h" if avg_time else "N/A")

                with col2:
                    med_time = tech_details['median_resolution_hours']
                    st.metric("Median Resolution Time", f"{med_time:.1f}h" if med_time else "N/A")

                with col3:
                    min_time = tech_details['min_resolution_hours']
                    st.metric("Fastest Resolution", f"{min_time:.1f}h" if min_time else "N/A")

                with col4:
                    max_time = tech_details['max_resolution_hours']
                    st.metric("Slowest Resolution", f"{max_time:.1f}h" if max_time else "N/A")

                # Breakdown charts
                col1, col2 = st.columns(2)

                with col1:
                    # Category breakdown
                    if tech_details['category_breakdown']:
                        cat_df = pd.DataFrame(
                            list(tech_details['category_breakdown'].items()),
                            columns=['Category', 'Count']
                        )
                        fig = px.bar(
                            cat_df,
                            x='Category',
                            y='Count',
                            title=f"Tickets by Category - {selected_tech}",
                            color='Count',
                            color_continuous_scale='Blues'
                        )
                        fig.update_layout(showlegend=False)
                        st.plotly_chart(fig, use_container_width=True)

                with col2:
                    # Priority breakdown
                    if tech_details['priority_breakdown']:
                        pri_df = pd.DataFrame(
                            list(tech_details['priority_breakdown'].items()),
                            columns=['Priority', 'Count']
                        )
                        fig = px.pie(
                            pri_df,
                            values='Count',
                            names='Priority',
                            title=f"Tickets by Priority - {selected_tech}",
                            color='Priority',
                            color_discrete_map={
                                'Critical': '#dc3545',
                                'High': '#fd7e14',
                                'Medium': '#ffc107',
                                'Low': '#28a745'
                            }
                        )
                        st.plotly_chart(fig, use_container_width=True)

                # SLA Compliance breakdown
                if tech_details['sla_compliance']:
                    st.markdown("#### SLA Compliance by Priority")

                    sla_data = []
                    for priority, metrics in tech_details['sla_compliance'].items():
                        sla_data.append({
                            'Priority': priority,
                            'Total Resolved': metrics['total'],
                            'Within SLA': metrics['within_sla'],
                            'Compliance %': metrics['compliance_pct']
                        })

                    sla_df = pd.DataFrame(sla_data)
                    st.dataframe(sla_df, use_container_width=True, hide_index=True)

                # Additional metrics
                st.markdown(f"**Average Daily Volume:** {tech_details['avg_daily_volume']} tickets/day")

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
