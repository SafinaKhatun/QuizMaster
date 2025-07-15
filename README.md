# Quiz Master  

## Description

Quiz Master is a structured quiz management system designed for admin-led quiz creation and user participation with authentication, role-based access control, and performance tracking through data visualizations.

## Technologies Used

- **Flask (Python)**: Provides a lightweight framework for building web applications.
- **Jinja2**: Allows for dynamic rendering of HTML templates.
- **SQLite**: Used for efficient, lightweight data storage.
- **HTML/CSS/Bootstrap**: Ensures a clean and responsive UI.
- **Flask-Login**: Manages user sessions.

## DB Schema Design

### Reasons for this design:

- Ensures data integrity by using foreign keys for linking subjects, chapters, and quizzes.
- Follows normalization to prevent redundant data storage.
- Allows scalability, ensuring easy expansion for additional features.

## Architecture and Features

### Project Organization:

- **Controllers (Flask Routes)**: Located in `app.py`, handling user authentication, quiz management, and scoring logic.
- **Templates (Frontend)**: Stored in the `templates/` directory, using Jinja2 for rendering dynamic content.
- **Database Models**: Managed in `models.py`, defining the schema and relationships.

### Implemented Features:

- **User  Authentication**: Registration, login, and role-based access control.
- **Quiz Management**: Admin can create subjects, chapters, quizzes, and add questions.
- **User  Quiz Attempts**: Users can attempt quizzes with real-time score tracking.
- **Scoring System**: Calculates and stores scores based on correct and incorrect answers.
- **Admin Summary Dashboard**: Displays registered users, active quizzes, chapters, etc.
- **Search Functionality**: Admin can search users, subjects, and quizzes for efficient management.

## Screenshots

Here are some screenshots of the Quiz Master application:

![Login Page](Screenshots/login.png)
*Login Page for Admin/User*

![Admin Dashboard](Screenshots/admin_dashboard.png)
*Admin Dashboard*

![Admin Quizzes](Screenshots/admin_quizzes.png)
*Admin Quizzes* 

![Admin Summary](Screenshots/admin_summary.png)
*Admin Summary*

![Registration Page](Screenshots/user_registration.png)
*Registration Page for User*

![User Dashboard](Screenshots/user_dashboard.png)
*User Dashboard*

![User Scores](Screenshots/user_scores.png)
*User Scores* 

![User Summary](Screenshots/user_summary.png)
*User Summary*


