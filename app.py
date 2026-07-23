import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px

# -------------------------------------------------------------
# PAGE CONFIGURATION & CUSTOM STYLING
# -------------------------------------------------------------
st.set_page_config(
    page_title="Tennis Analytics Dashboard",
    page_icon="🎾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS targeting all sidebar elements
st.markdown("""
<style>
    /* Main Background */
    .main {
        background-color: #f8f9fa;
    }
    
    /* Sidebar Background */
    section[data-testid="stSidebar"] {
        background-color: #1e222d !important;
    }
    
    /* FORCE ALL SIDEBAR TEXT TO WHITE */
    section[data-testid="stSidebar"] *, 
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] div {
        color: #ffffff !important;
    }

    /* Selected Radio Option Highlight */
    div[data-testid="stRadio"] label[data-baseweb="radio"] {
        background-color: rgba(255, 255, 255, 0.05);
        border-radius: 8px;
        padding: 6px 10px;
        margin-bottom: 4px;
        transition: all 0.2s ease-in-out;
    }
    
    div[data-testid="stRadio"] label[data-baseweb="radio"]:hover {
        background-color: rgba(255, 255, 255, 0.15);
    }

    /* Metric Cards Styling */
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        border-radius: 12px;
        padding: 18px 22px;
        box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.05);
        border: 1px solid #e9ecef;
    }
    
    div[data-testid="stMetricLabel"] {
        font-weight: 600;
        color: #6c757d !important;
    }
    
    div[data-testid="stMetricValue"] {
        font-weight: 700;
        color: #0f172a !important;
    }
</style>
""", unsafe_allow_html=True)

# Helper function to execute SQLite queries
def run_query(query):
    conn = sqlite3.connect("tennis_analytics.db")
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# -------------------------------------------------------------
# SIDEBAR NAVIGATION (Redesigned)
# -------------------------------------------------------------
with st.sidebar:
    st.image("https://img.icons8.com/color/96/tennis.png", width=64)
    st.title("SportRadar Analytics")
    st.caption("🎾 Tennis Data Explorer v1.0")
    st.markdown("---")
    
    # Styled selectbox / navigation options
    menu_options = [
        "📊 Executive Summary", 
        "🏆 Competitions", 
        "📍 Venues & Complexes", 
        "🎾 Competitors & Leaderboard", 
        "🌐 Country Performance", 
        "💻 SQL Query Console"
    ]
    
    selected_view = st.radio(
        "NAVIGATION", 
        menu_options,
        index=0
    )
    
    st.markdown("---")
    st.caption("Developed with Streamlit & SQLite")

# -------------------------------------------------------------
# 1. EXECUTIVE SUMMARY DASHBOARD
# -------------------------------------------------------------
if selected_view == "📊 Executive Summary":
    st.title("🏆 Executive Summary Dashboard")
    st.markdown("Real-time high-level statistics and key performance indicators.")
    st.markdown("---")
    
    # KPI Metrics Row
    m1, m2, m3, m4 = st.columns(4)
    
    total_comps = run_query("SELECT COUNT(*) as count FROM Competitors")['count'][0]
    total_countries = run_query("SELECT COUNT(DISTINCT country) as count FROM Competitors")['count'][0]
    max_pts = run_query("SELECT MAX(points) as max_pts FROM Competitor_Rankings")['max_pts'][0]
    total_venues = run_query("SELECT COUNT(*) as count FROM Venues")['count'][0]
    
    m1.metric("Total Competitors", f"{total_comps:,}" if total_comps else "0")
    m2.metric("Countries Represented", f"{total_countries:,}" if total_countries else "0")
    m3.metric("Highest Points Scored", f"{max_pts:,}" if max_pts else "0")
    m4.metric("Venues Tracked", f"{total_venues:,}" if total_venues else "0")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Charts Section
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.subheader("Top 10 Competitors by Points")
        top_df = run_query("""
            SELECT c.name, r.rank, r.points 
            FROM Competitors c 
            JOIN Competitor_Rankings r ON c.competitor_id = r.competitor_id 
            ORDER BY r.points DESC LIMIT 10
        """)
        fig_bar = px.bar(
            top_df, 
            x="points", 
            y="name", 
            orientation='h',
            color="points", 
            labels={"name": "Competitor", "points": "Total Points"},
            color_continuous_scale="Blues"
        )
        fig_bar.update_layout(yaxis={'categoryorder':'total ascending'}, margin=dict(l=0, r=0, t=20, b=0))
        st.plotly_chart(fig_bar, use_container_width=True)
        
    with col_chart2:
        st.subheader("Competitions Distribution by Gender")
        gender_df = run_query("""
            SELECT gender, COUNT(*) as count 
            FROM Competitions 
            GROUP BY gender
        """)
        fig_pie = px.pie(
            gender_df, 
            names="gender", 
            values="count", 
            hole=0.45,
            color_discrete_sequence=px.colors.qualitative.Set2
        )
        fig_pie.update_layout(margin=dict(l=0, r=0, t=20, b=0))
        st.plotly_chart(fig_pie, use_container_width=True)

# -------------------------------------------------------------
# 2. COMPETITIONS
# -------------------------------------------------------------
elif selected_view == "🏆 Competitions":
    st.title("🏆 Competition Hierarchies & Categories")
    st.markdown("Filter and inspect tournament categories and formats.")
    st.markdown("---")
    
    c_f1, c_f2 = st.columns(2)
    with c_f1:
        type_list = ["All"] + list(run_query("SELECT DISTINCT type FROM Competitions")['type'])
        type_filter = st.selectbox("Filter by Competition Type:", type_list)
    with c_f2:
        gender_list = ["All"] + list(run_query("SELECT DISTINCT gender FROM Competitions")['gender'])
        gender_filter = st.selectbox("Filter by Gender:", gender_list)
    
    query = """
        SELECT c.competition_name AS "Competition Name", c.type AS "Type", c.gender AS "Gender", 
               cat.category_name AS "Category Name", c.parent_id AS "Parent ID"
        FROM Competitions c
        LEFT JOIN Categories cat ON c.category_id = cat.category_id
        WHERE 1=1
    """
    if type_filter != "All":
        query += f" AND c.type = '{type_filter}'"
    if gender_filter != "All":
        query += f" AND c.gender = '{gender_filter}'"
        
    comp_data = run_query(query)
    st.write(f"Showing **{len(comp_data)}** records")
    st.dataframe(comp_data, use_container_width=True, height=450)

# -------------------------------------------------------------
# 3. VENUES & COMPLEXES
# -------------------------------------------------------------
elif selected_view == "📍 Venues & Complexes":
    st.title("📍 Sports Complexes & Venue Locations")
    st.markdown("---")
    
    countries = ["All"] + sorted(list(run_query("SELECT DISTINCT country_name FROM Venues")['country_name']))
    selected_country = st.selectbox("Select Country:", countries)
    
    v_query = """
        SELECT v.venue_name AS "Venue Name", v.city_name AS "City", 
               v.country_name AS "Country", v.timezone AS "Timezone", 
               c.complex_name AS "Complex Name"
        FROM Venues v
        LEFT JOIN Complexes c ON v.complex_id = c.complex_id
    """
    if selected_country != "All":
        v_query += f" WHERE v.country_name = '{selected_country}'"
        
    venues_df = run_query(v_query)
    st.dataframe(venues_df, use_container_width=True, height=450)

# -------------------------------------------------------------
# 4. COMPETITORS & LEADERBOARD
# -------------------------------------------------------------
elif selected_view == "🎾 Competitors & Leaderboard":
    st.title("🎾 Competitor Search & Leaderboard")
    st.markdown("---")
    
    f1, f2 = st.columns([2, 1])
    with f1:
        search_term = st.text_input("🔍 Search competitor by name:", "")
    with f2:
        max_r = run_query("SELECT MAX(rank) FROM Competitor_Rankings")['MAX(rank)'][0]
        rank_range = st.slider("Filter Rank Range:", 1, int(max_r) if max_r else 100, (1, 50))
    
    search_q = f"""
        SELECT c.name AS "Competitor Name", c.country AS "Country", c.abbreviation AS "Abbr", 
               r.rank AS "Rank", r.movement AS "Movement", r.points AS "Points", 
               r.competitions_played AS "Competitions Played"
        FROM Competitors c
        JOIN Competitor_Rankings r ON c.competitor_id = r.competitor_id
        WHERE r.rank BETWEEN {rank_range[0]} AND {rank_range[1]}
    """
    if search_term:
        search_q += f" AND c.name LIKE '%{search_term}%'"
        
    search_q += " ORDER BY r.rank ASC"
    
    comp_results = run_query(search_q)
    st.dataframe(comp_results, use_container_width=True, height=450)

# -------------------------------------------------------------
# 5. COUNTRY PERFORMANCE
# -------------------------------------------------------------
elif selected_view == "🌐 Country Performance":
    st.title("🌐 Country-Wise Aggregations")
    st.markdown("---")
    
    country_df = run_query("""
        SELECT c.country AS "Country", COUNT(c.competitor_id) AS "Total Competitors", 
               ROUND(AVG(r.points), 2) AS "Average Points", SUM(r.points) AS "Total Points"
        FROM Competitors c
        JOIN Competitor_Rankings r ON c.competitor_id = r.competitor_id
        GROUP BY c.country
        ORDER BY "Total Points" DESC
    """)
    
    st.dataframe(country_df, use_container_width=True, height=450)

# -------------------------------------------------------------
# 6. SQL CONSOLE
# -------------------------------------------------------------
elif selected_view == "💻 SQL Query Console":
    st.title("💻 SQL Query Console")
    st.markdown("Run custom query statements directly against `tennis_analytics.db`.")
    st.markdown("---")
    
    default_sql = "SELECT c.competition_name, cat.category_name FROM Competitions c JOIN Categories cat ON c.category_id = cat.category_id LIMIT 10;"
    user_query = st.text_area("Write SQL Query:", value=default_sql, height=120)
    
    if st.button("Execute Query", type="primary"):
        try:
            res = run_query(user_query)
            st.success(f"Execution successful! Returned {len(res)} rows.")
            st.dataframe(res, use_container_width=True)
        except Exception as e:
            st.error(f"SQL Execution Error: {e}")