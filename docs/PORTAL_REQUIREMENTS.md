# School Management System — Premium Homepage + Portals — Master Requirements

## Project Goal

Build a modern, professional School Management System with a premium homepage and dedicated portals for:

- Students
- Parents
- Teachers
- Principal
- Administration

The system should feel like a real university/school digital portal similar in concept to **MyIUB**, where students and parents can log in and manage academic, fee, attendance, examination, and school-related activities from one place.

The homepage should be the central entry point of the system and should clearly guide each user to the correct portal.

---

## 1. Main Homepage

Create a modern, premium, responsive school ERP homepage.

The homepage should feel like a real educational institution's official digital platform, not a basic CRUD application.

### Header

Include:

- School logo
- School name
- Home
- About
- Academics
- Admissions
- Departments / Classes
- Notices
- Events
- Contact
- Login button
- Student Portal button
- Parent Portal button

Add a clean responsive mobile navigation menu.

---

## 2. Hero Section

Create a strong hero section explaining the digital school platform.

Example concept:

### "Your School, Your Portal, Your Digital Campus"

Supporting text:

"Access academics, attendance, examinations, fees, activities, notices, and important school information from one secure portal."

Add:

- Student Portal button
- Parent Portal button
- Admission button
- Learn More button

Use a professional education-related visual/design.

The hero should immediately communicate that this is a complete digital school management platform.

---

## 3. Portal Access Section

Create a prominent section called:

## "Access Your School Portal"

Show separate cards for:

### Student Portal

Students can:

- View personal profile
- View registration number
- View class and section
- View academic year
- Check attendance
- View timetable
- View homework
- View syllabus
- View lecture/class information
- View examination schedule
- View results
- View date sheets
- View fee challans
- Pay school fees online
- View payment history
- Download receipts
- View school notices
- View events
- View curricular activities
- View non-curricular activities
- Receive notifications
- View academic progress

Button: **Login to Student Portal**

### Parent Portal

Parents should have their own secure portal.

Parents can:

- View linked children
- Switch between children if they have multiple students
- View child's profile
- View class and section
- View attendance
- View timetable
- View homework
- View syllabus
- View examination schedule
- View results
- View academic performance
- View fee status
- View monthly fee
- View admission fee
- View outstanding dues
- View challans
- Pay fees online
- View complete payment history
- Download payment receipts
- View notices
- View events
- View activities
- Receive school notifications
- View important academic updates

Button: **Login to Parent Portal**

---

## 4. Student Online Fee Payment

This is a very important part of the system.

Students should be able to pay their school fees directly from their portal.

Create a professional "My Fees" section inside the Student Portal.

Display:

- Student name
- Registration number
- Class
- Academic year
- Fee month
- Fee type
- Challan number
- Due date
- Amount
- Late fee
- Total payable
- Payment status

Possible statuses: Paid, Unpaid, Pending, Overdue, Partially Paid

When a student clicks **Pay Now**, they should be taken through a secure online payment flow.

After successful payment:

- Update payment status automatically
- Generate payment receipt
- Generate transaction/reference number
- Store payment record
- Show payment date and time
- Send notification
- Allow receipt download/printing

Students should be able to see their complete payment history.

---

## 5. Parent Fee Payment

Parents should have the same fee functionality.

For parents with multiple children:

### Select Student

Example: Muhammad — Class 8, Ahmed — Class 5, Fatima — Class 3

After selecting a child, show that child's:

- Monthly fees
- Admission fees
- Outstanding fees
- Challans
- Payment history
- Receipts

Parents should be able to pay fees for each child directly from the portal.

---

## 6. MyIUB-Style Student Dashboard

The Student Portal dashboard should feel like a real university/student information system.

After login, display:

### Welcome Area

"Welcome back, Muhammad"

Show: Student photo, Student name, Registration number, Class, Section, Academic year

### Dashboard Cards

Display cards for:

- Attendance
- Current Fees
- Pending Fees
- Upcoming Exams
- Latest Result
- Homework
- Notifications

### Quick Actions

Provide:

- Pay Fee
- View Attendance
- View Result
- View Timetable
- View Homework
- View Challan
- Download Receipt
- View Notices

---

## 7. Student Academic Dashboard

Create an academic overview showing:

### Attendance

Display: Overall attendance percentage, Present, Absent, Leave, Monthly attendance

Use simple charts where useful.

### Academic Performance

Display: Current GPA/percentage where applicable, Subject-wise marks, Previous examination results, Academic progress

### Upcoming

Show: Upcoming exams, Assignments, Homework, Events, Important notices

---

## 8. Parent Dashboard

The parent dashboard should be different from the student dashboard.

Show:

### Parent Overview

- Parent name
- Number of children
- School notifications
- Pending fees
- Upcoming exams
- Recent results

### Child Cards

For every child show: Name, Photo, Class, Section, Attendance, Fee status, Latest result

Clicking a child opens the complete student information.

---

## 9. Admissions

Homepage should have a clear "Admissions Open" section.

Display: Admission information, Available classes, Eligibility, Required documents, Admission procedure, Fee information, Important dates

Add: **Apply for Admission**

Admission workflow: Application → Review → Approval/Reject → Student Registration

---

## 10. School Fee System

The complete ERP should support:

### Fee Types

- Admission Fee
- Monthly Fee
- Examination Fee
- Transport Fee
- Fine/Late Fee
- Other School Charges

Administrators should be able to configure fee structures.

Students and parents should only see fees related to their account.

---

## 11. Challan System

Every payable fee should support a challan.

Challan should contain: School name/logo, Student name, Registration number, Class, Section, Academic year, Challan number, Fee month, Fee type, Amount, Due date, Late fee, Total amount, Payment status

Provide: Print Challan, Download Challan, Pay Online

