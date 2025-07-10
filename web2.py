import streamlit as st
import pandas as pd
import mysql.connector
import plotly.express as px

# ---------- DB CONNECTION ----------
def get_connection():
    return mysql.connector.connect(
        host="127.0.0.1",
        user="root",
        password="Root@123",
        database="tennis_data"
    )

# ---------- DATA FETCHING ----------
@st.cache_data
def run_query(query):
    try:
        conn = get_connection()
        df = pd.read_sql(query, conn)
    except Exception as e:
        st.error(f"Error while running query: {e}")
        df = pd.DataFrame()
    finally:
        if conn.is_connected():
            conn.close()
    return df

# ---------- STREAMLIT UI ----------
st.set_page_config(page_title="Tennis Data Dashboard", layout="wide")
st.title("🎾 Tennis Data Dashboard")

# ---------- NAVIGATION ----------
section = st.sidebar.selectbox("Choose a Section", [
    "🏠 Home", "Competitions", "Venues & Complexes", 
    "Competitor Rankings", "🔍 Search Competitors", 
    "👤 Competitor Details", "🌐 Country-Wise Analysis", 
    "🏆 Leaderboards"
])

# ---------- HOMEPAGE DASHBOARD ----------
if section == "🏠 Home":
    st.header("🏠 Tennis game Overview")

    col1, col2, col3 = st.columns(3)

    df_total = run_query("SELECT COUNT(*) AS total FROM competitors")
    col1.metric("Total Competitors", df_total['total'][0])

    df_countries = run_query("SELECT COUNT(DISTINCT country) AS countries FROM competitors")
    col2.metric("Countries Represented", df_countries['countries'][0])

    df_max_points = run_query("SELECT MAX(points) AS highest_points FROM competitor_rankings")
    col3.metric("Highest Points", df_max_points['highest_points'][0])

# ---------- SEARCH COMPETITORS ----------
elif section == "🔍 Search Competitors":
    st.header("🔍 Search and Filter Competitors")

    name = st.text_input("Search by Name")
    min_rank, max_rank = st.slider("Rank Range", 1, 500, (1, 50))
    country_df = run_query("SELECT DISTINCT country FROM competitors ORDER BY country")
    country = st.selectbox("Select Country", country_df['country'])

    query = f"""
        SELECT ct.name, ct.country, cr.rank, cr.points
        FROM competitors ct
        LEFT JOIN competitor_rankings cr ON cr.competitor_id = ct.competitor_id
        WHERE ct.name LIKE '%{name}%' 
        AND cr.rank BETWEEN {min_rank} AND {max_rank}
        AND ct.country = '{country}'
        ORDER BY cr.rank
    """
    df = run_query(query)
    st.dataframe(df)

# ---------- COMPETITOR DETAILS ----------
elif section == "👤 Competitor Details":
    st.header("👤 View Competitor Details")

    competitors = run_query("SELECT DISTINCT name FROM competitors ORDER BY name")
    selected_name = st.selectbox("Choose a Competitor", competitors['name'])

    df_details = run_query(f"""
        SELECT ct.name, ct.country, cr.rank, cr.movement, cr.points, cr.competitions_played
        FROM competitors ct
        LEFT JOIN competitor_rankings cr ON cr.competitor_id = ct.competitor_id
        WHERE ct.name = '{selected_name}'
    """)
    st.table(df_details)

# ---------- COUNTRY-WISE ANALYSIS ----------
elif section == "🌐 Country-Wise Analysis":
    st.header("🌐 Competitor Distribution by Country")

    df_country = run_query("""
        SELECT ct.country, COUNT(*) AS total_competitors, AVG(cr.points) AS average_points
        FROM competitors ct
        LEFT JOIN competitor_rankings cr ON ct.competitor_id = cr.competitor_id
        GROUP BY ct.country
        ORDER BY total_competitors DESC;
    """)
    st.dataframe(df_country)

    fig = px.bar(df_country.head(10), x='country', y='total_competitors',
                 title="Top 10 Countries by Competitor Count")
    st.plotly_chart(fig, use_container_width=True)

# ---------- LEADERBOARDS ----------
elif section == "🏆 Leaderboards":
    st.header("🏆 Competitor Leaderboards")

    st.subheader("Top 10 by Rank")
    df_rank = run_query("""
        SELECT ct.name, cr.rank, cr.points
        FROM competitors ct
        LEFT JOIN competitor_rankings cr ON ct.competitor_id = cr.competitor_id
        ORDER BY cr.rank ASC
        LIMIT 10;
    """)
    st.dataframe(df_rank)

    st.subheader("Top 10 by Points")
    df_points = run_query("""
        SELECT ct.name, cr.points
        FROM competitors ct
        LEFT JOIN competitor_rankings cr ON ct.competitor_id = cr.competitor_id
        ORDER BY cr.points DESC
        LIMIT 10;
    """)
    st.dataframe(df_points)

