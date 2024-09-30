import sqlite3

# Create a connection to SQLite database
conn = sqlite3.connect('ordering.db')
c = conn.cursor()

# Create tables based on your provided schema

# tbl_DietaryOption
c.execute('''CREATE TABLE IF NOT EXISTS tbl_DietaryOption (
    Dietary_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Dietary VARCHAR NOT NULL
);''')

# tbl_Gender
c.execute('''CREATE TABLE IF NOT EXISTS tbl_Gender (
    Gender_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Gender VARCHAR NOT NULL
);''')

# tbl_Meal
c.execute('''CREATE TABLE IF NOT EXISTS tbl_Meal (
    Meal_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Meal VARCHAR NOT NULL
);''')

# tbl_Students
c.execute('''CREATE TABLE IF NOT EXISTS tbl_Students (
    Student_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Name VARCHAR NOT NULL,
    Surname VARCHAR NOT NULL,
    Gender_ID_FK INTEGER NOT NULL,
    Grade INTEGER NOT NULL,
    Border BOOLEAN NOT NULL,
    Dietary_ID_FK INTEGER NOT NULL,
    Email VARCHAR NOT NULL,
    Password VARCHAR NOT NULL,
    FOREIGN KEY (Gender_ID_FK) REFERENCES tbl_Gender(Gender_ID),
    FOREIGN KEY (Dietary_ID_FK) REFERENCES tbl_DietaryOption(Dietary_ID)
);''')

# tbl_Teachers
c.execute('''CREATE TABLE IF NOT EXISTS tbl_Teachers (
    Teacher_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Name VARCHAR NOT NULL,
    Surname VARCHAR NOT NULL,
    Email VARCHAR NOT NULL,
    Password VARCHAR NOT NULL
);''')

# tbl_User
c.execute('''CREATE TABLE IF NOT EXISTS tbl_User (
    User_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Name VARCHAR NOT NULL,
    Surname VARCHAR NOT NULL,
    Email VARCHAR NOT NULL,
    Password VARCHAR NOT NULL
);''')

# tbl_Groups
c.execute('''CREATE TABLE IF NOT EXISTS tbl_Groups (
    Group_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Teacher_ID_FK INTEGER NOT NULL,
    GroupName VARCHAR NOT NULL,
    FOREIGN KEY (Teacher_ID_FK) REFERENCES tbl_Teachers(Teacher_ID)
);''')

# tbl_Groups_Students
c.execute('''CREATE TABLE IF NOT EXISTS tbl_Groups_Students (
    Group_ID_FK INTEGER NOT NULL,
    Student_ID_FK INTEGER NOT NULL,
    PRIMARY KEY (Group_ID_FK, Student_ID_FK),
    FOREIGN KEY (Group_ID_FK) REFERENCES tbl_Groups(Group_ID),
    FOREIGN KEY (Student_ID_FK) REFERENCES tbl_Students(Student_ID)
);''')

# tbl_Orders
c.execute('''CREATE TABLE IF NOT EXISTS tbl_Orders (
    Order_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    OrderDate DATE NOT NULL,
    Meal_ID_FK INTEGER NOT NULL,
    Teacher_ID_FK INTEGER,
    Student_ID_FK INTEGER,
    MealDate DATE NOT NULL,
    Notes VARCHAR,
    FOREIGN KEY (Meal_ID_FK) REFERENCES tbl_Meal(Meal_ID),
    FOREIGN KEY (Teacher_ID_FK) REFERENCES tbl_Teachers(Teacher_ID),
    FOREIGN KEY (Student_ID_FK) REFERENCES tbl_Students(Student_ID)
);''')

# tbl_Orders_Group
c.execute('''CREATE TABLE IF NOT EXISTS tbl_Orders_Group (
    Order_ID_FK INTEGER NOT NULL,
    Group_ID_FK INTEGER,
    Student_ID_FK INTEGER,
    PRIMARY KEY (Order_ID_FK, Group_ID_FK),
    FOREIGN KEY (Order_ID_FK) REFERENCES tbl_Orders(Order_ID),
    FOREIGN KEY (Group_ID_FK) REFERENCES tbl_Groups(Group_ID),
    FOREIGN KEY (Student_ID_FK) REFERENCES tbl_Students(Student_ID)
);''')

# Commit changes and close connection
conn.commit()
conn.close()

print("Database setup complete!")
