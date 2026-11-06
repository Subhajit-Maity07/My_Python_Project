import os
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Page Configuration
st.set_page_config(
    page_title="Dynamic Event Management & Analyzer",
    page_icon="🎓",
    layout="wide",
)

# File Paths for CSV Data Storage
EVENTS_FILE = "events.csv"
STUDENTS_FILE = "students.csv"
REGISTRATIONS_FILE = "registrations.csv"


# Custom Exception Classes
class EventNotFoundError(Exception):
    pass


class EventFullError(Exception):
    pass


class DuplicateRegistrationError(Exception):
    pass


class RegistrationNotFoundError(Exception):
    pass


# Function to Load Data (Initializes empty DataFrames if CSVs do not exist)
def load_data():
    events = (
        pd.read_csv(EVENTS_FILE)
        if os.path.exists(EVENTS_FILE)
        else pd.DataFrame(
            columns=[
                "event_id",
                "name",
                "date",
                "venue",
                "max_participants",
            ]
        )
    )
    students = (
        pd.read_csv(STUDENTS_FILE)
        if os.path.exists(STUDENTS_FILE)
        else pd.DataFrame(columns=["student_id", "name", "email"])
    )
    registrations = (
        pd.read_csv(REGISTRATIONS_FILE)
        if os.path.exists(REGISTRATIONS_FILE)
        else pd.DataFrame(
            columns=["registration_id", "event_id", "student_id", "rating"]
        )
    )

    # Ensure Correct Data Types
    if not events.empty:
        events["event_id"] = events["event_id"].astype(str)
        events["max_participants"] = events["max_participants"].astype(int)
    if not students.empty:
        students["student_id"] = students["student_id"].astype(str)
    if not registrations.empty:
        registrations["event_id"] = registrations["event_id"].astype(str)
        registrations["student_id"] = registrations["student_id"].astype(str)

    return events, students, registrations


# Function to Save Data to CSV Files
def save_data():
    st.session_state.events_df.to_csv(EVENTS_FILE, index=False)
    st.session_state.students_df.to_csv(STUDENTS_FILE, index=False)
    st.session_state.regs_df.to_csv(REGISTRATIONS_FILE, index=False)


# Initialize Session State with empty datasets
if "events_df" not in st.session_state:
    events, students, regs = load_data()
    st.session_state.events_df = events
    st.session_state.students_df = students
    st.session_state.regs_df = regs

# Main Header
st.title("🎓 Campus Event Management & Feedback Analyzer")
st.markdown("---")

# Navigation Menu
menu = [
    "📊 Analytics & Graphs",
    "➕ Create Event",
    "🎟️ Student Registration",
    "⭐ Submit Feedback",
    "📋 View Saved Data",
    "🔍 Search Students",
    "❌ Cancel Registration",
]
choice = st.sidebar.radio("Navigation Menu", menu)


