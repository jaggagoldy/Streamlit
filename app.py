import streamlit as st
import sqlite3
import pandas as pd
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

# Constants
PROJECT_STATUSES = [
    "New Request",
    "Brainstorming",
    "Scope Ready",
    "In Development",
    "Dev Completed",
    "Handover to QA",
    "QA End",
    "Stakeholder Demo",
    "Go-Live",
    "Delayed"
]

MILESTONE_TYPES = [
    "DEV_START",
    "DEV_COMPLETE",
    "HANDOVER_TO_QA",
    "QA_END",
    "STAKEHOLDER_DEMO",
    "GO_LIVE"
]

ROLES = ["FE", "BE", "iOS", "Android", "QA"]
PHASES = ["DEV", "QA"]

# Helper functions
def generate_month_options():
    """Generate list of months for the next 12 months."""
    months = []
    current = date.today()
    for i in range(13):  # Current month + 12 future months
        month_date = current + relativedelta(months=i)
        months.append(month_date.strftime("%b %Y"))
    return months

def get_current_month():
    """Get current month in format 'Feb 2026'."""
    return date.today().strftime("%b %Y")

# Database initialization and migration
def init_db():
    """Initialize SQLite database and create/migrate tables."""
    conn = sqlite3.connect('project_tracker.db')
    cursor = conn.cursor()
    
    # Create projects table with new schema
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            product TEXT,
            business_owner TEXT,
            scrum_master TEXT,
            platforms TEXT,
            planned_go_live DATE,
            status TEXT,
            delivery_month TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Check if migration is needed for existing projects table
    cursor.execute("PRAGMA table_info(projects)")
    columns = [col[1] for col in cursor.fetchall()]
    
    # Migrate old schema to new schema
    if 'product_squad' in columns and 'product' not in columns:
        # Rename product_squad to product
        cursor.execute("ALTER TABLE projects RENAME COLUMN product_squad TO product")
    
    # Add new columns if they don't exist
    if 'scrum_master' not in columns:
        cursor.execute("ALTER TABLE projects ADD COLUMN scrum_master TEXT")
    if 'platforms' not in columns:
        cursor.execute("ALTER TABLE projects ADD COLUMN platforms TEXT")
    if 'delivery_month' not in columns:
        cursor.execute("ALTER TABLE projects ADD COLUMN delivery_month TEXT")
    if 'notes' not in columns:
        cursor.execute("ALTER TABLE projects ADD COLUMN notes TEXT")
    
    # Create milestones table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS milestones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            milestone_type TEXT NOT NULL,
            planned_date DATE,
            revised_date DATE,
            delay_reason TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE
        )
    ''')
    
    # Create resources table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS resources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_name TEXT NOT NULL,
            role TEXT NOT NULL,
            project_id INTEGER NOT NULL,
            phase TEXT NOT NULL,
            allocation_pct INTEGER,
            end_rule TEXT DEFAULT 'Till Go-Live',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE
        )
    ''')
    
    conn.commit()
    conn.close()

# Database helper functions
def get_db_connection():
    """Get database connection."""
    conn = sqlite3.connect('project_tracker.db')
    conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign key constraints
    return conn

def get_all_projects(month_filter=None, product_filter=None, status_filter=None):
    """Fetch all projects from database with optional filters."""
    conn = get_db_connection()
    query = "SELECT * FROM projects WHERE 1=1"
    params = []
    
    if month_filter:
        query += " AND delivery_month = ?"
        params.append(month_filter)
    if product_filter:
        query += " AND product LIKE ?"
        params.append(f"%{product_filter}%")
    if status_filter and len(status_filter) > 0:
        placeholders = ','.join('?' * len(status_filter))
        query += f" AND status IN ({placeholders})"
        params.extend(status_filter)
    
    query += " ORDER BY created_at DESC"
    
    df = pd.read_sql_query(query, conn, params=params if params else None)
    conn.close()
    return df

def get_project_names():
    """Get list of project names for dropdowns."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM projects ORDER BY name")
    projects = cursor.fetchall()
    conn.close()
    return {name: id for id, name in projects}

def get_project_by_id(project_id):
    """Get a single project by ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
    project = cursor.fetchone()
    conn.close()
    return project

def add_project(name, product, business_owner, scrum_master, platforms, planned_go_live, status, delivery_month, notes):
    """Add a new project to database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO projects (name, product, business_owner, scrum_master, platforms, planned_go_live, status, delivery_month, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (name, product, business_owner, scrum_master, platforms, planned_go_live, status, delivery_month, notes))
    conn.commit()
    conn.close()

def update_project_status(project_id, new_status):
    """Update project status."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE projects SET status = ? WHERE id = ?", (new_status, project_id))
    conn.commit()
    conn.close()

