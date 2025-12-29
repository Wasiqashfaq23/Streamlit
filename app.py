import streamlit as st
import requests
from datetime import datetime
from DataStructres import PriorityQueue, Stack

N8N_WEBHOOK_URL = "https://hello12345.app.n8n.cloud/webhook/task-event"

def trigger_n8n(task):
    """Send task to n8n webhook and return calendar event ID if created"""
    payload = {"task": task}  # Always wrap in task object
    try:
        response = requests.post(N8N_WEBHOOK_URL, json=payload, timeout=10)
        if response.ok:
            data = response.json()
            # Check if calendar event was created
            if data.get("success") and "calendarEventId" in data:
                return data["calendarEventId"]
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"n8n connection error: {e}")
        return None


st.set_page_config(
    page_title="Task Manager",
    page_icon="📝",
    layout="wide"
)

st.markdown("""
<style>
    .priority-1 {
        background-color: #ff4444;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
        color: white;
    }
    .priority-2 {
        background-color: #ff8800;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
        color: white;
    }
    .priority-3 {
        background-color: #ffbb33;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
        color: white;
    }
    .priority-4 {
        background-color: #00C851;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
        color: white;
    }
    .priority-5 {
        background-color: #33b5e5;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
        color: white;
    }
    .footer {
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        background-color: #0e1117;
        color: #fafafa;
        text-align: center;
        padding: 10px;
        border-top: 2px solid #ff4b4b;
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    if 'pending' not in st.session_state:
        st.session_state.pending = PriorityQueue()
    if 'completed' not in st.session_state:
        st.session_state.completed = Stack()
    if 'counter' not in st.session_state:
        st.session_state.counter = 0

initialize_session_state()

def get_priority_badge(priority):
    colors = {
        1: ("🔴 Critical", "#ff4444"),
        2: ("🟠 High", "#ff8800"),
        3: ("🟡 Medium", "#ffbb33"),
        4: ("🟢 Low", "#00C851"),
        5: ("🔵 Very Low", "#33b5e5")
    }
    label, color = colors.get(priority, ("Unknown", "#666666"))
    return f'<span style="background-color: {color}; color: white; padding: 5px 10px; border-radius: 5px; font-weight: bold;">{label}</span>'

st.title("📝 Task Manager")
st.markdown("**DSA Project**: Priority Queue & Stack Implementation")
st.markdown("---")


with st.sidebar:
    st.header("➕ Add New Task")
    st.markdown("Fill in the details below to add a new task:")
    
    with st.form(key="task_form", clear_on_submit=True):
        task_name = st.text_input("Task Name")
        priority = st.selectbox(
            "Priority Level",
            options=[1, 2, 3, 4, 5],
            format_func=lambda x: {
                1: "🔴 1 - Critical",
                2: "🟠 2 - High",
                3: "🟡 3 - Medium",
                4: "🟢 4 - Low",
                5: "🔵 5 - Very Low"
            }[x]
        )
        deadline_date = st.date_input("Deadline")
        deadline_time = st.time_input("Deadline Time")
        
        submit_button = st.form_submit_button("Add Task", use_container_width=True)
        
        if submit_button:
            if task_name.strip():
                deadline_dt = datetime.combine(deadline_date, deadline_time)
                deadline_str = deadline_dt.strftime("%Y-%m-%dT%H:%M:%S")

                task = {
                    'id': st.session_state.counter,
                    'name': task_name.strip(),
                    'priority': priority,
                    'deadline': deadline_str,
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'calendarEventId': None
                }
                
                # Send to n8n and get calendar event ID
                calendar_id = trigger_n8n(task)
                if calendar_id:
                    task["calendarEventId"] = calendar_id
                    st.success(f"Task added and calendar event created!")
                else:
                    st.warning("Task added but calendar sync failed")
                
                st.session_state.pending.insert(task)
                st.session_state.counter += 1
                st.rerun()
            else:
                st.error("❌ Please enter a task name!")
            
    st.markdown("---")
    st.subheader("📊 Statistics")
    st.metric("Pending Tasks", st.session_state.pending.size())
    st.metric("Completed Tasks", st.session_state.completed.size())

tab1, tab2 = st.tabs(["📋 Pending Tasks", "✅ Completed Tasks"])

with tab1:
    st.subheader("Pending Tasks Queue")
    st.markdown("Tasks are prioritized from highest (1) to lowest (5) priority.")
    
    if st.session_state.pending.isEmpty():
        st.info("🎉 No pending tasks! Add a task from the sidebar to get started.")
    else:
        all_tasks = st.session_state.pending.getAllTasks()
        sorted_tasks = sorted(all_tasks, key=lambda x: (x['priority'], x['timestamp']))
        
        for idx, task in enumerate(sorted_tasks):
            col1, col2 = st.columns([4, 1])
            
            with col1:
                calendar_status = "📅" if task.get("calendarEventId") else "⚠️"
                st.markdown(f"""
                <div class="priority-{task['priority']}">
                    <h4 style="margin: 0;">{calendar_status} {task['name']}</h4>
                    <p style="margin: 5px 0 0 0; font-size: 0.9em;">
                        {get_priority_badge(task['priority'])} | 
                        <span style="opacity: 0.8;">
                            📅 Created: {task['timestamp']}<br>
                            ⏰ Deadline: {task.get('deadline', 'N/A')}
                        </span>
                    </p>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                if st.button("✓ Complete", key=f"complete_{task['id']}", use_container_width=True):
                    completed_task = st.session_state.pending.extract_min()
                    if completed_task:
                        completed_task['completed_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        st.session_state.completed.push(completed_task)
                        
                        # Delete from calendar if it exists
                        if completed_task.get("calendarEventId"):
                            # Send the completed task to n8n for deletion
                            trigger_n8n(completed_task)
                        
                        st.success(f"✅ Completed: {completed_task['name']}")
                        st.rerun()

with tab2:
    st.subheader("Completed Tasks Stack")
    st.markdown("Most recently completed tasks appear at the top (LIFO - Last In, First Out).")
    
    if st.session_state.completed.isEmpty():
        st.info("📭 No completed tasks yet. Complete some tasks to see them here!")
    else:
        all_completed = st.session_state.completed.getAllTasks()
        
        for idx, task in enumerate(reversed(all_completed)):
            col1, col2 = st.columns([4, 1])
            
            with col1:
                st.markdown(f"""
                <div class="priority-{task['priority']}" style="opacity: 0.8;">
                    <h4 style="margin: 0; text-decoration: line-through;">{task['name']}</h4>
                    <p style="margin: 5px 0 0 0; font-size: 0.9em;">
                        {get_priority_badge(task['priority'])} | 
                        <span style="opacity: 0.8;">
                            📅 Created: {task['timestamp']}<br>
                            ⏰ Deadline: {task.get('deadline', 'N/A')}<br>
                            ✓ Completed: {task.get('completed_at', 'N/A')}
                        </span>
                    </p>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                if st.button("↶ Undo", key=f"undo_{task['id']}", use_container_width=True):
                    undone_task = st.session_state.completed.pop()

                    if undone_task:
                        undone_task.pop("completed_at", None)      # remove completion flag first
                        undone_task["calendarEventId"] = None      # force calendar to re-create on undo

                        calendar_id = trigger_n8n(undone_task)
                        undone_task["calendarEventId"] = calendar_id if calendar_id else None
                        st.session_state.pending.insert(undone_task)
                        st.info(f"↶ Task moved back to pending: {undone_task['name']}")
                        st.rerun()

st.markdown("""
<div class="footer">
    <p style="margin: 0;">
        <strong>Task Manager - DSA Project</strong> | 
        Built with Streamlit 🎈 | 
        Custom Priority Queue (Min-Heap) & Stack Implementation | 
        © 2024
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("<br><br>", unsafe_allow_html=True)