import sqlite3
import streamlit as st
import user  # Import the user interface
import teacher  # Import the teacher interface
import student  # Import the student interface

# Initialize session state variables for login status, user type, and user ID
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_type' not in st.session_state:
    st.session_state.user_type = None
if 'first_name' not in st.session_state:
    st.session_state.first_name = ""
if 'last_name' not in st.session_state:
    st.session_state.last_name = ""
if 'user_id' not in st.session_state:  # Explicitly initializing user_id
    st.session_state.user_id = None

# Utility function to check user credentials from multiple tables
def check_login(email, password):
    conn = sqlite3.connect('ordering.db', check_same_thread=False)
    c = conn.cursor()

    # Check tbl_User
    c.execute("SELECT 'User' AS UserType, Name, Surname, User_ID FROM tbl_User WHERE Email = ? AND Password = ?", (email, password))
    user = c.fetchone()
    if user:
        conn.close()
        return user

    # Check tbl_Teachers
    c.execute("SELECT 'Teacher' AS UserType, Name, Surname, Teacher_ID FROM tbl_Teachers WHERE Email = ? AND Password = ?", (email, password))
    teacher = c.fetchone()
    if teacher:
        conn.close()
        return teacher

    # Check tbl_Students
    c.execute("SELECT 'Student' AS UserType, Name, Surname, Student_ID FROM tbl_Students WHERE Email = ? AND Password = ?", (email, password))
    student = c.fetchone()
    if student:
        conn.close()
        return student

    # If no match, return None
    conn.close()
    return None

# Streamlit UI for Login Page
def login_page():
    st.title("Login Page")

    # Input fields for email and password
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    # Button for login action
    if st.button("Login"):
        # Check credentials against the database
        user_data = check_login(email, password)  # Store the result in a variable
        
        if user_data:
            user_type = user_data[0]  # 'User', 'Teacher', or 'Student'
            first_name = user_data[1]
            last_name = user_data[2]
            user_id = user_data[3]  # Store the user ID (User_ID, Teacher_ID, or Student_ID)

            # Store login info in session state
            st.session_state.logged_in = True
            st.session_state.user_type = user_type
            st.session_state.first_name = first_name
            st.session_state.last_name = last_name
            st.session_state.user_id = user_id  # Store the specific user ID (for queries)

            st.success(f"Welcome {first_name} {last_name}! You are logged in as a {user_type}.")
        else:
            st.error("Invalid email or password. Please try again.")

# Main app logic
if st.session_state.logged_in:
    # Display the logged-in user's name and role in the sidebar
    st.sidebar.title(f"Welcome, {st.session_state.first_name} {st.session_state.last_name}")
    st.sidebar.markdown(f"**Role**: {st.session_state.user_type}")

    # Show the correct interface based on the user type
    if st.session_state.user_type == 'User':
        user.show_user_interface()  # Call the correct function for general users
    elif st.session_state.user_type == 'Teacher':
        if st.session_state.user_id:  # Ensure the teacher's ID is not None
            teacher.show_teacher_interface(st.session_state.user_id)  # Pass the teacher's ID to the teacher interface
        else:
            st.error("Teacher ID is not available.")
    elif st.session_state.user_type == 'Student':
        if st.session_state.user_id:  # Ensure the student's ID is not None
            student.show_student_interface(st.session_state.user_id)  # Pass the student's ID to the student interface
        else:
            st.error("Student ID is not available.")
else:
    # If not logged in, show the login page
    login_page()