# 1. Dynamic Analytics & Graph Generation
if choice == "📊 Analytics & Graphs":
    st.subheader("📊 Dynamic Analytics & Visualizations Dashboard")

    events_df = st.session_state.events_df
    students_df = st.session_state.students_df
    regs_df = st.session_state.regs_df

    if events_df.empty:
        st.warning(
            "⚠️ No data provided yet! Please create an event under 'Create"
            " Event' and register students to display dynamic charts."
        )
    else:
        # Dynamic Metric Cards
        tot_events = len(events_df)
        tot_regs = len(regs_df)
        uniq_students = (
            len(regs_df["student_id"].unique()) if not regs_df.empty else 0
        )

        rated_regs = (
            regs_df.dropna(subset=["rating"])
            if not regs_df.empty
            else pd.DataFrame()
        )
        if not rated_regs.empty and "rating" in rated_regs.columns:
            rated_regs["rating"] = pd.to_numeric(
                rated_regs["rating"], errors="coerce"
            )
            avg_rating = rated_regs["rating"].mean()
        else:
            avg_rating = 0.0

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Events Created", tot_events)
        m2.metric("Total Registrations", tot_regs)
        m3.metric("Unique Students", uniq_students)
        m4.metric(
            "Overall Avg Rating",
            f"{avg_rating:.2f} / 5.0" if not np.isnan(avg_rating) else "N/A",
        )

        st.markdown("---")

        # Tabs for Required Visualizations
        t1, t2, t3 = st.tabs([
            "📈 Event Participation Graph",
            "📊 Bar Chart (Average Ratings)",
            "📉 Histogram (Feedback Distribution)",
        ])

        # Graph 1: Event Participation Graph
        with t1:
            st.markdown("#### 1. Event Participation Graph")
            event_counts = (
                regs_df.groupby("event_id").size().reset_index(name="count")
                if not regs_df.empty
                else pd.DataFrame(columns=["event_id", "count"])
            )
            merged_part = pd.merge(
                events_df, event_counts, on="event_id", how="left"
            ).fillna({"count": 0})

            fig1 = px.bar(
                merged_part,
                x="name",
                y="count",
                color="name",
                title="Event-wise Participation Graph",
                labels={"name": "Event Name", "count": "Registered Students"},
                text_auto=True,
            )
            fig1.update_layout(template="plotly_white")
            st.plotly_chart(fig1, use_container_width=True)

        # Graph 2: Bar Chart for Average Ratings
        with t2:
            st.markdown("#### 2. Bar Chart - Average Rating per Event")
            if not regs_df.empty and "rating" in regs_df.columns:
                valid_ratings = regs_df.dropna(subset=["rating"]).copy()
                if not valid_ratings.empty:
                    valid_ratings["rating"] = pd.to_numeric(
                        valid_ratings["rating"], errors="coerce"
                    )
                    avg_df = (
                        valid_ratings.groupby("event_id")["rating"]
                        .mean()
                        .reset_index()
                    )
                    rating_merged = pd.merge(
                        events_df, avg_df, on="event_id", how="left"
                    ).fillna({"rating": 0})

                    fig2 = px.bar(
                        rating_merged,
                        x="name",
                        y="rating",
                        color="rating",
                        color_continuous_scale="Viridis",
                        title="Average Feedback Rating per Event (Scale 1.0 - 5.0)",
                        labels={
                            "name": "Event Name",
                            "rating": "Average Rating",
                        },
                        text_auto=".2f",
                    )
                    fig2.update_layout(
                        yaxis=dict(range=[0, 5.2]), template="plotly_white"
                    )
                    st.plotly_chart(fig2, use_container_width=True)
                else:
                    st.info(
                        "ℹ️ No feedback ratings submitted yet. Submit ratings"
                        " under 'Submit Feedback'."
                    )
            else:
                st.info(
                    "ℹ️ No feedback ratings submitted yet. Submit ratings under"
                    " 'Submit Feedback'."
                )

        # Graph 3: Histogram of Feedback Ratings
        with t3:
            st.markdown("#### 3. Histogram - Distribution of Ratings")
            if not regs_df.empty and "rating" in regs_df.columns:
                valid_ratings = regs_df.dropna(subset=["rating"]).copy()
                if not valid_ratings.empty:
                    valid_ratings["rating"] = pd.to_numeric(
                        valid_ratings["rating"], errors="coerce"
                    )
                    fig3 = px.histogram(
                        valid_ratings,
                        x="rating",
                        nbins=10,
                        color_discrete_sequence=["#22C55E"],
                        title="Distribution of Feedback Ratings (Histogram)",
                        labels={"rating": "Rating Stars (1.0 to 5.0)"},
                    )
                    fig3.update_layout(template="plotly_white")
                    st.plotly_chart(fig3, use_container_width=True)
                else:
                    st.info(
                        "ℹ️ Feedback ratings required to display histogram."
                    )
            else:
                st.info("ℹ️ Feedback ratings required to display histogram.")


