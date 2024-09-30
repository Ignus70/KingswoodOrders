import sqlite3
import streamlit as st
import pandas as pd
from datetime import datetime

# Utility function to fetch data
def fetch_data(query, params=()):
    conn = sqlite3.connect('ordering.db', check_same_thread=False)
    c = conn.cursor()
    c.execute(query, params)
    data = c.fetchall()
    conn.close()
    return data

# Utility function to insert or update data
def execute_query(query, params):
    conn = sqlite3.connect('ordering.db', check_same_thread=False)
    c = conn.cursor()
    c.execute(query, params)
    conn.commit()
    conn.close()

# Utility function to delete data
def delete_query(query, params):
    conn = sqlite3.connect('ordering.db', check_same_thread=False)
    c = conn.cursor()
    c.execute(query, params)
    conn.commit()
    conn.close()

# Function to display the teacher's user interface
def show_teacher_interface(teacher_id):
    # Sidebar menu for navigation
    menu = st.sidebar.selectbox(
        "Menu",
        ["Manage Groups", "Add New Group", "Add Bookings"]
    )

    # Check if the teacher_id is valid (not None)
    if not teacher_id:
        st.error("Teacher ID is not available. Please log in again.")
        return  # Stop execution if the teacher ID is not valid

    ### 1. Manage Existing Groups ###
    if menu == "Manage Groups":
        st.title("Manage Existing Groups")

        # Fetch the teacher's groups
        groups_query = "SELECT Group_ID, GroupName FROM tbl_Groups WHERE Teacher_ID_FK = ?"
        groups = fetch_data(groups_query, (teacher_id,))
        if groups:
            group_dict = {group_name: group_id for group_id, group_name in groups}
            selected_group = st.selectbox("Select a Group to Manage", list(group_dict.keys()))
            
            if selected_group:
                group_id = group_dict[selected_group]

                # Create two columns
                col1, col2 = st.columns([3, 1])

                # Show students in the selected group (in the left column)
                with col1:
                    st.subheader(f"Students in {selected_group}")

                    query_students_in_group = '''
                        SELECT tbl_Students.Name || ' ' || tbl_Students.Surname AS StudentName, 
                               tbl_Students.Grade, tbl_Gender.Gender
                        FROM tbl_Groups_Students
                        JOIN tbl_Students ON tbl_Groups_Students.Student_ID_FK = tbl_Students.Student_ID
                        JOIN tbl_Gender ON tbl_Students.Gender_ID_FK = tbl_Gender.Gender_ID
                        WHERE tbl_Groups_Students.Group_ID_FK = ?
                        ORDER BY tbl_Students.Grade ASC, tbl_Students.Surname ASC
                    '''
                    students_in_group = fetch_data(query_students_in_group, (group_id,))
                    students_in_group_df = pd.DataFrame(students_in_group, columns=["Student Name", "Grade", "Gender"])

                    # Display DataFrame
                    st.dataframe(students_in_group_df, hide_index=True)

                # Add a delete group option (in the right column)
                with col2:
                    st.subheader("Delete Group")

                    # Initialize a session state for confirmation
                    if "confirm_delete" not in st.session_state:
                        st.session_state.confirm_delete = False

                    # First button to initiate deletion process
                    if st.button(f"Delete {selected_group}"):
                        st.session_state.confirm_delete = True  # Trigger the confirmation state

                    # If confirmation is triggered, show the confirm button
                    if st.session_state.confirm_delete:
                        if st.button(f"Confirm Deletion of {selected_group}"):
                            # Delete the group and associated students
                            delete_group_query = '''
                                DELETE FROM tbl_Groups WHERE Group_ID = ?
                            '''
                            delete_query(delete_group_query, (group_id,))
                            # Optionally, delete associated students in the group
                            delete_students_in_group_query = '''
                                DELETE FROM tbl_Groups_Students WHERE Group_ID_FK = ?
                            '''
                            delete_query(delete_students_in_group_query, (group_id,))
                            st.success(f"Group '{selected_group}' and its associated students have been deleted.")
                            st.session_state.confirm_delete = False  # Reset the confirmation state
                            st.rerun()  # Rerun the app to refresh the state

                ### Add New Students to the Group (similar to your original logic) ###
                st.subheader(f"Add Students to {selected_group}")

                query_all_students = '''
                    SELECT tbl_Students.Student_ID, tbl_Students.Name || ' ' || tbl_Students.Surname AS StudentName,
                           tbl_Students.Grade, tbl_Gender.Gender
                    FROM tbl_Students
                    JOIN tbl_Gender ON tbl_Students.Gender_ID_FK = tbl_Gender.Gender_ID
                    WHERE tbl_Students.Student_ID NOT IN (
                        SELECT Student_ID_FK FROM tbl_Groups_Students WHERE Group_ID_FK = ?
                    )
                    ORDER BY tbl_Students.Grade ASC, tbl_Students.Surname ASC
                '''
                available_students = fetch_data(query_all_students, (group_id,))
                available_students_df = pd.DataFrame(available_students, columns=["Student ID", "Student Name", "Grade", "Gender"])

                # Collect the rows the user wants to add to the group
                selected_rows = st.dataframe(
                                available_students_df,
                                use_container_width=True,
                                hide_index=True,
                                on_select="rerun",
                                selection_mode='multi-row',
                                height=600
                            ).selection.rows
                
                selected_student_ids = available_students_df.loc[selected_rows, 'Student ID'].tolist()
                selected_student_names = available_students_df['Student Name'][selected_rows]
                
                st.dataframe(selected_student_names)

                # Button to add selected students to the group
                if st.button("Add Selected Students to Group"):
                    for student_id in selected_student_ids:
                        add_student_query = '''
                            INSERT INTO tbl_Groups_Students (Group_ID_FK, Student_ID_FK) VALUES (?, ?)
                        '''
                        execute_query(add_student_query, (group_id, student_id))
                    st.success(f"Added selected students to {selected_group}")
                    st.rerun()

    ### 2. Add New Group ### (Same as original logic)
    elif menu == "Add New Group":
        st.title("Create New Group")

        # Input for group name
        new_group_name = st.text_input("Group Name")

        if st.button("Create Group"):
            if new_group_name:
                # Create the group by inserting it into the tbl_Groups table with Teacher_ID_FK
                create_group_query = "INSERT INTO tbl_Groups (Teacher_ID_FK, GroupName) VALUES (?, ?)"
                execute_query(create_group_query, (teacher_id, new_group_name))
                st.success(f"Group '{new_group_name}' created successfully!")

                # Get the newly created group ID
                new_group_id_query = "SELECT Group_ID FROM tbl_Groups WHERE GroupName = ? AND Teacher_ID_FK = ?"
                new_group_id = fetch_data(new_group_id_query, (new_group_name, teacher_id))[0][0]

                st.subheader(f"Assign Students to '{new_group_name}'")

                # Fetch all available students (not yet in the group)
                query_all_students = '''
                    SELECT tbl_Students.Student_ID, tbl_Students.Name || ' ' || tbl_Students.Surname AS StudentName,
                           tbl_Students.Grade, tbl_Gender.Gender
                    FROM tbl_Students
                    JOIN tbl_Gender ON tbl_Students.Gender_ID_FK = tbl_Gender.Gender_ID
                    WHERE tbl_Students.Student_ID NOT IN (
                        SELECT Student_ID_FK FROM tbl_Groups_Students WHERE Group_ID_FK = ?
                    )
                    ORDER BY tbl_Students.Grade ASC, tbl_Students.Surname ASC
                '''
                available_students = fetch_data(query_all_students, (new_group_id,))
                available_students_df = pd.DataFrame(available_students, columns=["Student ID", "Student Name", "Grade", "Gender"])

                # Collect the rows the user wants to add to the group
                selected_rows = st.dataframe(
                                available_students_df,
                                use_container_width=True,
                                hide_index=True,
                                selection_mode='multi-row',
                                height=600
                            ).selection.rows
                
                selected_student_ids = available_students_df.loc[selected_rows, 'Student ID'].tolist()
                selected_student_names = available_students_df.loc[selected_rows, 'Student Name']
                
                st.write(selected_student_names)

                # Button to add selected students to the group
                if st.button("Add Selected Students to Group"):
                    for student_id in selected_student_ids:
                        add_student_query = '''
                            INSERT INTO tbl_Groups_Students (Group_ID_FK, Student_ID_FK) VALUES (?, ?)
                        '''
                        execute_query(add_student_query, (new_group_id, student_id))
                    st.success(f"Added selected students to '{new_group_name}'")
                    st.rerun()

    ### 3. Add Bookings Page ###
    if menu == "Add Bookings":
        st.title("Add New Booking")

        # Fetch the teacher's groups for the dropdown (Group_ID_FK)
        query_groups = "SELECT Group_ID, GroupName FROM tbl_Groups WHERE Teacher_ID_FK = ?"
        groups = fetch_data(query_groups, (teacher_id,))
        group_dict = {group_name: group_id for group_id, group_name in groups}
        selected_group = st.selectbox("Select Group", list(group_dict.keys()))

        # Show the students from the selected group
        group_id_fk = group_dict[selected_group]  # Selected group ID
        query_students_in_group = '''
            SELECT tbl_Students.Student_ID, tbl_Students.Name || ' ' || tbl_Students.Surname AS StudentName, 
                   tbl_Students.Grade, tbl_Gender.Gender
            FROM tbl_Groups_Students
            JOIN tbl_Students ON tbl_Groups_Students.Student_ID_FK = tbl_Students.Student_ID
            JOIN tbl_Gender ON tbl_Students.Gender_ID_FK = tbl_Gender.Gender_ID
            WHERE tbl_Groups_Students.Group_ID_FK = ?
            ORDER BY tbl_Students.Grade ASC, tbl_Students.Surname ASC
        '''

        # Fetch the meals for the dropdown (Meal_ID_FK)
        query_meals = "SELECT Meal_ID, Meal FROM tbl_Meal"
        meals = fetch_data(query_meals)
        meal_dict = {meal_name: meal_id for meal_id, meal_name in meals}
        selected_meal = st.selectbox("Select Meal", list(meal_dict.keys()))

        students_in_group = fetch_data(query_students_in_group, (group_id_fk,))
        students_in_group_df = pd.DataFrame(students_in_group, columns=["Student ID", "Student Name", "Grade", "Gender"])

        # Current date and time for orderDate (automatically set)
        order_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # User selects the meal date
        meal_date = st.date_input("Select Meal Date")

        # Prepare the data for insertion
        meal_id_fk = meal_dict[selected_meal]  # Selected meal ID

        # Display the students in the selected group
        st.subheader(f"Students in {selected_group}")
        st.dataframe(students_in_group_df, hide_index=True)

        # Button to add booking
        if st.button("Add Booking"):
    # Step 1: Check for existing bookings for this meal and date for both individual and group bookings
            query_check_existing = '''
                SELECT COUNT(*)
                FROM tbl_Orders
                WHERE tbl_Orders.Student_ID_FK = ? AND tbl_Orders.Meal_ID_FK = ? AND tbl_Orders.MealDate = ?

                UNION

                SELECT COUNT(*)
                FROM tbl_Orders
                JOIN tbl_Orders_Group ON tbl_Orders.Order_ID = tbl_Orders_Group.Order_ID_FK
                JOIN tbl_Groups_Students ON tbl_Orders_Group.Group_ID_FK = tbl_Groups_Students.Group_ID_FK
                WHERE tbl_Groups_Students.Student_ID_FK = ? AND tbl_Orders.Meal_ID_FK = ? AND tbl_Orders.MealDate = ?
            '''
            
            # Execute the query and pass the parameters twice (for both queries in the UNION)
            existing_booking_count = fetch_data(query_check_existing, (student_id, meal_id_fk, meal_date, student_id, meal_id_fk, meal_date))
            
            # Sum the results to get the total count of bookings
            total_existing_bookings = sum([row[0] for row in existing_booking_count])

            # If there are existing bookings, notify the user
            if total_existing_bookings > 0:
                st.error(f"You or some students in {selected_group} already have this meal booked for {meal_date}.")
            else:
                # Step 2: Insert into tbl_Orders first
                add_order_query = '''
                    INSERT INTO tbl_Orders (OrderDate, Meal_ID_FK, Teacher_ID_FK, MealDate, Student_ID_FK)
                    VALUES (?, ?, ?, ?, NULL)
                '''
                execute_query(add_order_query, (order_date, meal_id_fk, teacher_id, meal_date))

                # Step 3: Insert into tbl_Orders_Group (associate group with the order)
                add_booking_query = '''
                    INSERT INTO tbl_Orders_Group (Order_ID_FK, Group_ID_FK, Student_ID_FK)
                    SELECT MAX(Order_ID), ?, NULL FROM tbl_Orders
                '''
                execute_query(add_booking_query, (group_id_fk,))

                st.success("Booking added successfully!")
                st.rerun()

        # Show all bookings for the teacher with MealDate >= today
        st.subheader("Upcoming Bookings")
        today_date = datetime.now().strftime("%Y-%m-%d")
        query_bookings = '''
            SELECT tbl_Meal.Meal, tbl_Orders.MealDate, tbl_Groups.GroupName
            FROM tbl_Orders
            JOIN tbl_Meal ON tbl_Orders.Meal_ID_FK = tbl_Meal.Meal_ID
            JOIN tbl_Orders_Group ON tbl_Orders.Order_ID = tbl_Orders_Group.Order_ID_FK
            JOIN tbl_Groups ON tbl_Orders_Group.Group_ID_FK = tbl_Groups.Group_ID
            WHERE tbl_Orders.Teacher_ID_FK = ? AND tbl_Orders.MealDate >= ?
            ORDER BY tbl_Orders.MealDate ASC
        '''
        bookings = fetch_data(query_bookings, (teacher_id, today_date))

        # Display the bookings in a DataFrame
        if bookings:
            bookings_df = pd.DataFrame(bookings, columns=["Meal", "Meal Date", "Group"])
            bookings_df['Meal Date'] = pd.to_datetime(bookings_df['Meal Date'])
            bookings_df['Meal Date'] = bookings_df["Meal Date"].dt.strftime('%a %d/%m/%Y')
            st.dataframe(bookings_df, hide_index=True)
        else:
            st.write("No upcoming bookings.")
