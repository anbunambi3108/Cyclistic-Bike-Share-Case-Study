import os 
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import warnings
from datetime import datetime, timedelta
import io
import folium
from streamlit_folium import st_folium

# Ignore warnings for cleaner output
warnings.filterwarnings('ignore')

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================
st.set_page_config(
    page_title="Cyclistic Bike-Share Analytics",
    page_icon="🚴",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# CUSTOM STYLING
# ============================================================================
st.markdown("""
    <style>
    .main {background-color: #f8f9fa;}
    
    /* Custom metric card style (retained from original for consistency) */
    .metric-box {
        background: linear-gradient(135deg, #1a4d7d 0%, #f4a460 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .header-title {
        color: #1a4d7d;
        font-size: 2.5em;
        font-weight: bold;
        margin-bottom: 10px;
    }
    .subheader {
        color: #1a4d7d;
        font-size: 1.5em;
        font-weight: bold;
        margin-top: 20px;
        margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# ============================================================================
# DATA LOADING & PREPARATION
# ============================================================================
@st.cache_data
def load_data():
    """Load data from parquet file with error handling and prepare date columns"""
    try:
        # NOTE: Assumes 'Data/12_Months_data/combined_cyclistic_data.parquet' exists.
        data_path = "Data/12_Months_data/combined_cyclistic_data.parquet"
        # Explicit existence check
        if not os.path.exists(data_path):
            st.error(f"❌ Parquet file not found at: {data_path}")
            return None
        df = pd.read_parquet(data_path)
        
        # Ensure datetime columns are properly formatted
        df['started_at'] = pd.to_datetime(df['started_at'], errors='coerce')
        df['ended_at'] = pd.to_datetime(df['ended_at'], errors='coerce')
        df = df.dropna(subset=['started_at', 'ended_at'])
        
        # Validate data integrity
        if df.empty:
            st.error("❌ Dataset is empty!")
            return None
        
        # Calculate ride time
        if 'ride_time_min' not in df.columns:
            df['ride_time_min'] = (df['ended_at'] - df['started_at']).dt.total_seconds() / 60
        
        # Remove rides that are too short (e.g., less than 1 minute) or too long (e.g., > 24 hours)
        df = df[(df['ride_time_min'] > 1) & (df['ride_time_min'] < 1440)]

        # --- Mandatory for sorting and plotting ---
        df['month_year'] = df['started_at'].dt.to_period('M').astype(str)
        df['hour'] = df['started_at'].dt.hour
        df['date'] = df['started_at'].dt.date
        # --- End of mandatory columns ---
        
        # Add 'weekday' and 'season' columns if they don't exist
        if 'weekday' not in df.columns:
            df['weekday'] = df['started_at'].dt.day_name().str[:3] # e.g., Mon, Tue
        if 'season' not in df.columns:
            def get_season(month):
                if month in [12, 1, 2]: return 'Winter'
                elif month in [3, 4, 5]: return 'Spring'
                elif month in [6, 7, 8]: return 'Summer'
                else: return 'Fall'
            df['season'] = df['started_at'].dt.month.apply(get_season)

        st.success(f"✅ Data loaded successfully: {len(df):,} rides")
        return df
    
    except FileNotFoundError:
        st.error("❌ Parquet file not found. Please check the file path.")
        return None
    except Exception as e:
        st.error(f"❌ Error loading data: {str(e)}")
        return None

# ============================================================================
# HELPER & QUERY FUNCTIONS
# ============================================================================

# --- Data Filtering ---
def filter_data(df, rider_type, seasons, bike_types):
    """Filter data based on user selections"""
    filtered_df = df.copy()
    
    if rider_type != "All Riders":
        filtered_df = filtered_df[filtered_df['member_casual'] == rider_type.lower()]
    
    if seasons:
        filtered_df = filtered_df[filtered_df['season'].isin(seasons)]
        
    if bike_types:
        filtered_df = filtered_df[filtered_df['rideable_type'].isin(bike_types)]
    
    return filtered_df

# --- Geographic Queries ---

def query_station_stats(df, station_col, lat_col, lng_col, n=20):
    """Queries top N stations with ride count and avg duration for mapping/tables"""
    grouped = df.groupby([station_col]).agg(
        Trips=('ride_id', 'count'),
        Avg_Duration=('ride_time_min', 'mean'),
        Lat=(lat_col, 'first'),
        Lng=(lng_col, 'first'),
        Member_Trips=('member_casual', lambda x: (x.astype(str).str.strip().str.lower() == 'member').sum()),
        Casual_Trips=('member_casual', lambda x: (x.astype(str).str.strip().str.lower() == 'casual').sum())
    ).reset_index().rename(columns={station_col: 'Station Name', 'Avg_Duration': 'Avg Duration'})
    
    grouped['Avg Duration'] = grouped['Avg Duration'].round(0).astype(int)
    
    return grouped.sort_values('Trips', ascending=False).head(n)

def query_top_routes(df, n=20):
    """Queries top N routes with ride count and member/casual breakdown"""
    routes = df.groupby(['start_station_name', 'end_station_name']).agg({
        'ride_id': 'count',
        'ride_time_min': 'mean',
        'member_casual': lambda x: (x.astype(str).str.strip().str.lower() == 'member').sum()
    }).reset_index()
    
    routes.columns = ['Start Station', 'End Station', 'Trips', 'Avg Duration', 'Member Trips']
    routes = routes.nlargest(n, 'Trips')
    routes['Casual Trips'] = routes['Trips'] - routes['Member Trips']
    
    # Final formatting
    routes['Trips'] = routes['Trips'].round(0).astype(int)
    routes['Avg Duration'] = routes['Avg Duration'].round(0).astype(int)
    routes['Member Trips'] = routes['Member Trips'].round(0).astype(int)
    routes['Casual Trips'] = routes['Casual Trips'].round(0).astype(int)
    
    return routes

# --- Holiday Data (Retained for consistency) ---
HOLIDAYS_DATA = [
    ('2024-09-02', 'Labor Day'), ('2024-10-14', 'Columbus Day'), 
    ('2024-11-11', 'Veterans Day'), ('2024-11-28', 'Thanksgiving'), 
    ('2024-12-25', 'Christmas'), ('2025-01-01', "New Year's Day"), 
    ('2025-01-20', 'MLK Jr. Day'), ('2025-02-17', "Presidents' Day"), 
    ('2025-05-26', 'Memorial Day'), ('2025-06-19', 'Juneteenth'), 
    ('2025-07-04', 'Independence Day'), ('2025-09-01', 'Labor Day'),
]

def get_holiday_df():
    """Create holiday dataframe"""
    holiday_df = pd.DataFrame(HOLIDAYS_DATA, columns=['holiday_date', 'holiday_name'])
    holiday_df['holiday_date'] = pd.to_datetime(holiday_df['holiday_date']).dt.date
    return holiday_df

def query_holiday_stats(df):
    """Statistical summary by holiday"""
    holiday_df = get_holiday_df()
    df['date'] = df['started_at'].dt.date 
    
    holiday_rides = df[df['date'].isin(holiday_df['holiday_date'])].copy()
    
    if holiday_rides.empty:
        return pd.DataFrame()
    
    holiday_rides = holiday_rides.merge(
        holiday_df, left_on='date', right_on='holiday_date', how='left'
    )
    
    stats_list = []
    for holiday_date in holiday_rides['holiday_date'].unique():
        holiday_subset = holiday_rides[holiday_rides['holiday_date'] == holiday_date]
        if holiday_subset.empty: continue
            
        holiday_name = holiday_subset['holiday_name'].iloc[0]
        total = len(holiday_subset)
        members = len(holiday_subset[holiday_subset['member_casual'] == 'member'])
        casual = total - members
        
        member_subset = holiday_subset[holiday_subset['member_casual']=='member']
        casual_subset = holiday_subset[holiday_subset['member_casual']=='casual']

        stats_list.append({
            'holiday_date': holiday_date,
            'holiday_name': holiday_name,
            'total_rides': total,
            'member_rides': members,
            'casual_rides': casual,
            'member_pct': round((members / total * 100) if total > 0 else 0, 1),
            'casual_pct': round((casual / total * 100) if total > 0 else 0, 1),
            'avg_member_duration': round(member_subset['ride_time_min'].mean(), 1) if not member_subset.empty else 0,
            'avg_casual_duration': round(casual_subset['ride_time_min'].mean(), 1) if not casual_subset.empty else 0
        })
    
    return pd.DataFrame(stats_list).sort_values('holiday_date')

# --- Plotly Enhancement ---
def enhance_plotly_figure(fig, show_legend=False, x_anchor='left', y_anchor='top', x_pos=1.05, y_pos=1):
    """Applies consistent styling, legend placement, and tooltip rounding."""
    legend_config = dict(
        orientation="v", yanchor=y_anchor, y=y_pos, xanchor=x_anchor, x=x_pos, bgcolor='rgba(0,0,0,0)'
    )

    fig.update_layout(
        legend=legend_config,
        showlegend=show_legend,
        margin=dict(l=20, r=20, t=50, b=20),
        plot_bgcolor='white',
        paper_bgcolor='white',
        hovermode="x unified"
    )
    
    fig.update_xaxes(showgrid=False, gridcolor='#e5e5e5')
    fig.update_yaxes(showgrid=False, gridcolor='#e5e5e5', tickformat=',.0f')
    
    if fig.data and fig.data[0].type in ['bar', 'scatter', 'line']:
        if fig.data[0].type == 'line':
            fig.update_traces(hovertemplate='Rides: %{y:,.0f}<extra></extra>')
        else:
            fig.update_traces(hovertemplate='Rides: %{y:,.0f}<extra>%{x}</extra>')

    return fig

# --- Custom Legend HTML ---
CUSTOM_LEGEND_HTML = """
    <div style="display: flex; justify-content: flex-end; align-items: center; margin-bottom: 20px;">
        <h4 style="color: #1a4d7d; margin: 0 15px 0 0; font-size: 1.1em;">Rider Types:</h4>
        <div style="display: flex; align-items: center; margin-right: 15px;">
            <span style="display: inline-block; width: 12px; height: 12px; border-radius: 50%; background-color: #1a4d7d; margin-right: 5px;"></span>
            <span style="font-weight: bold;">Member</span>
        </div>
        <div style="display: flex; align-items: center;">
            <span style="display: inline-block; width: 12px; height: 12px; border-radius: 50%; background-color: #f4a460; margin-right: 5px;"></span>
            <span style="font-weight: bold;">Casual</span>
        </div>
    </div>
"""

# ============================================================================
# MAIN APPLICATION
# ============================================================================
# def main():
#     # Load data
#     df = load_data()
    
#     if df is None:
#         st.stop()
def main():
    # Debug info
    st.write("Current working directory:", os.getcwd())
    st.write("Contents of Data/12_Months_data (if it exists):")

    if os.path.exists("Data/12_Months_data"):
        st.write(os.listdir("Data/12_Months_data"))
    else:
        st.write("Data/12_Months_data does NOT exist")

    df = load_data()

    if df is None:
        st.stop()

    # ========================================================================
    # SIDEBAR FILTERS
    # ========================================================================
    st.sidebar.markdown("## 🔧 Filters")
    
    rider_type = st.sidebar.radio(
        "👥 Rider Type",
        ["All Riders", "Member", "Casual"],
        help="Filter by membership status"
    )
    
    st.sidebar.markdown("**🌤️ Seasons**")
    seasons_options = ["Winter", "Spring", "Summer", "Fall"]
    seasons = [season for season in seasons_options if st.sidebar.checkbox(season, value=True, key=f"season_{season}")]
    if not seasons: seasons = seasons_options
    
    st.sidebar.markdown("**🚲 Bike Type**")
    bike_options = df['rideable_type'].unique().tolist()
    bike_types = [bike for bike in bike_options if st.sidebar.checkbox(bike, value=True, key=f"bike_{bike}")]
    if not bike_types: bike_types = bike_options
    
    # Apply filters
    filtered_df = filter_data(df, rider_type, seasons, bike_types)
    
    if filtered_df.empty:
        st.warning("⚠️ No data matches your filter criteria. Please adjust your selections.")
        return
    
    # ========================================================================
    # 1. HEADER & KEY METRICS
    # ========================================================================
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown('<div class="header-title">🚴 Cyclistic Bike-Share Analytics</div>', unsafe_allow_html=True)
        st.markdown("*Insights on how **annual members** and **casual riders** use Cyclistic differently*")
    st.divider()
    
    member_data = filtered_df[filtered_df['member_casual'] == 'member']
    casual_data = filtered_df[filtered_df['member_casual'] == 'casual']
    
    total_rides = len(filtered_df)
    member_rides = len(member_data)
    casual_rides = len(casual_data)
    
    member_pct = round((member_rides / total_rides) * 100) if total_rides > 0 else 0
    casual_pct = round((casual_rides / total_rides) * 100) if total_rides > 0 else 0
    member_millions = member_rides / 1_000_000
    casual_millions = casual_rides / 1_000_000
    total_millions = total_rides / 1_000_000
    avg_duration = round(filtered_df['ride_time_min'].mean())
    
    col1, col2, col3, col4 = st.columns([1.5, 1.5, 1.5, 1.5])
    
    with col1:
        st.markdown(f"""
            <div style="background: linear-gradient(135deg, #1a4d7d 0%, #2d6ba3 100%); padding: 25px; border-radius: 15px; text-align: center; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <p style="font-size: 14px; margin: 0; opacity: 0.9;">MEMBER RIDES</p>
                <h2 style="font-size: 32px; margin: 10px 0; font-weight: bold;">{member_millions:.1f}M</h2>
                <p style="font-size: 16px; margin: 0; font-weight: bold;">{member_pct}%</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
            <div style="background: linear-gradient(135deg, #f4a460 0%, #e69147 100%); padding: 25px; border-radius: 15px; text-align: center; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <p style="font-size: 14px; margin: 0; opacity: 0.9;">CASUAL RIDES</p>
                <h2 style="font-size: 32px; margin: 10px 0; font-weight: bold;">{casual_millions:.1f}M</h2>
                <p style="font-size: 16px; margin: 0; font-weight: bold;">{casual_pct}%</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
            <div style="background: linear-gradient(135deg, #34495e 0%, #2c3e50 100%); padding: 25px; border-radius: 15px; text-align: center; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <p style="font-size: 14px; margin: 0; opacity: 0.9;">TOTAL RIDES</p>
                <h2 style="font-size: 32px; margin: 10px 0; font-weight: bold;">{total_millions:.1f}M</h2>
            </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
            <div style="background: linear-gradient(135deg, #7f8c8d 0%, #95a5a6 100%); padding: 25px; border-radius: 15px; text-align: center; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <p style="font-size: 14px; margin: 0; opacity: 0.9;">AVG DURATION</p>
                <h2 style="font-size: 32px; margin: 10px 0; font-weight: bold;">{avg_duration}</h2>
                <p style="font-size: 16px; margin: 0; font-weight: bold;">minutes</p>
            </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    # ========================================================================
    # 2. MEMBER VS CASUAL COMPARISON - DONUT CHARTS
    # ========================================================================
    st.markdown('<div class="subheader">👥 Member vs Casual: Ride Volume, Duration, & Travel Time</div>', unsafe_allow_html=True)
    st.markdown(CUSTOM_LEGEND_HTML, unsafe_allow_html=True)
    
    try:
        filtered_df['hours_travelled'] = filtered_df['ride_time_min'] / 60
        col1, col2, col3 = st.columns(3)
        
        # 1. Number of Rides Donut
        with col1:
            rides_by_type = filtered_df.groupby('member_casual').size().reset_index(name='rides')
            rides_by_type['label'] = rides_by_type['member_casual'].map({'member': 'Member', 'casual': 'Casual'})
            total_rides_count = rides_by_type['rides'].sum()
            
            fig_rides = px.pie(rides_by_type, values='rides', names='label', title='Total Rides Distribution', 
                               color='label', color_discrete_map={'Member': '#1a4d7d', 'Casual': '#f4a460'}, hole=0.5)
            fig_rides.update_traces(textposition='inside', textinfo='percent', hovertemplate='%{label}: %{value:,.0f} rides<br>(%{percent})<extra></extra>')
            fig_rides = enhance_plotly_figure(fig_rides) 
            fig_rides.add_annotation(text=f"{total_rides_count:,.0f}", x=0.5, y=0.5, font_size=24, showarrow=False, font_color="#333", font_weight='bold')
            st.plotly_chart(fig_rides, use_container_width=True)
        
        # 2. Avg Trip Duration Donut
        with col2:
            duration_by_type = filtered_df.groupby('member_casual')['ride_time_min'].mean().round(0).reset_index()
            duration_by_type['label'] = duration_by_type['member_casual'].map({'member': 'Member', 'casual': 'Casual'})
            duration_by_type.columns = ['member_casual', 'avg_duration', 'label']
            total_avg_duration = round(filtered_df['ride_time_min'].mean())
            
            fig_duration = px.pie(duration_by_type, values='avg_duration', names='label', title='Average Trip Duration (min)', 
                                color='label', color_discrete_map={'Member': '#1a4d7d', 'Casual': '#f4a460'}, hole=0.5)
            fig_duration.update_traces(textposition='inside', textinfo='percent', hovertemplate='%{label}: %{value:,.0f} min<br>(%{percent})<extra></extra>')
            fig_duration = enhance_plotly_figure(fig_duration)
            fig_duration.add_annotation(text=f"{total_avg_duration:,.0f}m", x=0.5, y=0.5, font_size=24, showarrow=False, font_color="#333", font_weight='bold')
            st.plotly_chart(fig_duration, use_container_width=True)
        
        # 3. Total Hours Travelled Donut
        with col3:
            hours_by_type = filtered_df.groupby('member_casual')['hours_travelled'].sum().reset_index()
            hours_by_type['label'] = hours_by_type['member_casual'].map({'member': 'Member', 'casual': 'Casual'})
            hours_by_type.columns = ['member_casual', 'total_hours', 'label']
            total_hours_count = hours_by_type['total_hours'].sum()
            
            fig_hours = px.pie(hours_by_type, values='total_hours', names='label', title='Total Hours Travelled', 
                            color='label', color_discrete_map={'Member': '#1a4d7d', 'Casual': '#f4a460'}, hole=0.5)
            fig_hours.update_traces(textposition='inside', textinfo='percent', hovertemplate='%{label}: %{value:,.0f} hours<br>(%{percent})<extra></extra>')
            fig_hours = enhance_plotly_figure(fig_hours)
            fig_hours.add_annotation(text=f"{total_hours_count:,.0f}", x=0.5, y=0.5, font_size=24, showarrow=False, font_color="#333", font_weight='bold')
            st.plotly_chart(fig_hours, use_container_width=True)
        
    except Exception as e:
        st.error(f"❌ Error creating comparison charts: {str(e)}")
    
    st.divider()
    
    # ========================================================================
    # 3. USAGE PATTERNS (Monthly & Hourly)
    # ========================================================================
    st.markdown('<div class="subheader">📈 Usage Patterns: Monthly & Hourly Trends</div>', unsafe_allow_html=True)
    st.markdown(CUSTOM_LEGEND_HTML, unsafe_allow_html=True)
    
    try:
        col1, col2 = st.columns(2)
        color_map = {'member': '#1a4d7d', 'casual': '#f4a460'}
        is_all_riders = rider_type == "All Riders"
        current_color = color_map[rider_type.lower()] if not is_all_riders else None
        
        # Monthly trends
        with col1:
            monthly_data = filtered_df.groupby(['month_year', 'member_casual']).size().reset_index(name='rides')
            monthly_data['sort_key'] = pd.to_datetime(monthly_data['month_year'], format='%Y-%m')
            monthly_data = monthly_data.sort_values('sort_key').drop('sort_key', axis=1)
            
            if not is_all_riders:
                monthly_data = monthly_data[monthly_data['member_casual'] == rider_type.lower()]
            
            fig_monthly = px.line(monthly_data, x='month_year', y='rides', 
                                color='member_casual' if is_all_riders else None,
                                title='Monthly Ride Trends', labels={'rides': 'Number of Rides', 'month_year': 'Month'},
                                markers=True, 
                                color_discrete_map=color_map if is_all_riders else None)
            
            if not is_all_riders and fig_monthly.data:
                fig_monthly.data[0].marker.color = current_color
                fig_monthly.data[0].line.color = current_color

            fig_monthly = enhance_plotly_figure(fig_monthly, show_legend=False)
            st.plotly_chart(fig_monthly, use_container_width=True)
        
        # Hourly distribution
        with col2:
            hourly_data = filtered_df.groupby(['hour', 'member_casual']).size().reset_index(name='rides')
            hourly_data = hourly_data.sort_values('hour')
            hourly_data['time_label'] = hourly_data['hour'].apply(lambda x: f"{x % 12 or 12}:00 {'AM' if x < 12 else 'PM'}")
            
            if not is_all_riders:
                hourly_data = hourly_data[hourly_data['member_casual'] == rider_type.lower()]

            fig_hourly = px.bar(hourly_data, x='time_label', y='rides', 
                                color='member_casual' if is_all_riders else None, 
                                barmode='group' if is_all_riders else 'relative',
                                title='Hourly Ride Distribution (Commute vs. Leisure Peaks)', 
                                labels={'rides': 'Number of Rides', 'time_label': 'Time of Day'},
                                color_discrete_map=color_map if is_all_riders else None)
            
            if not is_all_riders:
                fig_hourly.update_traces(marker_color=current_color)
            
            fig_hourly = enhance_plotly_figure(fig_hourly)
            fig_hourly.update_traces(hovertemplate='Time: %{x}<br>Rides: %{y:,.0f}<extra></extra>')
            fig_hourly.update_xaxes(tickangle=-45)

            st.plotly_chart(fig_hourly, use_container_width=True)
        
    except Exception as e:
        st.error(f"❌ Error creating usage pattern charts: {str(e)}")
    
    st.divider()
    
    # ========================================================================
    # 4. WEEKDAY & SEASONAL BREAKDOWN
    # ========================================================================
    st.markdown('<div class="subheader">📅 Weekday & Seasonal Breakdown (Weekly Commute Cycle vs. Seasonal Peaks)</div>', unsafe_allow_html=True)
    st.markdown(CUSTOM_LEGEND_HTML, unsafe_allow_html=True)
    
    try:
        col1, col2 = st.columns(2)
        
        # Weekday analysis
        with col1:
            weekday_order = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
            weekday_data = filtered_df.groupby(['weekday', 'member_casual']).size().reset_index(name='rides')
            
            if not is_all_riders:
                weekday_data = weekday_data[weekday_data['member_casual'] == rider_type.lower()]
            
            weekday_data['weekday'] = pd.Categorical(weekday_data['weekday'], categories=weekday_order, ordered=True)
            weekday_data = weekday_data.sort_values('weekday')
            
            fig_weekday = px.bar(weekday_data, x='weekday', y='rides', 
                                color='member_casual' if is_all_riders else None, 
                                barmode='group' if is_all_riders else 'relative',
                                title='Rides by Weekday', 
                                labels={'rides': 'Number of Rides', 'weekday': 'Day of Week'},
                                color_discrete_map=color_map if is_all_riders else None)
            
            if not is_all_riders:
                fig_weekday.update_traces(marker_color=current_color)
            
            fig_weekday = enhance_plotly_figure(fig_weekday)
            fig_weekday.update_traces(hovertemplate='Day: %{x}<br>Rides: %{y:,.0f}<extra></extra>')

            st.plotly_chart(fig_weekday, use_container_width=True)
        
        # Seasonal analysis
        with col2:
            season_order = ['Winter', 'Spring', 'Summer', 'Fall']
            season_data = filtered_df.groupby(['season', 'member_casual']).size().reset_index(name='rides')
            
            if not is_all_riders:
                season_data = season_data[season_data['member_casual'] == rider_type.lower()]
            
            season_data['season'] = pd.Categorical(season_data['season'], categories=season_order, ordered=True)
            season_data = season_data.sort_values('season')
            
            fig_season = px.bar(season_data, x='season', y='rides', 
                                color='member_casual' if is_all_riders else None, 
                                barmode='group' if is_all_riders else 'relative',
                                title='Rides by Season', 
                                labels={'rides': 'Number of Rides', 'season': 'Season'},
                                color_discrete_map=color_map if is_all_riders else None)
            
            if not is_all_riders:
                fig_season.update_traces(marker_color=current_color)
            
            fig_season = enhance_plotly_figure(fig_season)
            fig_season.update_traces(hovertemplate='Season: %{x}<br>Rides: %{y:,.0f}<extra></extra>')

            st.plotly_chart(fig_season, use_container_width=True)
        
    except Exception as e:
        st.error(f"❌ Error creating temporal analysis charts: {str(e)}")
    
    st.divider()

    # ========================================================================
    # 5. BIKE TYPE PREFERENCES
    # ========================================================================
    st.markdown('<div class="subheader">🚲 Bike Type Preferences</div>', unsafe_allow_html=True)
    st.markdown(CUSTOM_LEGEND_HTML, unsafe_allow_html=True)
    
    try:
        bike_data = filtered_df.groupby(['rideable_type', 'member_casual']).size().reset_index(name='rides')
        
        if not is_all_riders:
            bike_data = bike_data[bike_data['member_casual'] == rider_type.lower()]
            color_param, barmode_param, color_map_param = None, 'relative', None
        else:
            color_param, barmode_param, color_map_param = 'member_casual', 'group', color_map

        fig_bike = px.bar(bike_data, x='rideable_type', y='rides', color=color_param, barmode=barmode_param,
                          title='Bike Type Usage by Rider Type', 
                          labels={'rides': 'Number of Rides', 'rideable_type': 'Bike Type'},
                          color_discrete_map=color_map_param)
        
        if not is_all_riders:
            fig_bike.update_traces(marker_color=current_color)
            
        fig_bike = enhance_plotly_figure(fig_bike)
        fig_bike.update_traces(hovertemplate='Type: %{x}<br>Rides: %{y:,.0f}<extra></extra>')
        
        st.plotly_chart(fig_bike, use_container_width=True)
    except Exception as e:
        st.error(f"❌ Error creating bike type chart: {str(e)}")
    
    st.divider()
    
    # ========================================================================
    # 6. GEOGRAPHIC LOCATIONS: STARTING STATIONS MAP
    # ========================================================================
    st.markdown('<div class="subheader">🗺️ Geographic Analysis: Primary Starting Stations</div>', unsafe_allow_html=True)

    try:
        col1, col2 = st.columns([1, 2])
        
        # Get all start station data based on current filters
        all_start_stats = filtered_df.groupby(['start_station_name']).agg(
            Trips=('ride_id', 'count'),
            Lat=('start_lat', 'first'),
            Lng=('start_lng', 'first'),
            Member_Trips=('member_casual', lambda x: (x.astype(str).str.strip().str.lower() == 'member').sum()),
            Casual_Trips=('member_casual', lambda x: (x.astype(str).str.strip().str.lower() == 'casual').sum())
        ).reset_index().rename(columns={'start_station_name': 'Station Name'})
        
        all_start_stats['Dominant Rider'] = np.where(all_start_stats['Member_Trips'] > all_start_stats['Casual_Trips'], 'Member', 'Casual')
        
        # Filter for top 50 unique stations by total trips for manageable display
        top_stations_for_map = all_start_stats.nlargest(50, 'Trips')
        
        if top_stations_for_map.empty:
            st.info("No starting station data available for mapping under current filters.")
        else:
            # Map generation
            avg_lat = top_stations_for_map['Lat'].mean()
            avg_lng = top_stations_for_map['Lng'].mean()
            max_rides = top_stations_for_map['Trips'].max()
            
            map_start = folium.Map(location=[avg_lat, avg_lng], zoom_start=12, tiles='OpenStreetMap')
            
            for idx, row in top_stations_for_map.iterrows():
                rider_type = row['Dominant Rider']
                color = '#1a4d7d' if rider_type == 'Member' else '#f4a460'
                
                # Scale marker radius by trip volume
                radius = 5 + (row['Trips'] / max_rides * 15) if max_rides > 0 else 5
                
                popup_html = f"""
                <b>{row['Station Name']}</b><br>
                Total Rides: {row['Trips']:,.0f}<br>
                Dominant: {rider_type}<br>
                Member: {row['Member_Trips']:,.0f}<br>
                Casual: {row['Casual_Trips']:,.0f}
                """
                
                folium.CircleMarker(
                    location=[row['Lat'], row['Lng']], 
                    radius=radius,
                    popup=folium.Popup(popup_html, max_width=300),
                    color=color, fill=True, fillColor=color, fillOpacity=0.7
                ).add_to(map_start)
            
            st_folium(map_start, width=900, height=500)

    except Exception as e:
        st.error(f"❌ Error creating map: {str(e)}")
    
    st.divider()

    # ========================================================================
    # 7. TOP 20 STATIONS & ROUTES TABLES
    # ========================================================================
    st.markdown('<div class="subheader">⭐ Top 20 Stations: Commute vs. Leisure Focus</div>', unsafe_allow_html=True)
    
    try:
        # Get overall start station stats
        all_start_stats_full = filtered_df.groupby(['start_station_name']).agg(
            Trips=('ride_id', 'count'),
            Avg_Duration=('ride_time_min', 'mean'),
            Member_Trips=('member_casual', lambda x: (x.astype(str).str.strip().str.lower() == 'member').sum()),
            Casual_Trips=('member_casual', lambda x: (x.astype(str).str.strip().str.lower() == 'casual').sum())
        ).reset_index().rename(columns={'start_station_name': 'Station Name', 'Avg_Duration': 'Avg Duration'})
        
        all_start_stats_full['Avg Duration'] = all_start_stats_full['Avg Duration'].round(0).astype(int)
        
        # 1. Member-Dominant Stations
        member_dominant = all_start_stats_full.sort_values('Member_Trips', ascending=False).head(20)
        member_dominant['Dominance'] = 'Member'
        
        # 2. Casual-Dominant Stations
        casual_dominant = all_start_stats_full.sort_values('Casual_Trips', ascending=False).head(20)
        casual_dominant['Dominance'] = 'Casual'
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Top 20 Member-Focused Starting Stations**")
            member_table = member_dominant[['Station Name', 'Trips', 'Member_Trips', 'Casual_Trips', 'Avg Duration']].copy()
            member_table.columns = ['Station Name', 'Total Trips', 'Member Trips', 'Casual Trips', 'Avg Duration (min)']
            st.dataframe(member_table, use_container_width=True, hide_index=True)
        
        with col2:
            st.markdown("**Top 20 Casual-Focused Starting Stations**")
            casual_table = casual_dominant[['Station Name', 'Trips', 'Member_Trips', 'Casual_Trips', 'Avg Duration']].copy()
            casual_table.columns = ['Station Name', 'Total Trips', 'Member Trips', 'Casual Trips', 'Avg Duration (min)']
            st.dataframe(casual_table, use_container_width=True, hide_index=True)
        
    except Exception as e:
        st.error(f"❌ Error creating station analysis tables: {str(e)}")
    
    st.divider()
    
    # Top 20 Routes Table
    st.markdown('<div class="subheader">🛣️ Top 20 Popular Routes (All Riders)</div>', unsafe_allow_html=True)
    
    try:
        st.markdown("**Top 20 Popular Routes (Start → End) based on current filters**")
        routes = query_top_routes(filtered_df, n=20)
        
        st.dataframe(
            routes[['Start Station', 'End Station', 'Trips', 'Member Trips', 'Casual Trips', 'Avg Duration']], 
            use_container_width=True, hide_index=True
        )
        
    except Exception as e:
        st.error(f"❌ Error creating route analysis: {str(e)}")
    
    st.divider()
    
    # ========================================================================
    # 8. HOLIDAY RIDE PATTERNS ANALYSIS
    # ========================================================================
    st.markdown('<div class="subheader">🎄 Holiday Ride Patterns Analysis</div>', unsafe_allow_html=True)
    
    try:
        holiday_stats = query_holiday_stats(df)
        
        if not holiday_stats.empty:
            st.markdown("**Holiday vs Regular Day Comparison**")
            
            holiday_display = holiday_stats[['holiday_name', 'total_rides', 'member_rides', 'casual_rides', 'member_pct', 'casual_pct', 'avg_member_duration', 'avg_casual_duration']].copy()
            holiday_display.columns = ['Holiday', 'Total Rides', 'Member Rides', 'Casual Rides', 'Member %', 'Casual %', 'Member Avg (min)', 'Casual Avg (min)']
            st.dataframe(holiday_display, use_container_width=True, hide_index=True)
            
            if len(holiday_stats) > 0:
                fig_holiday = px.bar(holiday_stats, x='holiday_name', y=['member_rides', 'casual_rides'],
                                     barmode='group', title='Member vs Casual Rides by Holiday',
                                     labels={'value': 'Rides', 'holiday_name': 'Holiday', 'variable': 'Rider Type'},
                                     color_discrete_map={'member_rides': '#1a4d7d', 'casual_rides': '#f4a460'})
                
                new_names = {'member_rides': 'Member', 'casual_rides': 'Casual'}
                fig_holiday.for_each_trace(lambda t: t.update(name = new_names[t.name], legendgroup = new_names[t.name], hovertemplate = t.hovertemplate.replace(t.name, new_names[t.name])))

                fig_holiday = enhance_plotly_figure(fig_holiday, show_legend=True, x_anchor='right', y_anchor='top', x_pos=1, y_pos=1)
                fig_holiday.update_xaxes(tickangle=-45)
                st.plotly_chart(fig_holiday, use_container_width=True)
        else:
            st.info("ℹ️ No holiday ride data available in the dataset.")
    
    except Exception as e:
        st.error(f"❌ Error creating holiday analysis: {str(e)}")
    
    st.divider()

    # ========================================================================
    # 9. INSIGHTS & RECOMMENDATIONS
    # ========================================================================
    st.markdown('<div class="subheader">💡 Key Insights & Strategic Recommendations</div>', unsafe_allow_html=True)
    
    try:
        member_data = filtered_df[filtered_df['member_casual'] == 'member']
        casual_data = filtered_df[filtered_df['member_casual'] == 'casual']
        
        member_pct = (len(member_data) / len(filtered_df)) * 100 if len(filtered_df) > 0 else 0
        casual_pct = (len(casual_data) / len(filtered_df)) * 100 if len(filtered_df) > 0 else 0
        member_avg_duration = member_data['ride_time_min'].mean() if not member_data.empty else 0
        casual_avg_duration = casual_data['ride_time_min'].mean() if not casual_data.empty else 0
        duration_diff = ((casual_avg_duration - member_avg_duration) / member_avg_duration) * 100 if member_avg_duration > 0 else 0
        
        member_weekend = filtered_df[(filtered_df['member_casual'] == 'member') & (filtered_df['weekday'].isin(['Sat', 'Sun']))].shape[0]
        casual_weekend = filtered_df[(filtered_df['member_casual'] == 'casual') & (filtered_df['weekday'].isin(['Sat', 'Sun']))].shape[0]
        
        member_weekend_pct = (member_weekend / len(member_data)) * 100 if len(member_data) > 0 else 0
        casual_weekend_pct = (casual_weekend / len(casual_data)) * 100 if len(casual_data) > 0 else 0
        
        holiday_stats = query_holiday_stats(df)
        holiday_insights = ""
        if not holiday_stats.empty:
            avg_holiday_member_pct = holiday_stats['member_pct'].mean()
            avg_holiday_casual_pct = holiday_stats['casual_pct'].mean()
            holiday_insights = f"Holiday analysis reveals members account for **{avg_holiday_member_pct:.0f}%** of holiday rides, while casual riders represent **{avg_holiday_casual_pct:.0f}**%. "
            
        with st.expander("📋 Detailed Findings", expanded=True):
            findings = [
                f"🔵 **Customer Mix:** Members represent **{member_pct:.0f}%** of rides, while casual riders account for **{casual_pct:.0f}**% (based on current filters).",
                f"⏱️ **Trip Duration:** Casual riders take **{casual_avg_duration:.0f} min** trips, which is **{duration_diff:.0f}% longer** than member trips ({member_avg_duration:.0f} min), indicating a more leisure-focused use case for casual riders.",
                f"📅 **Weekend Usage:** Casual riders have a much higher concentration of usage on weekends (**{casual_weekend_pct:.0f}%** of their trips are weekends) compared to members (**{member_weekend_pct:.0f}%** of their trips are weekends).",
                f"🕗 **Time-of-Day:** Peak member usage occurs during standard **commute hours** (7-9 AM, 5-7 PM). Casual riders peak later in the day, aligning with leisure and tourism.",
                f"🎉 **Holiday Pattern:** {holiday_insights}This suggests members maintain routine usage, while casual riders show significant engagement on specific holidays.",
                f"📍 **Geographic Focus:** Top starting stations differ significantly; members cluster in **commute corridors** while casual riders prefer **leisure destinations** (as confirmed by the map and tables)."
            ]
            
            for finding in findings:
                st.markdown(f"• {finding}")
        
        with st.expander("🎯 Strategic Recommendations", expanded=True):
            recommendations = [
                {
                    'title': '1. Time-Based Membership Tiers',
                    'description': 'Introduce flexible membership tiers: (a) Peak-hour commuter pass for members (lower cost, limited hours), (b) Weekend/Leisure pass for casual riders, priced to capture the value of their long, weekend trips. This aligns pricing with usage behavior.'
                },
                {
                    'title': '2. High-Value Conversion Promotions',
                    'description': 'Launch aggressive, limited-time promotions during **peak season (Summer)** and **high-casual holidays** (e.g., Independence Day). Offer a "Summer Pass" that automatically converts to an annual membership discount after 3 months, or a "Holiday Explorer" bundle.'
                },
                {
                    'title': '3. Destination-Based Incentives',
                    'description': 'Partner with attractions, restaurants, and entertainment venues near top casual stations and routes. Offer membership sign-up benefits (e.g., free coffee coupon, attraction discount) directly at these high-traffic leisure locations.'
                },
                {
                    'title': '4. Duration-Incentive Program for Conversion',
                    'description': 'Target casual riders who take long trips with a message like: "Stop paying high fees for long rides—members ride for one low annual price." Introduce a *reduced rate* for member trips over 30 minutes to solidify loyalty against the higher cost structure for casual riders.'
                },
                {
                    'title': '5. Geographic and Inventory Optimization',
                    'description': 'Use geographic and holiday data to pre-position bikes at high-casual-use stations (especially on weekends and holidays) and ensure adequate supply at key commute stations during weekday peak hours. This maximizes utilization and customer satisfaction for both segments.'
                }
            ]
            
            for rec in recommendations:
                st.markdown(f"**{rec['title']}**")
                st.markdown(f"{rec['description']}")
                st.markdown("---")
    
    except Exception as e:
        st.error(f"❌ Error generating insights: {str(e)}")
    
    st.divider()
    
    # ============================================================================
    # 10. FOOTER
    # ============================================================================
    st.divider()
    st.markdown("""
        <div style="text-align: center; color: #999; font-size: 0.9em; margin-top: 2rem;">
            <p>Cyclistic Bike-Share Analytics Dashboard | Google Data Analytics Capstone Project</p>
            <p>Data powered by Divvy | Last updated: {}</p>
        </div>
    """.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')), unsafe_allow_html=True)


# ============================================================================
# RUN APPLICATION
# ============================================================================
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # This ensures the app doesn't hard-crash on startup
        st.error(f"🚨 Unhandled error in app: {e}")
        st.exception(e)