def update_project_notes(project_id, notes):
    """Update project notes."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE projects SET notes = ? WHERE id = ?", (notes, project_id))
    conn.commit()
    conn.close()

def delete_project(project_id):
    """Delete a project and all related milestones and resources."""
    conn = get_db_connection()
    cursor = conn.cursor()
    # Foreign key constraints with ON DELETE CASCADE will handle related records
    cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))
    conn.commit()
    conn.close()

def get_milestones_for_project(project_id):
    """Get all milestones for a specific project."""
    conn = get_db_connection()
    df = pd.read_sql_query(
        "SELECT * FROM milestones WHERE project_id = ? ORDER BY planned_date",
        conn,
        params=(project_id,)
    )
    conn.close()
    return df

def add_milestone(project_id, milestone_type, planned_date, revised_date, delay_reason):
    """Add a new milestone to database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO milestones (project_id, milestone_type, planned_date, revised_date, delay_reason)
        VALUES (?, ?, ?, ?, ?)
    ''', (project_id, milestone_type, planned_date, revised_date, delay_reason))
    conn.commit()
    conn.close()

def delete_milestone(milestone_id):
    """Delete a milestone."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM milestones WHERE id = ?", (milestone_id,))
    conn.commit()
    conn.close()

def get_all_resources():
    """Get all resources with project names."""
    conn = get_db_connection()
    df = pd.read_sql_query('''
        SELECT r.*, p.name as project_name 
        FROM resources r
        JOIN projects p ON r.project_id = p.id
        ORDER BY r.created_at DESC
    ''', conn)
    conn.close()
    return df

def add_resource(employee_name, role, project_id, phase, allocation_pct):
    """Add a new resource to database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO resources (employee_name, role, project_id, phase, allocation_pct)
        VALUES (?, ?, ?, ?, ?)
    ''', (employee_name, role, project_id, phase, allocation_pct))
    conn.commit()
    conn.close()

