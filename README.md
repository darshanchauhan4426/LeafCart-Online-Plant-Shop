LeafCart - A Full-Stack E-commerce Plant Shop
LeafCart is a complete, full-stack e-commerce web application built from the ground up using Python and Django. This project is a professional online store for selling plants, featuring a complete customer journey from browsing and searching for products to a secure checkout process and post-purchase order management.

Project Repository: https://github.com/darshanchauhan4426/Online-Plant-Shop

Features
LeafCart is a full-featured application that includes:

User & Account Management
Custom User Model: Secure user system using email for authentication.

Full Authentication: Complete user registration, login, and logout functionality.

Password Security: Strong password validation and a "Forgot Password" feature that sends a secure reset link via email.

Professional User Dashboard: A dedicated profile page where users can update their personal details (with password confirmation) and change their password.

E-commerce & Shopping
Dynamic Product Catalog: A multi-image gallery for each product, with details like price, stock status, and average customer rating.

Advanced Shop Page: A professional shop interface with:

Filtering: Filter products by category.

Searching: A search bar that queries product names and descriptions.

Sorting: Sort products by price, name, or availability.

Pagination: A clean pagination system that works with all active filters.

Stock Management: The system tracks inventory, displays "Out of Stock" messages, and automatically decrements stock after a purchase.

Shopping Cart: A fully functional shopping cart with the ability to update quantities and remove items.

Interactive Wishlist: An AJAX-powered wishlist that allows users to add or remove items without reloading the page.

Coupon System: A discount code system that allows the administrator to create coupons that apply a percentage-based discount to the cart total.

Post-Purchase Features
Order History: The user dashboard displays a complete history of all past orders with their status.

PDF Invoice Generation: Users can download a professional, dynamically generated PDF invoice for any order that has been marked as "Delivered".

Tech Stack
This project was built using the following technologies:

Backend: Python, Django

Frontend: HTML5, CSS3, JavaScript, Bootstrap (from the Alazea/LeafCart theme)

Database: SQLite3 (for development)

Key Python Libraries:

xhtml2pdf: For generating PDF invoices from HTML templates.

python-dotenv: For securely managing environment variables.

email_validator: For advanced email validation on the registration form.

Setup & Installation
To run this project locally, follow these steps:

1. Clone the Repository

git clone [https://github.com/darshanchauhan4426/Online-Plant-Shop.git](https://github.com/darshanchauhan4426/Online-Plant-Shop.git)
cd Online-Plant-Shop

2. Create and Activate a Virtual Environment

# Create the environment
python -m venv venv

# Activate it (on Windows)
venv\Scripts\activate

3. Install Dependencies
This project uses a requirements.txt file to manage its dependencies.

pip install -r requirements.txt

4. Create a .env File
In the root directory of the project, create a file named .env and add your secret keys and email credentials:

SECRET_KEY=your_django_secret_key_goes_here
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_16_digit_google_app_password

5. Set Up the Database
Run the migrations to create the database tables.

python manage.py migrate

6. Create an Admin Superuser
You will need an admin account to manage products, categories, and orders.

python manage.py createsuperuser

7. Run the Development Server

python manage.py runserver