# 2. Create Event Input Form
elif choice == "➕ Create Event":
    st.subheader("➕ Create a New Event (Input Data)")
    with st.form("create_event_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            eid = st.text_input("Event ID (e.g., E101)").strip()
            ename = st.text_input("Event Name").strip()
            edate = st.date_input("Event Date")
        with col2:
            evenue = st.text_input("Venue").strip()
            emax = st.number_input(
                "Maximum Capacity", min_value=1, value=50
            )

        submitted = st.form_submit_button("Save Event Data")

        if submitted:
            if not eid or not ename:
                st.error("Event ID and Event Name are required!")
            elif (
                eid
                in st.session_state.events_df["event_id"].astype(str).values
            ):
                st.error(f"Event ID '{eid}' already exists in the database!")
            else:
                new_event = pd.DataFrame([{
                    "event_id": str(eid),
                    "name": ename,
                    "date": str(edate),
                    "venue": evenue,
                    "max_participants": int(emax),
                }])
                st.session_state.events_df = pd.concat(
                    [st.session_state.events_df, new_event], ignore_index=True
                )
                save_data()
                st.success(f"Event '{ename}' saved successfully!")


# 3. Student Registration Input Form
elif choice == "🎟️ Student Registration":
    st.subheader("🎟️ Register Student for Event (Input Data)")
    events_df = st.session_state.events_df

    if events_df.empty:
        st.warning("Please create an event under 'Create Event' first.")
    else:
        event_dict = {
            f"{row['name']} ({row['event_id']})": str(row["event_id"])
            for _, row in events_df.iterrows()
        }

        with st.form("reg_form", clear_on_submit=True):
            sid = st.text_input("Student ID (e.g., S101)").strip()
            sname = st.text_input("Student Name").strip()
            semail = st.text_input("Student Email").strip()
            selected_label = st.selectbox("Select Event", list(event_dict.keys()))

            submitted = st.form_submit_button("Register Student")

            if submitted:
                if not sid or not sname:
                    st.error("Student ID and Name are required!")
                else:
                    eid = event_dict[selected_label]
                    regs_df = st.session_state.regs_df
                    students_df = st.session_state.students_df
                    event_info = events_df[events_df["event_id"] == eid].iloc[0]

                    try:
                        # Capacity Exception Check
                        curr_count = len(regs_df[regs_df["event_id"] == eid])
                        if curr_count >= event_info["max_participants"]:
                            raise EventFullError(
                                f"Event '{event_info['name']}' has reached max"
                                " capacity!"
                            )

                        # Duplicate Registration Check
                        if not regs_df[
                            (regs_df["event_id"] == eid)
                            & (regs_df["student_id"] == sid)
                        ].empty:
                            raise DuplicateRegistrationError(
                                "Student is already registered for this event!"
                            )

                        # Save Student Details
                        if (
                            sid
                            not in students_df["student_id"].astype(str).values
                        ):
                            new_std = pd.DataFrame([{
                                "student_id": sid,
                                "name": sname,
                                "email": semail,
                            }])
                            st.session_state.students_df = pd.concat(
                                [st.session_state.students_df, new_std],
                                ignore_index=True,
                            )

                        # Save Registration Record
                        reg_id = f"REG{len(regs_df) + 1:03d}"
                        new_reg = pd.DataFrame([{
                            "registration_id": reg_id,
                            "event_id": eid,
                            "student_id": sid,
                            "rating": None,
                        }])
                        st.session_state.regs_df = pd.concat(
                            [st.session_state.regs_df, new_reg],
                            ignore_index=True,
                        )

                        save_data()
                        st.success(
                            f"Student {sname} successfully registered for"
                            f" {event_info['name']}!"
                        )

                    except (EventFullError, DuplicateRegistrationError) as e:
                        st.error(f"Error: {e}")


# 4. Submit Feedback Input Form
elif choice == "⭐ Submit Feedback":
    st.subheader("⭐ Submit Event Feedback (Input Rating)")
    regs_df = st.session_state.regs_df

    if regs_df.empty:
        st.warning("Active registration required before submitting feedback.")
    else:
        sid = st.text_input("Enter Student ID").strip()
        eid = st.text_input("Enter Event ID").strip()
        rating = st.slider("Select Rating (1.0 to 5.0)", 1.0, 5.0, 5.0, step=0.5)

        if st.button("Submit Feedback"):
            mask = (regs_df["student_id"] == sid) & (regs_df["event_id"] == eid)
            if regs_df[mask].empty:
                st.error("Registration record not found!")
            else:
                st.session_state.regs_df.loc[mask, "rating"] = rating
                save_data()
                st.success("Feedback rating successfully recorded!")


# 5. View Saved Database Data
elif choice == "📋 View Saved Data":
    st.subheader("📋 Live Database Preview")
    st.write("### Events Table")
    st.dataframe(st.session_state.events_df, use_container_width=True)
    st.write("### Students Directory")
    st.dataframe(st.session_state.students_df, use_container_width=True)
    st.write("### Registrations & Ratings")
    st.dataframe(st.session_state.regs_df, use_container_width=True)


# 6. Search Registered Students
elif choice == "🔍 Search Students":
    st.subheader("🔍 Search Registered Students by Event")
    events_df = st.session_state.events_df

    if events_df.empty:
        st.info("No events data available.")
    else:
        selected_eid = st.selectbox(
            "Select Event ID", events_df["event_id"].unique()
        )
        if st.button("Search"):
            regs_df = st.session_state.regs_df
            students_df = st.session_state.students_df
            event_regs = regs_df[regs_df["event_id"] == selected_eid]

            if event_regs.empty:
                st.info("No students registered for this event yet.")
            else:
                merged = pd.merge(
                    event_regs, students_df, on="student_id", how="left"
                )
                st.dataframe(
                    merged[["student_id", "name", "email"]],
                    use_container_width=True,
                )


# 7. Cancel Registration
elif choice == "❌ Cancel Registration":
    st.subheader("❌ Cancel Event Registration")
    regs_df = st.session_state.regs_df

    sid = st.text_input("Student ID")
    eid = st.text_input("Event ID")

    if st.button("Cancel Registration"):
        match = regs_df[
            (regs_df["student_id"] == sid) & (regs_df["event_id"] == eid)
        ]
        if match.empty:
            st.error("Registration record not found!")
        else:
            st.session_state.regs_df = regs_df[
                ~((regs_df["student_id"] == sid) & (regs_df["event_id"] == eid))
            ]
            save_data()
            st.success("Registration record cancelled successfully.")