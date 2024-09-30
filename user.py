import sqlite3
import streamlit as st
import pandas as pd

# Utility function to fetch data
def fetch_data(query, params=()):
    conn = sqlite3.connect('ordering.db', check_same_thread=False)
    c = conn.cursor()
    c.execute(query, params)
    data = c.fetchall()
    conn.close()
    return data

# Utility function to insert data
def insert_data(query, params):
    conn = sqlite3.connect('ordering.db', check_same_thread=False)
    c = conn.cursor()
    c.execute(query, params)
    conn.commit()
    conn.close()

# Utility function to get the foreign key (ID) for a given value from a table
def get_foreign_key_value(table, id_column, value_column, value):
    query = f"SELECT {id_column} FROM {table} WHERE {value_column} = ?"
    result = fetch_data(query, (value,))
    return result[0][0] if result else None

# Function to display user interface
def show_user_interface():
    # Sidebar menu for navigation
    menu = st.sidebar.selectbox(
        "Menu",
        ["Bookings", "Import Students", "Dietary Options", "Meals"]
    )

    # Bookings section
    if menu == "Bookings":
        st.title("Bookings")

        # Fetch and display all orders with required fields
        query = '''
            SELECT 
            tbl_Orders.Order_ID, 
            tbl_Students.Student_ID, 
            tbl_Orders.MealDate,
            tbl_Meal.Meal, 
            tbl_Students.Name || ' ' || tbl_Students.Surname AS StudentName,
            tbl_Students.Grade, 
            tbl_Students.Border, 
            tbl_Groups.GroupName
        FROM 
            tbl_Orders
        LEFT JOIN 
            tbl_Orders_Group ON tbl_Orders.Order_ID = tbl_Orders_Group.Order_ID_FK
        LEFT JOIN 
            tbl_Meal ON tbl_Orders.Meal_ID_FK = tbl_Meal.Meal_ID
        LEFT JOIN 
            tbl_Groups_Students ON tbl_Orders_Group.Group_ID_FK = tbl_Groups_Students.Group_ID_FK
        LEFT JOIN 
            tbl_Students ON tbl_Groups_Students.Student_ID_FK = tbl_Students.Student_ID
        LEFT JOIN 
            tbl_Groups ON tbl_Orders_Group.Group_ID_FK = tbl_Groups.Group_ID

        '''
        bookings = fetch_data(query)
        
        # Convert to DataFrame for better display
        bookings = pd.DataFrame(bookings, columns=["Oder_ID", "Order_ID", "Meal Date", "Meal", "StudentName", "Grade", "Border", "Group"])
        st.dataframe(bookings)

    # Import Students section
    elif menu == "Import Students":
        st.title("Import Students")
        st.subheader("Current Students in the System")
        
        # Modify the SQL query to fetch the data
        query = '''
            SELECT tbl_Students.Student_ID, tbl_Students.Name || ' ' || tbl_Students.Surname AS StudentName, 
                tbl_Gender.Gender, tbl_Students.Grade, tbl_Students.Border, tbl_DietaryOption.Dietary,
                tbl_Students.Email
            FROM tbl_Students
            JOIN tbl_Gender ON tbl_Students.Gender_ID_FK = tbl_Gender.Gender_ID
            JOIN tbl_DietaryOption ON tbl_Students.Dietary_ID_FK = tbl_DietaryOption.Dietary_ID
            ORDER BY tbl_Students.Grade ASC, tbl_Students.Surname ASC
        '''
        students = fetch_data(query)
        
        # Convert to DataFrame for better display
        students_df = pd.DataFrame(students, columns=["Student_ID", "Student Name", "Gender", "Grade", "Is Border", "Dietary", "Email"])
        
        st.data_editor(students_df, num_rows='dynamic')

        # File uploader for Excel file
        st.subheader("Import New Students")
        uploaded_file = st.file_uploader("Choose an Excel file", type=["xlsx"])

        if uploaded_file:
            # Read Excel file into a DataFrame
            students_df = pd.read_excel(uploaded_file)

            st.write("Preview of uploaded file:")
            st.dataframe(students_df)

            # Display required columns for student import
            st.write("Required columns in the Excel file: Name, Surname, Gender, Grade, Border, Dietary, Email, Password")

            # Check if all required columns exist in the DataFrame
            required_columns = ['Name', 'Surname', 'Gender', 'Grade', 'Border', 'Dietary', 'Email', 'Password']
            if not all(column in students_df.columns for column in required_columns):
                st.error("Missing one or more required columns in the Excel file.")
            else:
                if st.button("Import Students"):
                    for _, row in students_df.iterrows():
                        # Handle Gender_ID_FK
                        gender = row['Gender']
                        gender_id = get_foreign_key_value('tbl_Gender', 'Gender_ID', 'Gender', gender)
                        if gender_id is None:
                            st.error(f"Gender '{gender}' does not exist in the database.")
                            continue  # Skip this row if gender is invalid
                        
                        # Handle Dietary_ID_FK
                        dietary = row['Dietary']
                        dietary_id = get_foreign_key_value('tbl_DietaryOption', 'Dietary_ID', 'Dietary', dietary)
                        if dietary_id is None:
                            st.error(f"Dietary option '{dietary}' does not exist in the database.")
                            continue  # Skip this row if dietary option is invalid

                        # Insert data into tbl_Students
                        insert_data('''
                            INSERT INTO tbl_Students (Name, Surname, Gender_ID_FK, Grade, Border, Dietary_ID_FK, Email, Password)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (row['Name'], row['Surname'], gender_id, row['Grade'], row['Border'], dietary_id, row['Email'], row['Password']))

                    st.success("Students imported successfully!")

    # Dietary Options section
    elif menu == "Dietary Options":
        st.title("Dietary Options")

        # Fetch and display existing dietary options
        dietary_options = fetch_data("SELECT Dietary_ID, Dietary FROM tbl_DietaryOption")
        dietary_df = pd.DataFrame(dietary_options, columns=["Dietary ID", "Dietary"])
        st.table(dietary_df)

        # Add new dietary option
        new_dietary = st.text_input("Add New Dietary Option")
        if st.button("Add Dietary Option"):
            insert_data("INSERT INTO tbl_DietaryOption (Dietary) VALUES (?)", (new_dietary,))
            st.success(f"Dietary option '{new_dietary}' added successfully!")
        
        # Edit existing dietary option
        edit_dietary_id = st.number_input("Enter Dietary ID to Edit", min_value=1)
        edit_dietary_name = st.text_input("New Dietary Option Name")
        if st.button("Edit Dietary Option"):
            insert_data("UPDATE tbl_DietaryOption SET Dietary = ? WHERE Dietary_ID = ?", (edit_dietary_name, edit_dietary_id))
            st.success(f"Dietary option '{edit_dietary_id}' updated to '{edit_dietary_name}'.")

    # Meals section
    elif menu == "Meals":
        st.title("Meals")

        # Fetch and display existing meal options
        meals = fetch_data("SELECT Meal_ID, Meal FROM tbl_Meal")
        meals_df = pd.DataFrame(meals, columns=["Meal ID", "Meal"])
        st.table(meals_df)

        # Add new meal
        new_meal = st.text_input("Add New Meal")
        if st.button("Add Meal"):
            insert_data("INSERT INTO tbl_Meal (Meal) VALUES (?)", (new_meal,))
            st.success(f"Meal '{new_meal}' added successfully!")
        
        # Edit existing meal
        edit_meal_id = st.number_input("Enter Meal ID to Edit", min_value=1)
        edit_meal_name = st.text_input("New Meal Name")
        if st.button("Edit Meal"):
            insert_data("UPDATE tbl_Meal SET Meal = ? WHERE Meal_ID = ?", (edit_meal_name, edit_meal_id))
            st.success(f"Meal '{edit_meal_id}' updated to '{edit_meal_name}'.")
