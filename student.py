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

def execute_query_and_return_id(query, params):
    conn = sqlite3.connect('ordering.db', check_same_thread=False)
    c = conn.cursor()
    c.execute(query, params)
    conn.commit()
    last_id = c.lastrowid  # Get the last inserted ID (Order_ID)
    conn.close()
    return last_id

# Utility function to insert data
def execute_query(query, params):
    conn = sqlite3.connect('ordering.db', check_same_thread=False)
    c = conn.cursor()
    c.execute(query, params)
    conn.commit()
    conn.close()

# Function to display the student's user interface
def show_student_interface(student_id):
    # Sidebar menu for navigation
    menu = st.sidebar.selectbox(
        "Menu",
        ["Groups", "Bookings"]
    )

    ### 1. Groups ###
    if menu == "Groups":
        st.title("My Groups")

        # Fetch the groups the student belongs to, along with the teacher in charge
        query_groups = '''
            SELECT tbl_Groups.GroupName, tbl_Teachers.Name || ' ' || tbl_Teachers.Surname AS TeacherName
            FROM tbl_Groups_Students
            LEFT JOIN tbl_Groups ON tbl_Groups_Students.Group_ID_FK = tbl_Groups.Group_ID
            LEFT JOIN tbl_Teachers ON tbl_Groups.Teacher_ID_FK = tbl_Teachers.Teacher_ID
            WHERE tbl_Groups_Students.Student_ID_FK = ?
        '''
        student_groups = fetch_data(query_groups, (student_id,))
        student_groups_df = pd.DataFrame(student_groups, columns=["Group Name", "Teacher In Charge"])

        # Display groups in a table
        st.subheader("Groups I'm a Part Of")
        st.dataframe(student_groups_df, hide_index=True)

    ### 2. Bookings ###
    elif menu == "Bookings":
        st.title("My Bookings")

        # Fetch upcoming bookings for the student
        today_date = datetime.now().strftime("%Y-%m-%d")
        query_upcoming_bookings = '''
            SELECT 
                tbl_Meal.Meal, 
                tbl_Orders.MealDate,
                COALESCE(tbl_Orders.Teacher_ID_FK, tbl_Orders.Student_ID_FK) AS BookedBy
            FROM 
                tbl_Orders
            LEFT JOIN 
                tbl_Meal ON tbl_Orders.Meal_ID_FK = tbl_Meal.Meal_ID
            LEFT JOIN 
                tbl_Orders_Group ON tbl_Orders.Order_ID = tbl_Orders_Group.Order_ID_FK
            LEFT JOIN 
                tbl_Groups_Students ON tbl_Orders_Group.Group_ID_FK = tbl_Groups_Students.Group_ID_FK
            WHERE 
                tbl_Orders.Student_ID_FK = ? AND tbl_Orders.MealDate >= ?
            
            UNION

            SELECT 
                tbl_Meal.Meal, 
                tbl_Orders.MealDate,
                COALESCE(tbl_Orders.Teacher_ID_FK, tbl_Orders.Student_ID_FK) AS BookedBy
            FROM 
                tbl_Orders
            LEFT JOIN 
                tbl_Meal ON tbl_Orders.Meal_ID_FK = tbl_Meal.Meal_ID
            LEFT JOIN 
                tbl_Orders_Group ON tbl_Orders.Order_ID = tbl_Orders_Group.Order_ID_FK
            LEFT JOIN 
                tbl_Groups_Students ON tbl_Orders_Group.Group_ID_FK = tbl_Groups_Students.Group_ID_FK
            WHERE 
                tbl_Groups_Students.Student_ID_FK = ? AND tbl_Orders.MealDate >= ?
            
            ORDER BY 
                MealDate ASC
        '''


        upcoming_bookings = fetch_data(query_upcoming_bookings, (student_id, today_date, student_id, today_date))
        upcoming_bookings_df = pd.DataFrame(upcoming_bookings, columns=["Meal", "Meal Date", "Booked By"])

        # Display the upcoming bookings in a table
        st.subheader("Upcoming Bookings")
        st.dataframe(upcoming_bookings_df, hide_index=True)

        ### Add New Booking ###
        st.subheader("Add New Booking")

        # Fetch the available meals for the dropdown
        query_meals = "SELECT Meal_ID, Meal FROM tbl_Meal"
        meals = fetch_data(query_meals)
        meal_dict = {meal_name: meal_id for meal_id, meal_name in meals}
        selected_meal = st.selectbox("Select Meal", list(meal_dict.keys()))

        # User selects the meal date
        meal_date = st.date_input("Select Meal Date")

        # Button to add booking
        if st.button("Add Booking"):
            # Insert the booking into the tbl_Orders table
            order_date = datetime.now().strftime("%d/%m/%Y %H:%M:%S")  # current date and time
            meal_id_fk = meal_dict[selected_meal]  # selected meal ID

            # Check for existing bookings for the same meal and date (individually or through a group)
            query_check_existing = '''
                SELECT COUNT(*)
                FROM tbl_Orders
                WHERE Student_ID_FK = ? AND Meal_ID_FK = ? AND MealDate = ?

                UNION

                SELECT COUNT(*)
                FROM tbl_Orders
                JOIN tbl_Orders_Group ON tbl_Orders.Order_ID = tbl_Orders_Group.Order_ID_FK
                JOIN tbl_Groups_Students ON tbl_Orders_Group.Group_ID_FK = tbl_Groups_Students.Group_ID_FK
                WHERE tbl_Groups_Students.Student_ID_FK = ? AND tbl_Orders.Meal_ID_FK = ? AND tbl_Orders.MealDate = ?
            '''

            # Execute the query and pass the parameters twice for individual and group bookings
            existing_booking_count = fetch_data(query_check_existing, (student_id, meal_id_fk, meal_date, student_id, meal_id_fk, meal_date))

            # Sum the results from both individual and group bookings
            total_existing_bookings = sum([row[0] for row in existing_booking_count])

            # If the student already has a booking for the meal, show an error
            if total_existing_bookings > 0:
                st.error(f"You have already booked this meal for {meal_date}.")
            else:
                # Step 1: Insert into tbl_Orders and get the new Order_ID
                add_order_query = '''
                    INSERT INTO tbl_Orders (OrderDate, Meal_ID_FK, Student_ID_FK, Teacher_ID_FK, MealDate)
                    VALUES (?, ?, ?, NULL, ?)
                '''
                new_order_id = execute_query_and_return_id(add_order_query, (order_date, meal_id_fk, student_id, meal_date))

                # Step 2: Insert the booking into tbl_Orders_Group
                add_order_group_query = '''
                    INSERT INTO tbl_Orders_Group (Order_ID_FK, Group_ID_FK, Student_ID_FK)
                    VALUES (?, NULL, ?)
                '''
                execute_query(add_order_group_query, (new_order_id, student_id))

                st.success(f"Booking for {selected_meal} on {meal_date} added successfully!")
                st.rerun()