def delete_resource(resource_id):
    """Delete a resource."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM resources WHERE id = ?", (resource_id,))
    conn.commit()
    conn.close()

# Initialize database
init_db()

# Streamlit app configuration
st.set_page_config(
    page_title="Project Tracker",
    page_icon="📊",
    layout="wide"
)

# Initialize session state for confirmations
if 'delete_confirm' not in st.session_state:
    st.session_state.delete_confirm = {}

# Sidebar navigation
st.sidebar.title("🗂️ Navigation")
page = st.sidebar.radio(
    "Go to",
    [
        "📝 Project Intake",
        "🎯 Milestones",
        "👥 Resources",
        "📋 Release View (Management)",
        "📈 CTO Dashboard"
    ]
)

st.title("📊 Project & Resource Tracker")
st.markdown("---")

# PAGE 1: PROJECT INTAKE
if page == "📝 Project Intake":
    st.header("Project Intake Form")
    
    with st.form("project_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            project_name = st.text_input("Project Name *", placeholder="Enter project name")
            product = st.text_input("Product *", placeholder="Enter product name")
            business_owner = st.text_input("Business Owner (Stakeholders)", placeholder="Enter business owner name")
            scrum_master = st.text_input("Scrum Master", placeholder="Enter scrum master name")
        
        with col2:
            platforms = st.text_input("Platforms", placeholder="e.g., iOS, Android, Web")
            planned_go_live = st.date_input("Planned Go-Live", value=date.today())
            delivery_month = st.selectbox("Delivery Month *", options=generate_month_options())
            status = st.selectbox("Status *", options=PROJECT_STATUSES)
        
        notes = st.text_area("Notes", placeholder="Enter any additional notes or updates")
        
        submitted = st.form_submit_button("💾 Save Project", use_container_width=True)
        
        if submitted:
            if not project_name or not product:
                st.error("❌ Project Name and Product are required!")
            else:
                try:
                    add_project(
                        project_name,
                        product,
                        business_owner,
                        scrum_master,
                        platforms,
                        planned_go_live.isoformat(),
                        status,
                        delivery_month,
                        notes
                    )
                    st.success(f"✅ Project '{project_name}' saved successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error saving project: {str(e)}")
    
    st.markdown("---")
    st.subheader("Existing Projects")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        month_filter = st.selectbox("Filter by Month", ["All"] + generate_month_options(), key="intake_month_filter")
    with col2:
        product_filter = st.text_input("Filter by Product", placeholder="Search product...", key="intake_product_filter")
    with col3:
        status_filter = st.multiselect("Filter by Status", PROJECT_STATUSES, key="intake_status_filter")
    
    # Apply filters
    month_f = None if month_filter == "All" else month_filter
    product_f = product_filter if product_filter else None
    status_f = status_filter if status_filter else None
    
    projects_df = get_all_projects(month_f, product_f, status_f)
    
    if not projects_df.empty:
        # Display projects with delete buttons
        for idx, row in projects_df.iterrows():
            with st.expander(f"**{row['name']}** - {row['status']}", expanded=False):
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.write(f"**Product:** {row['product']}")
                    st.write(f"**Business Owner:** {row['business_owner']}")
                    st.write(f"**Scrum Master:** {row['scrum_master']}")
                    st.write(f"**Platforms:** {row['platforms']}")
                    st.write(f"**Delivery Month:** {row['delivery_month']}")
                    st.write(f"**Planned Go-Live:** {row['planned_go_live']}")
                    st.write(f"**Status:** {row['status']}")
                    if row['notes']:
                        st.write(f"**Notes:** {row['notes']}")
                with col2:
                    if st.button("🗑️ Delete", key=f"delete_project_{row['id']}"):
                        st.session_state.delete_confirm[f"project_{row['id']}"] = True
                        st.rerun()
                    
                    if st.session_state.delete_confirm.get(f"project_{row['id']}", False):
                        st.warning("⚠️ Are you sure?")
                        col_yes, col_no = st.columns(2)
                        with col_yes:
                            if st.button("Yes", key=f"confirm_delete_project_{row['id']}"):
                                delete_project(row['id'])
                                st.session_state.delete_confirm[f"project_{row['id']}"] = False
                                st.success("✅ Project deleted!")
                                st.rerun()
                        with col_no:
                            if st.button("No", key=f"cancel_delete_project_{row['id']}"):
                                st.session_state.delete_confirm[f"project_{row['id']}"] = False
                                st.rerun()
    else:
        st.info("No projects found. Add your first project above!")

# PAGE 2: MILESTONES
elif page == "🎯 Milestones":
    st.header("Project Milestones")
    
    projects = get_project_names()
    
    if not projects:
        st.warning("⚠️ No projects available. Please add a project first in the Project Intake page.")
    else:
        selected_project_name = st.selectbox(
            "Select Project",
            options=list(projects.keys()),
            key="milestone_project_selector"
        )
        
        if selected_project_name:
            project_id = projects[selected_project_name]
            
            st.markdown("---")
            st.subheader("Add New Milestone")
            
            with st.form("milestone_form", clear_on_submit=True):
                col1, col2 = st.columns(2)
                
                with col1:
                    milestone_type = st.selectbox("Milestone Type *", options=MILESTONE_TYPES)
                    planned_date = st.date_input("Planned Date *", value=date.today())
                
                with col2:
                    revised_date = st.date_input("Revised Date (Optional)", value=None)
                    delay_reason = st.text_area("Reason for Delay (Optional)", placeholder="Enter reason if delayed")
                
                milestone_submitted = st.form_submit_button("➕ Add Milestone", use_container_width=True)
                
                if milestone_submitted:
                    try:
                        add_milestone(
                            project_id,
                            milestone_type,
                            planned_date.isoformat(),
                            revised_date.isoformat() if revised_date else None,
                            delay_reason if delay_reason else None
                        )
                        st.success(f"✅ Milestone '{milestone_type}' added successfully!")
                        
                        # Check if dates are slipping and suggest Delayed status
                        if revised_date and revised_date > planned_date:
                            project = get_project_by_id(project_id)
                            if project and project[7] != "Delayed":  # status is at index 7
                                st.warning("⚠️ This milestone has a revised date later than planned. Would you like to mark the project as 'Delayed'?")
                                if st.button("Mark as Delayed"):
                                    update_project_status(project_id, "Delayed")
                                    st.success("✅ Project status updated to 'Delayed'")
                                    st.rerun()
                        
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error adding milestone: {str(e)}")
            
            st.markdown("---")
            st.subheader(f"Milestones for {selected_project_name}")
            
            milestones_df = get_milestones_for_project(project_id)
            if not milestones_df.empty:
                for idx, row in milestones_df.iterrows():
                    col1, col2 = st.columns([5, 1])
                    with col1:
                        st.write(f"**{row['milestone_type']}** - Planned: {row['planned_date']}" + 
                                (f" | Revised: {row['revised_date']}" if row['revised_date'] else "") +
                                (f" | Reason: {row['delay_reason']}" if row['delay_reason'] else ""))
                    with col2:
                        if st.button("🗑️", key=f"delete_milestone_{row['id']}"):
                            st.session_state.delete_confirm[f"milestone_{row['id']}"] = True
                            st.rerun()
                        
                        if st.session_state.delete_confirm.get(f"milestone_{row['id']}", False):
                            st.warning("Delete?")
                            col_yes, col_no = st.columns(2)
                            with col_yes:
                                if st.button("Yes", key=f"confirm_delete_milestone_{row['id']}"):
                                    delete_milestone(row['id'])
                                    st.session_state.delete_confirm[f"milestone_{row['id']}"] = False
                                    st.success("✅ Deleted!")
                                    st.rerun()
                            with col_no:
                                if st.button("No", key=f"cancel_delete_milestone_{row['id']}"):
                                    st.session_state.delete_confirm[f"milestone_{row['id']}"] = False
                                    st.rerun()
            else:
                st.info("No milestones yet for this project.")

# PAGE 3: RESOURCES
elif page == "👥 Resources":
    st.header("Resource Assignment")
    
    projects = get_project_names()
    
    if not projects:
        st.warning("⚠️ No projects available. Please add a project first in the Project Intake page.")
    else:
        st.subheader("Add New Resource")
        
        with st.form("resource_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                employee_name = st.text_input("Employee Name *", placeholder="Enter employee name")
                role = st.selectbox("Role *", options=ROLES)
                resource_project_name = st.selectbox("Select Project *", options=list(projects.keys()), key="resource_project_selector")
            
            with col2:
                phase = st.selectbox("Phase *", options=PHASES)
                allocation_pct = st.number_input("Allocation % *", min_value=0, max_value=100, value=100, step=5)
                st.info("📌 End Rule: Till Go-Live")
            
            resource_submitted = st.form_submit_button("➕ Add Resource", use_container_width=True)
            
            if resource_submitted:
                if not employee_name:
                    st.error("❌ Employee Name is required!")
                else:
                    try:
                        resource_project_id = projects[resource_project_name]
                        add_resource(employee_name, role, resource_project_id, phase, allocation_pct)
                        st.success(f"✅ Resource '{employee_name}' assigned successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error adding resource: {str(e)}")
        
        st.markdown("---")
        st.subheader("All Resources")
        
        resources_df = get_all_resources()
        if not resources_df.empty:
            for idx, row in resources_df.iterrows():
                col1, col2 = st.columns([5, 1])
                with col1:
                    st.write(f"**{row['employee_name']}** ({row['role']}) - {row['project_name']} | Phase: {row['phase']} | Allocation: {row['allocation_pct']}%")
                with col2:
                    if st.button("🗑️", key=f"delete_resource_{row['id']}"):
                        st.session_state.delete_confirm[f"resource_{row['id']}"] = True
                        st.rerun()
                    
                    if st.session_state.delete_confirm.get(f"resource_{row['id']}", False):
                        st.warning("Delete?")
                        col_yes, col_no = st.columns(2)
                        with col_yes:
                            if st.button("Yes", key=f"confirm_delete_resource_{row['id']}"):
                                delete_resource(row['id'])
                                st.session_state.delete_confirm[f"resource_{row['id']}"] = False
                                st.success("✅ Deleted!")
                                st.rerun()
                        with col_no:
                            if st.button("No", key=f"cancel_delete_resource_{row['id']}"):
                                st.session_state.delete_confirm[f"resource_{row['id']}"] = False
                                st.rerun()
        else:
            st.info("No resources assigned yet.")

# PAGE 4: RELEASE VIEW (MANAGEMENT)
elif page == "📋 Release View (Management)":
    st.header("Release View (Management)")
    st.caption("High-level delivery information for leadership")
    
    # Month filter (default to current month)
    current_month = get_current_month()
    month_filter = st.selectbox("Filter by Delivery Month", generate_month_options(), index=0 if current_month in generate_month_options() else 0, key="release_month_filter")
    
    projects_df = get_all_projects(month_filter=month_filter)
    
    if not projects_df.empty:
        st.markdown("---")
        
        # Display as a clean table
        st.subheader(f"Projects for {month_filter}")
        
        # Create display dataframe
        display_data = []
        for idx, row in projects_df.iterrows():
            display_data.append({
                "Month": row['delivery_month'] or "—",
                "Project": row['name'],
                "Stakeholders": row['business_owner'] or "—",
                "Scrum Master": row['scrum_master'] or "—",
                "Platforms": row['platforms'] or "—",
                "Status": row['status'],
                "Delivery Date": row['planned_go_live'],
                "Notes": row['notes'] or "—"
            })
        
        display_df = pd.DataFrame(display_data)
        
        # Show editable table using st.data_editor
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        st.subheader("Update Project Notes")
        
        # Allow editing notes for each project
        for idx, row in projects_df.iterrows():
            with st.expander(f"Edit Notes: {row['name']}", expanded=False):
                new_notes = st.text_area(
                    "Status Notes",
                    value=row['notes'] or "",
                    key=f"notes_{row['id']}",
                    placeholder="Enter status updates, blockers, or notes..."
                )
                
                col1, col2 = st.columns([1, 4])
                with col1:
                    if st.button("💾 Save Notes", key=f"save_notes_{row['id']}"):
                        update_project_notes(row['id'], new_notes)
                        st.success("✅ Notes updated!")
                        st.rerun()
                
                with col2:
                    # Allow manual status change
                    new_status = st.selectbox(
                        "Change Status",
                        options=PROJECT_STATUSES,
                        index=PROJECT_STATUSES.index(row['status']) if row['status'] in PROJECT_STATUSES else 0,
                        key=f"status_{row['id']}"
                    )
                    if new_status != row['status']:
                        if st.button("Update Status", key=f"update_status_{row['id']}"):
                            update_project_status(row['id'], new_status)
                            st.success(f"✅ Status updated to '{new_status}'!")
                            st.rerun()
    else:
        st.info(f"No projects scheduled for {month_filter}. Try selecting a different month.")

# PAGE 5: CTO DASHBOARD
elif page == "📈 CTO Dashboard":
    st.header("CTO Dashboard")
    
    # Month filter
    month_options = ["All Months"] + generate_month_options()
    selected_month = st.selectbox("Filter by Delivery Month", month_options, key="dashboard_month_filter")
    
    month_f = None if selected_month == "All Months" else selected_month
    projects_df = get_all_projects(month_filter=month_f)
    resources_df = get_all_resources()
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_projects = len(projects_df)
        st.metric("Total Projects", total_projects)
    
    with col2:
        st.metric("Total Resources", len(resources_df))
    
    with col3:
        if not projects_df.empty:
            on_time = len(projects_df[projects_df['status'] != 'Delayed'])
            delayed = len(projects_df[projects_df['status'] == 'Delayed'])
            st.metric("On-Time", on_time, delta=f"{delayed} delayed", delta_color="inverse")
        else:
            st.metric("On-Time", 0)
    
    with col4:
        if not projects_df.empty:
            active_statuses = ['In Development', 'Dev Completed', 'Handover to QA', 'QA End']
            active_projects = len(projects_df[projects_df['status'].isin(active_statuses)])
            st.metric("Active Projects", active_projects)
        else:
            st.metric("Active Projects", 0)
    
    st.markdown("---")
    
    if not projects_df.empty:
        # Status breakdown
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Projects by Status")
            status_counts = projects_df['status'].value_counts()
            st.bar_chart(status_counts)
        
        with col2:
            st.subheader("On-Time vs Delayed")
            on_time_count = len(projects_df[projects_df['status'] != 'Delayed'])
            delayed_count = len(projects_df[projects_df['status'] == 'Delayed'])
            
            delay_df = pd.DataFrame({
                'Category': ['On-Time', 'Delayed'],
                'Count': [on_time_count, delayed_count]
            })
            st.bar_chart(delay_df.set_index('Category'))
        
        st.markdown("---")
        
        # Phase breakdown
        st.subheader("Projects by Phase")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            in_dev = len(projects_df[projects_df['status'].isin(['In Development', 'Dev Completed'])])
            st.metric("In Development", in_dev)
        
        with col2:
            in_qa = len(projects_df[projects_df['status'].isin(['Handover to QA', 'QA End'])])
            st.metric("In QA", in_qa)
        
        with col3:
            live = len(projects_df[projects_df['status'] == 'Go-Live'])
            st.metric("Live", live)
        
        st.markdown("---")
        st.subheader("Recent Projects")
        recent_df = projects_df.head(10)[['name', 'product', 'status', 'delivery_month', 'planned_go_live']]
        recent_df.columns = ['Project', 'Product', 'Status', 'Delivery Month', 'Go-Live Date']
        st.dataframe(recent_df, use_container_width=True, hide_index=True)
    else:
        st.info("No data available for the selected month. Start by adding projects!")

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>Project & Resource Tracker | Built with Streamlit</div>",
    unsafe_allow_html=True
)
