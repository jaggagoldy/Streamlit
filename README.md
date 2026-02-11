# 📊 Project & Resource Tracker

A simple, shareable internal web app built with **Streamlit + Python + SQLite** for tracking projects, milestones, and resources.

## Features

### 📝 Project Intake
- Add new projects with details: name, product/squad, business owner, planned go-live date, and status
- Track project status: Brainstorming, Dev, QA, Live, or Delayed
- View all projects in a sortable table

### 🎯 Milestones
- Add milestones to projects with predefined types:
  - DEV_START
  - DEV_COMPLETE
  - HANDOVER_TO_QA
  - QA_END
  - STAKEHOLDER_DEMO
  - GO_LIVE
- Track planned dates, revised dates, and delay reasons
- View all milestones per project

### 👥 Resources
- Assign team members to projects
- Specify role (FE, BE, iOS, Android, QA)
- Set phase (DEV or QA) and allocation percentage
- Default end rule: "Till Go-Live"
- View all resource assignments

### 📈 Dashboard
- Overview metrics: total projects, resources, and active projects
- Visual charts showing project distribution by status
- Recent projects summary

## Local Setup

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Installation

1. **Clone or download this repository**

2. **Navigate to the project directory**
   ```bash
   cd streamlit-project-tracker
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   streamlit run app.py
   ```

5. **Open your browser**
   - The app will automatically open at `http://localhost:8501`
   - If not, navigate to the URL shown in your terminal

## Database

- The app uses **SQLite** for data storage
- Database file: `project_tracker.db` (created automatically on first run)
- Located in the same directory as `app.py`

### Backup Your Data
To backup your data, simply copy the `project_tracker.db` file to a safe location.

## Deployment to Streamlit Cloud

### Steps:

1. **Push your code to GitHub**
   - Create a new repository on GitHub
   - Push this project to the repository

2. **Deploy on Streamlit Cloud**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Sign in with your GitHub account
   - Click "New app"
   - Select your repository, branch, and `app.py`
   - Click "Deploy"

### Important Notes for Cloud Deployment:

⚠️ **Data Persistence**: SQLite databases on Streamlit Cloud are **ephemeral** and will reset on each deployment or app restart. For production use, consider:
- Using a cloud database (PostgreSQL, MySQL)
- Implementing data export/import functionality
- Using Streamlit Cloud secrets for connection strings

## Project Structure

```
streamlit-project-tracker/
├── app.py                  # Main application file
├── requirements.txt        # Python dependencies
├── README.md              # This file
└── project_tracker.db     # SQLite database (created on first run)
```

## Usage Tips

1. **Start with Projects**: Add your projects first in the "Project Intake" tab
2. **Add Milestones**: Once projects are created, add milestones in the "Milestones" tab
3. **Assign Resources**: Assign team members to projects in the "Resources" tab
4. **Monitor Progress**: Use the "Dashboard" tab for a quick overview

## Customization

The app is designed to be easily customizable. You can:
- Modify status options in the project intake form
- Add new milestone types
- Extend the dashboard with custom charts
- Add new tabs for additional functionality

## Support

For issues or questions, please refer to the [Streamlit documentation](https://docs.streamlit.io).

---

**Built with ❤️ using Streamlit**