# ---------- COMPETITIONS SECTION ----------
elif section == "Competitions":
    st.header("📅 Competitions Overview")

    df1 = run_query("""
        SELECT cp.competition_id AS competition_id, cp.competition_name AS competition_name, c.category_name AS category_name 
        FROM competition cp LEFT JOIN category c ON c.category_id = cp.category_id;
    """)
    st.subheader("All Competitions with Category")
    st.dataframe(df1)

    df2 = run_query("""
        SELECT c.category_name AS category, COUNT(cp.competition_name) AS competitions 
        FROM competition cp 
        LEFT JOIN category c ON c.category_id = cp.category_id 
        GROUP BY c.category_name;
    """)
    st.subheader("Competitions Count per Category")
    st.dataframe(df2)

    df3 = run_query("SELECT * FROM competition WHERE type = 'doubles'")
    st.subheader("Doubles Competitions")
    st.dataframe(df3)

# ---------- VENUES & COMPLEXES SECTION ----------
elif section == "Venues & Complexes":
    st.header("🏟️ Venues & Complexes Overview")

    df1 = run_query("""
        SELECT v.venue_name, cm.complex_name from venues v LEFT JOIN complex cm on v.complex_id = cm.complex_id;
    """)
    st.subheader("All Venues with Complex")
    st.dataframe(df1)

    df2 = run_query("""
        SELECT cm.complex_name, COUNT(v.venue_id) AS venues_count 
        FROM venues v 
        LEFT JOIN complex cm on v.complex_id = cm.complex_id 
        GROUP BY cm.complex_name ORDER BY venues_count DESC;
    """)
    st.subheader("Venue Count per Complex")
    st.dataframe(df2)

# ---------- COMPETITOR RANKINGS SECTION ----------
elif section == "Competitor Rankings":
    st.header("📊 Competitor Rankings Overview")

    df1 = run_query("""
        SELECT ct.name AS Competitor, cr.rank AS `Rank`, cr.points AS Points
        FROM competitor_rankings cr 
        LEFT JOIN competitors ct ON cr.competitor_id = ct.competitor_id;
    """)
    st.subheader("All Competitors with Rank and Points")
    st.dataframe(df1)

    df2 = run_query("""
        SELECT ct.name AS Competitor, cr.rank AS `Rank`
        FROM competitor_rankings cr 
        LEFT JOIN competitors ct ON cr.competitor_id = ct.competitor_id
        ORDER BY cr.rank ASC LIMIT 5;
    """)
    st.subheader("Top 5 Competitors")
    st.dataframe(df2)

    df3 = run_query("""
        SELECT ct.name AS Competitor, cr.rank AS `Rank`, cr.points AS Points, cr.movement AS Movement
        FROM competitor_rankings cr 
        LEFT JOIN competitors ct ON cr.competitor_id = ct.competitor_id
        WHERE cr.movement = 0 ORDER BY cr.rank ASC;
    """)
    st.subheader("Stable Rank (No Movement)")
    st.dataframe(df3)

    df4 = run_query("""
        SELECT ct.country AS Country, SUM(cr.points) AS Total_Points
        FROM competitor_rankings cr 
        LEFT JOIN competitors ct ON cr.competitor_id = ct.competitor_id
        WHERE ct.country = 'Croatia' GROUP BY ct.country;
    """)
    st.subheader("Total Points - Croatia")
    st.dataframe(df4)

    df5 = run_query("""
        SELECT ct.country AS Country, COUNT(*) AS Competitor_Count
        FROM competitors ct GROUP BY ct.country ORDER BY Competitor_Count DESC;
    """)
    st.subheader("Competitor Count per Country")
    st.dataframe(df5)

    df6 = run_query("""
        SELECT ct.name AS Competitor, cr.rank AS `Rank`, cr.points AS Points
        FROM competitor_rankings cr 
        LEFT JOIN competitors ct ON cr.competitor_id = ct.competitor_id
        WHERE cr.points = (SELECT MAX(points) FROM competitor_rankings);
    """)
    st.subheader("Competitor with Highest Points")
    st.dataframe(df6)