After successful payment, mark the challan as **PAID** and generate an official receipt.

---

## 12. Teacher Portal

Teachers can manage:

- Assigned classes
- Students
- Attendance
- Homework
- Diary
- Syllabus
- Lecture plans
- Tests
- Exams
- Marks
- Results
- Notices
- Activities

Teachers should also have access to their payroll information.

---

## 13. Teacher Payroll

Administration should manage teacher salaries.

Store: Teacher, Employee ID, Salary, Month, Deductions, Bonuses, Net salary, Bank account information, Payment status, Payment date, Transaction/reference number

Teachers should be able to view their salary/payment history.

---

## 14. Principal Portal

The Principal should have a complete management dashboard.

Principal should be able to monitor:

- Total students
- Total teachers
- Admissions
- Attendance
- Fees
- Outstanding fees
- Examination performance
- Results
- Classes
- Activities
- Teacher performance
- Payroll overview
- School announcements
- Reports

Principal approval workflows should include: Admissions, Important announcements, Academic decisions, Student promotion, Other configured approvals

---

## 15. School Activities

Students and parents should be able to see school activities.

Separate activities into:

### Curricular Activities

Academic competitions, Subject competitions, Presentations, Projects, Educational activities

### Non-Curricular Activities

Sports, Cultural events, Debates, Trips, Celebrations, Clubs, School functions

Activities should be associated with the academic year.

---

## 16. Academic Year System

The ERP must properly support academic years.

Example: **Academic Year 2026–2027**

Every student record, fee, attendance, examination, result, timetable, and activity should be connected to the appropriate academic year.

Students/parents should be able to view relevant historical records where permitted.

---

## 17. Notifications

Create a centralized notification system.

Students and parents can receive notifications for: Fee due dates, Successful payments, New challans, Results, Attendance, Homework, Exams, School notices, Events, Important announcements

Show unread notification count in the portal header.

---

## 18. Homepage Statistics

Add a professional statistics section.

Possible cards: Students, Teachers, Classes, Departments, Academic Programs, Years of Excellence

Do not expose private student information on the public homepage.

---

## 19. School Notices

Create a homepage section for important notices.

Example: Examination announcement, Admission announcement, Holiday notice, Fee deadline, School event, Important academic announcement

Include: **View All Notices**

---

## 20. Upcoming Events

Show upcoming: Exams, Parent-teacher meetings, Sports events, School functions, Holidays, Competitions, Academic activities

---

## 21. Security

All portals must use proper authentication and authorization.

- Student: Can only access their own records.
- Parent: Can only access their linked children.
- Teacher: Can only access assigned classes/students and permitted academic data.
- Principal: Can access school-wide management information.
- Administration: Can manage authorized ERP functions.

Never expose sensitive information through public pages or APIs.

---

## 22. UI/UX Requirements

The design should be: Modern, Premium, Clean, Professional, Responsive, Mobile-friendly, Easy for students and parents, Suitable for a real school

Use: Clear typography, Professional cards, Clean tables, Charts, Status badges, Icons, Proper spacing, Consistent buttons, Responsive sidebar, Responsive navbar, Dashboard layouts

Support: Desktop, Tablet, Mobile

Also support: Light mode, Dark mode

---

## 23. Portal Navigation

### Student Sidebar

Dashboard, My Profile, Attendance, Timetable, Homework, Diary, Syllabus, Exams, Date Sheet, Results, Fees, Challans, Payments, Receipts, Activities, Notices, Notifications, Academic Year, Logout

### Parent Sidebar

Dashboard, My Children, Child Profile, Attendance, Timetable, Homework, Exams, Results, Fees, Challans, Payments, Receipts, Activities, Notices, Notifications, Academic Year, Logout

---

## 24. Global Search

Add a global search feature for authenticated users.

Students/parents should be able to quickly find: Notices, Results, Homework, Challans, Payments, Activities, Exams

Use a simple keyboard shortcut such as: **Ctrl + K**

---

## 25. Homepage Footer

Include: School logo, School name, About school, Quick links, Admissions, Student Portal, Parent Portal, Contact, Address, Phone, Email, Social media links, Privacy Policy, Terms & Conditions

---

## 26. Important Architecture Rule

Do not build the homepage as an isolated frontend.

The homepage and portals must connect to the actual ERP backend.

- Student Portal → Student database records
- Parent Portal → Parent/Student relationship
- Fees → Fee/Challan/Payment records
- Results → Examination/Result records
- Attendance → Attendance records
- Activities → Academic-year activity records
- Notifications → Notification system

Everything shown in the portal should come from real backend data.

Do not use fake static dashboard data in the final implementation.

---

## 27. Final User Experience

The final flow should look like this:

### Public User

School Website → Homepage → Student Portal / Parent Portal / Admissions

### Student

Login → Student Dashboard → Check Fees → View Challan → Pay Online → Payment Confirmation → Receipt Generated → Payment History Updated

### Parent

Login → Parent Dashboard → Select Child → View Academic + Attendance + Fees → Pay Fee → Receipt Generated → Payment History Updated

The complete experience should feel like a real **MyIUB-style student information portal**, but designed specifically for a modern school ERP.

---

## Development Instruction

Before implementing the homepage, inspect the existing School ERP project structure and reuse the existing:

- Authentication
- User roles
- Student models
- Parent models
- Teacher models
- Principal functionality
- Admission system
- Fee system
- Challan system
- Payment system
- Attendance
- Exams
- Results
- Activities
- Notifications
- Academic-year system

Do not create duplicate models or duplicate functionality if these already exist.

Modify only the files required for the homepage and portal experience.

Keep the existing backend functionality working.

The homepage should become the polished public entry point, while Student Portal and Parent Portal should become the main authenticated experiences for students and parents.
