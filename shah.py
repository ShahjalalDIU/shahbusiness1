import streamlit as st
import mysql.connector
from mysql.connector import Error
import pandas as pd
import numpy as np
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from datetime import date
import matplotlib.pyplot as plt
from datetime import datetime
from sqlalchemy import create_engine
import calendar  # Import to get month names

# Initialize session state variables if they don't exist
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'current_user' not in st.session_state:
    st.session_state['current_user'] = None
if 'user_role' not in st.session_state:
    st.session_state['user_role'] = None
if 'invoice' not in st.session_state:
    st.session_state['invoice'] = []

# MySQL Database connection
def create_connection():
    conn = None
    try:
        conn = mysql.connector.connect(
            host='192.250.235.46',
            user='shahbusi_shah',
            password='Shahjalal811',
            database='shahbusi_login',
            port = '3306'

        )
        if conn.is_connected():
            return conn
    except Error as e:
        st.error(f"Error connecting to MySQL database: {e}")
    return conn

def logout_user():
    st.session_state['logged_in'] = False
    st.session_state['current_user'] = None
    st.session_state['user_role'] = None
    st.success("You have been logged out.")
    st.stop()
def get_sales_data_by_date_range(conn, start_date, end_date):
    try:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT payment, new_due, rejection, total_invoice_price FROM invoices WHERE invoice_date BETWEEN %s AND %s"
        cursor.execute(query, (start_date, end_date))
        sales_data = cursor.fetchall()
        return sales_data
    except Exception as e:
        st.error(f"Error fetching sales data: {e}")
        return []


def get_due_data_by_date_range(conn, start_date, end_date):

    try:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT new_due FROM invoices WHERE invoice_date BETWEEN %s AND %s"
        cursor.execute(query, (start_date, end_date))
        due_data = cursor.fetchall()
        return due_data
    except Exception as e:
        st.error(f"Error fetching due data: {e}")
        return []


def get_rejection_data_by_date_range(conn, start_date, end_date):

    try:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT rejection FROM invoices WHERE invoice_date BETWEEN %s AND %s"
        cursor.execute(query, (start_date, end_date))
        rejection_data = cursor.fetchall()
        return rejection_data
    except Exception as e:
        st.error(f"Error fetching rejection data: {e}")
        return []


def get_total_invoice_price_by_date_range(conn, start_date, end_date):

    try:
        cursor = conn.cursor()
        query = "SELECT SUM(total_invoice_price) AS total_price FROM invoices WHERE invoice_date BETWEEN %s AND %s"
        cursor.execute(query, (start_date, end_date))
        result = cursor.fetchone()
        return result[0] if result and result[0] is not None else 0
    except Exception as e:
        st.error(f"Error fetching total invoice price: {e}")
        return 0

def update_product_details(conn, old_product_name, new_name, dp_price, mrp_price, group_name, available_stock):
    cursor = conn.cursor()
    try:
        # Update product details in the database
        update_query = """
            UPDATE products
            SET name = %s, dp_price = %s, mrp_price = %s, group_name = %s, available_stock = %s
            WHERE name = %s
        """
        cursor.execute(update_query, (new_name, dp_price, mrp_price, group_name, available_stock, old_product_name))
        conn.commit()
        st.success(f"Product '{new_name}' updated successfully!")
    except Error as e:
        st.error(f"Error occurred while updating product: {e}")
    finally:
        cursor.close()


def get_total_sales(conn):
    try:
        cursor = conn.cursor()
        query = "SELECT SUM(payment) FROM invoices"
        cursor.execute(query)
        total_sales = cursor.fetchone()[0]
        return total_sales if total_sales else 0
    except Exception as e:
        st.error(f"Error fetching total sales: {e}")
        return 0

# Function to plot the graph
def plot_monthly_totals(total_invoice_price, payment, due, rejection):
    categories = ['Total Bill', 'Payment', 'Due', 'Rejection']
    values = [total_invoice_price, payment, due, rejection]
    colors = ['skyblue', 'red', 'black', 'green']

    plt.figure(figsize=(10, 6))
    plt.bar(categories, values, color=colors)
    for i, val in enumerate(values):
        plt.text(i, val + 0.5, f"${val:,.2f}", ha='center', fontsize=12)
    plt.title('Monthly Invoice Data', fontsize=16)
    plt.ylabel('Amount ($)', fontsize=12)
    st.pyplot(plt)



def get_today_sales(conn):
    today = date.today()
    query = "SELECT SUM(payment) AS total_payment FROM invoices WHERE invoice_date = %s"
    with conn.cursor(dictionary=True) as cursor:
        cursor.execute(query, (today,))
        result = cursor.fetchone()
        return result['total_payment'] if result['total_payment'] else 0

# Function to get monthly sales
def get_sales_data_by_date_range(conn, start_date, end_date):
    """Fetch sales data (total payments) between two dates."""
    try:
        cursor = conn.cursor(dictionary=True)
        query = """
        SELECT invoice_date, payment FROM invoices WHERE invoice_date BETWEEN %s AND %s
        """
        cursor.execute(query, (start_date, end_date))
        sales_data = cursor.fetchall()
        return sales_data
    except Exception as e:
        st.error(f"Error fetching sales data: {e}")
        return []


def get_total_sales(conn):
    """Fetch overall sales from the database."""
    try:
        cursor = conn.cursor()
        query = "SELECT SUM(payment) FROM invoices"
        cursor.execute(query)
        total_sales = cursor.fetchone()[0]
        return total_sales if total_sales else 0
    except Exception as e:
        st.error(f"Error fetching total sales: {e}")
        return 0


def insert_invoice(conn, customer_info, total_invoice_price, rej, prev_due, amt, payment, due):
    try:
        cursor = conn.cursor()
        sql_insert_invoice = """
            INSERT INTO invoices (invoice_date, customer_name, customer_address, customer_mobile, previous_due, rejection, payment, new_due, final_amount, total_invoice_price)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """
        data = (
            customer_info['date'],
            customer_info['name'],
            customer_info['address'],
            customer_info['mobile'],
            prev_due,
            rej,
            payment,
            due,
            amt,
            total_invoice_price
        )
        cursor.execute(sql_insert_invoice, data)
        conn.commit()
        st.success("Invoice data stored successfully!")
    except Error as e:
        st.error(f"Error inserting invoice data: {e}")

# Retrieve product names from the database
def get_registered_products(conn):
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM products")
        products = cursor.fetchall()
        return [product[0] for product in products]
    except Error as e:
        st.error(f"Error fetching products: {e}")
        return []

# Retrieve current stock for a product
def get_current_stock(conn, product_name):
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT available_stock FROM products WHERE name = %s", (product_name,))
        result = cursor.fetchone()
        return result[0] if result else None
    except Error as e:
        st.error(f"Error fetching current stock: {e}")
        return None

# Update product stock in the database
def update_product_stock(conn, product_name, new_stock):
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE products SET available_stock = %s WHERE name = %s", (new_stock, product_name))
        conn.commit()

    except Error as e:
        st.error(f"Error updating product stock: {e}")

# Insert a product into the database
def insert_product(conn, name, dp_price, mrp_price, group_name, available_stock):
    try:
        if product_exists(conn, name):
            st.error("A product with this name already exists. Please use a different name.")
        else:
            sql_insert_product = """
                INSERT INTO products (name, dp_price, mrp_price, group_name, available_stock)
                VALUES (%s, %s, %s, %s, %s);
            """
            cursor = conn.cursor()
            cursor.execute(sql_insert_product, (name ,dp_price, mrp_price, group_name, available_stock))
            conn.commit()
            st.success("Product registered successfully!")
    except Error as e:
        st.error(f"Error inserting product: {e}")

# Check if product name already exists
def product_exists(conn, name):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE name = %s", (name,))
    return cursor.fetchone() is not None

# Function to fetch product details by name
def get_product_details_by_name(conn, product_name):
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM products WHERE name = %s", (product_name,))
        product = cursor.fetchone()
        return product
    except Error as e:
        st.error(f"Error fetching product details: {e}")
        return None

# Function to create PDF
def create_pdf(invoice_df, customer_info, total_invoice_price, rej, prev_due, amt, payment, due):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    def draw_page_header():
        c.drawString(250, height - 30, "M/S. ISHAQ ENTERPRISE")
        c.drawString(30, height - 50, f"Name: {customer_info['name']}")
        c.drawString(450, height - 50, f"Date: {customer_info['date']}")
        c.drawString(30, height - 70, f"Address: {customer_info['address']}")
        c.drawString(30, height - 90, f"Mobile: {customer_info['mobile']}")

        # Table headers
        c.drawString(30, height - 120, "S/N")
        c.drawString(80, height - 120, "Product Name")
        c.drawString(280, height - 120, "Quantity")
        c.drawString(380, height - 120, "Price")
        c.drawString(480, height - 120, "Total")

    draw_page_header()
    y_offset = height - 140
    serial_number = 1

    for i, row in invoice_df.iterrows():
        if y_offset < 100:
            c.showPage()
            draw_page_header()
            y_offset = height - 140

        c.drawString(30, y_offset, str(serial_number))
        c.drawString(80, y_offset, row['Product Name'])
        c.drawString(280, y_offset, str(row['Quantity']))
        c.drawString(380, y_offset, f"{row['DP Price']:.2f}")
        c.drawString(480, y_offset, f"{row['Total Price']:.2f}")

        y_offset -= 20
        serial_number += 1

    y_offset -= 40
    c.drawString(430, y_offset, f"Invoice Price : {total_invoice_price:.2f}")
    c.drawString(430, y_offset - 25, f"Rejection (-): {rej:.2f}")
    c.drawString(430, y_offset - 45, f"Previous Due (+): {prev_due:.2f}")
    c.drawString(430, y_offset - 65, f"Final Amount : {amt:.2f}")
    c.drawString(230, y_offset - 50, f"Payment: {payment:.2f}")
    c.drawString(230, y_offset - 80, f"New Due: {due:.2f}")

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

# Define the login page
def login_page():
    st.title("Login Page")
    user_type = st.radio("Select Login Type:", ["Admin Login", "Staff Login"])

    if user_type == "Admin Login":
        username = st.text_input("Admin Username:")
        password = st.text_input("Admin Password:", type="password")
        if st.button("Login"):
            if username == "admin" and password == "shah3303":
                st.session_state['logged_in'] = True
                st.session_state['current_user'] = "Admin"
                st.session_state['user_role'] = "admin"
                st.success(" Now you are go to a new world..!!")
                st.button("OK")
            else:
                st.error("Invalid admin credentials")

    elif user_type == "Staff Login":
        username = st.text_input("Staff Username:")
        password = st.text_input("Staff Password:", type="password")
        if st.button("Login"):
            if username == "staff" and password == "staff123":
                st.session_state['logged_in'] = True
                st.session_state['current_user'] = "Staff"
                st.session_state['user_role'] = "staff"
                st.success(" Now you are go to a new world..!!")
                st.button("OK")
            else:
                st.error("Invalid staff credentials")


def get_invoices_data_by_date(conn, search_date):
    try:
        cursor = conn.cursor(dictionary=True)
        query = """
        SELECT * FROM invoices WHERE invoice_date = %s
        """  # Assuming your invoices table has a 'date' column
        cursor.execute(query, (search_date,))
        invoices_data = cursor.fetchall()
        return invoices_data
    except Error as e:
        st.error(f"Error fetching invoices data: {e}")
        return []

# Function to fetch group names matching the search term
def search_group_by_name(conn, group_search):
    cursor = conn.cursor()
    query = "SELECT DISTINCT group_name FROM products WHERE group_name LIKE %s;"
    cursor.execute(query, (f"%{group_search}%",))
    result = cursor.fetchall()
    return [row[0] for row in result]  # Return the list of matching group names

# Function to fetch product details for the selected group
def get_products_by_group(conn, group_name):
    query = """
        SELECT name, dp_price, mrp_price, available_stock
        FROM products
        WHERE group_name = %s;
    """
    df = pd.read_sql(query, conn, params=[group_name])
    return df

# Admin workplace dashboard code
def admin_workplace(conn):

    # Change from radio to selectbox
    choice = st.sidebar.radio("Select an option:",
                                   ["Dashboard", "Register Product", "Update Stock", "Search Product", "Invoices Sheet", "Edit Product", "Log Out"])


    if choice == "Dashboard":
        st.subheader("Admin Dashboard")
        today = datetime.now().date()
        start_of_month = today.replace(day=1)

        # Get today's sales
        today_sales_data = get_sales_data_by_date_range(conn, today, today)
        today_sales = sum([sale['payment'] for sale in today_sales_data])

        # Get today's dues
        today_due_data = get_due_data_by_date_range(conn, today, today)
        today_due = sum([due['new_due'] for due in today_due_data])

        # Get monthly sales
        monthly_sales_data = get_sales_data_by_date_range(conn, start_of_month, today)
        monthly_sales = sum([sale['payment'] for sale in monthly_sales_data])

        # Get monthly dues
        monthly_due_data = get_due_data_by_date_range(conn, start_of_month, today)
        monthly_due = sum([due['new_due'] for due in monthly_due_data])

        # Get overall sales
        overall_sales = get_total_sales(conn)

        current_year = datetime.now().year
        year_range = list(range(current_year, current_year + 5))

        # Get total invoice prices
        today_total_invoice_price = get_total_invoice_price_by_date_range(conn, today, today)
        monthly_total_invoice_price = get_total_invoice_price_by_date_range(conn, start_of_month, today)

        # Display the 3 boxes at the top
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(label="Today's Sales", value=f"${today_sales:,.2f}")

        with col2:
            st.metric(label="Monthly Sales", value=f"${monthly_sales:,.2f}")

        with col3:
            selected_year = st.selectbox("Select Year", year_range, index=0)
        # Add two boxes for today's and monthly dues
        col4, col5 = st.columns(2)

        with col4:
            st.markdown("<div style='border: 10px solid black; padding: 10px; '>"
                        f"<h4>Today's Due</h4>"
                        f"<p>${today_due:,.2f}</p></div>", unsafe_allow_html=True)

        with col5:
            st.markdown("<div style='border: 10px solid black; padding: 10px;'>"
                        f"<h4>Monthly Due</h4>"
                        f"<p>${monthly_due:,.2f}</p></div>", unsafe_allow_html=True)

        # Add two boxes for today's and monthly rejections
        today_rejection_data = get_rejection_data_by_date_range(conn, today, today)
        today_rejection = sum([rej['rejection'] for rej in today_rejection_data])

        monthly_rejection_data = get_rejection_data_by_date_range(conn, start_of_month, today)
        monthly_rejection = sum([rej['rejection'] for rej in monthly_rejection_data])

        col6, col7 = st.columns(2)

        with col6:
            st.markdown("<div style='border: 10px solid black; padding: 10px;'>"
                        f"<h4>Today's Rejection</h4>"
                        f"<p>${today_rejection:,.2f}</p></div>", unsafe_allow_html=True)

        with col7:
            st.markdown("<div style='border: 10px solid black; padding: 10px;'>"
                        f"<h4>Monthly Rejection</h4>"
                        f"<p>${monthly_rejection:,.2f}</p></div>", unsafe_allow_html=True)

            # Get the current year and the next 5 years

        col8, col9, col10 = st.columns(3)

        with col9:
            st.metric(label="overall_sales", value=f"${overall_sales:,.2f}")


        current_year = datetime.now().year
        year_range = list(range(current_year, current_year + 5))

        def get_monthly_sales_by_year(conn, year):
            monthly_sales = {}
            for month in range(1, 13):  # Loop over months 1-12 (January to December)
                start_date = datetime(year, month, 1)
                if month == 12:
                    end_date = datetime(year + 1, 1, 1)
                else:
                    end_date = datetime(year, month + 1, 1)

                # Get monthly sales data
                monthly_sales_data = get_sales_data_by_date_range(conn, start_date, end_date)
                monthly_sales[month] = sum([sale['payment'] for sale in monthly_sales_data])

            return monthly_sales

        # Get monthly sales for the selected year
        monthly_sales = get_monthly_sales_by_year(conn, selected_year)

        # Prepare data for the bar chart
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        sales_values = [monthly_sales.get(month, 0) for month in range(1, 13)]  # Get sales for each month

        # Set up the bar chart
        st.subheader(f"Monthly Sales - {selected_year}")

        # Centering the graph with empty columns and increasing its size
        empty_col1, main_col, empty_col2 = st.columns(
            [1, 6, 1])  # Adjust the ratio for centering, make the main_col wider

        with main_col:
            fig, ax = plt.subplots(figsize=(18, 13))  # Increased size for larger graph
            bars = ax.bar(months, sales_values, color="teal")

            # Add title and labels
            ax.set_title(f"Monthly Sales for {selected_year}", fontsize=20)
            ax.set_ylabel("Amount in Taka", fontsize=16)
            ax.set_xlabel("Month", fontsize=16)
            ax.set_facecolor("silver")  # Background color for the graph

            # Ensure proper display of month names
            plt.xticks(rotation=45, ha="right", fontsize=18)  # Rotate the month labels and increase font size

            # Adding values on top of each bar
            for bar in bars:
                yval = bar.get_height()
                ax.text(bar.get_x() + bar.get_width() / 2, yval, f'{yval:,.2f}tk', rotation=60 ,ha='right', va='bottom',
                        fontsize=16)

            # Show the plot
            st.pyplot(fig)



    elif choice == "Register Product":
        st.subheader("Register Product")
        product_name = st.text_input("Product Name")

        dp_price = st.text_input("Distributor Price")
        mrp_price = st.text_input("MRP Price")
        group_name = st.text_input("Group Name")
        available_stock = st.number_input("Available Stock", min_value=0.0, step=0.01)  # Allow floats

        if st.button("Register"):
            if product_name and dp_price and mrp_price and group_name and available_stock:
                insert_product(conn, product_name, dp_price, mrp_price, group_name, available_stock)
            else:
                st.error("Please fill in all the required fields")


    elif choice == "Update Stock":
        st.subheader("Insert Product")
        products = get_registered_products(conn)

        if products:
            selected_product = st.selectbox("Select Product", products)

            if selected_product:
                new_quantity = st.number_input("Enter Quantity to Add", min_value=0.0, step=0.1)  # Allow floats

                if st.button("Update Stock"):
                    current_stock = get_current_stock(conn, selected_product)

                    if current_stock is not None:
                        updated_stock = current_stock + new_quantity
                        update_product_stock(conn, selected_product, updated_stock)
                    else:
                        st.error("Error: Could not retrieve current stock.")
        else:
            st.warning("No registered products found!")

    elif choice == "Search Product":
        st.subheader("Search Product")
        products = get_registered_products(conn)

        if products:
            selected_product = st.selectbox("Select Product", products)

            if selected_product:
                product_details = get_product_details_by_name(conn, selected_product)

                if product_details:

                    st.write(f"**Product Name:** {product_details['name']}")
                    st.write(f"**Distributor Price (DP Price):** {product_details['dp_price']}")
                    st.write(f"**MRP Price:** {product_details['mrp_price']}")
                    st.write(f"**Group Name:** {product_details['group_name']}")
                    st.write(f"**Available Stock:** {product_details['available_stock']}")
                else:
                    st.error(f"Product {selected_product} not found.")
        else:
            st.warning("No registered products found!")



    elif choice == "Invoices Sheet":
        st.subheader("Invoices Sheet")
        # Add a date input for selecting the date
        selected_date = st.date_input("Select Date:")
        if st.button("Search"):
            invoices_data = get_invoices_data_by_date(conn, selected_date)
            if invoices_data:
                # Convert invoices data to DataFrame

                df = pd.DataFrame(invoices_data)

                st.write(df)  # Display the invoices data as a table

                # Calculate total payment and total due

                total_payment = df[
                    'payment'].sum() if 'payment' in df.columns else 0  # Adjust 'payment' to your actual column name

                total_due = df[
                    'new_due'].sum() if 'new_due' in df.columns else 0  # Adjust 'due' to your actual column name

                # Display total payment and total due

                st.write(f"**Total Payment:** {total_payment}")

                st.write(f"**Total Due:** {total_due}")

            else:

                st.warning(f"No data found for {selected_date}.")

    elif choice == "Edit Product":
        st.subheader("Edit Product")

        # Fetch all registered products
        products = get_registered_products(conn)

        if products:
            # Select a product to edit
            selected_product = st.selectbox("Select Product to Edit", products)

            if selected_product:
                # Fetch current details of the selected product
                product_details = get_product_details_by_name(conn, selected_product)

                # Show product details in input fields
                if product_details:
                    # Editable fields for product details
                    product_name = st.text_input("Product Name", product_details['name'])
                    dp_price = st.text_input("Distributor Price", product_details['dp_price'])
                    mrp_price = st.text_input("MRP Price", product_details['mrp_price'])
                    group_name = st.text_input("Group Name", product_details['group_name'])
                    available_stock = st.number_input("Available Stock", min_value=0.0, step=0.01,
                                                      value=product_details['available_stock'])

                    if st.button("Save Changes"):
                        # Call function to update the product in the database
                        update_product_details(conn, selected_product, product_name, dp_price, mrp_price, group_name,
                                               available_stock)
                else:
                    st.error("Could not retrieve product details.")
        else:
            st.warning("No registered products found!")


    elif choice == "Log Out":
        st.sidebar.warning("Are you sure you want to log out?")

        # Display Yes and No buttons
        col1, col2, col3 = st.sidebar.columns(3)
        with col1:
            yes = st.button("Yes")

        with col3:
            no = st.button("No")

        col4, col5, col6 = st.sidebar.columns(3)
        with col5:
            st.button("OK")

        if yes:
            # Log out the user and redirect to the login page
            st.success(" Thank you.")
            logout_user()  # Call the log-out function
        elif no:
            # Stay on the current page
            st.sidebar.info("Staying No Problem.")

# Staff workplace page
def staff_workplace(conn):
    st.sidebar.title("Staff Menu")
    choice = st.sidebar.radio("Select an option:", ["Create Invoice", "Search Single Product", "Search Group Product", "Log Out"])

    if choice == "Create Invoice":
        st.subheader('ISHAQ ENTERPRISE')

        # 1st row: Customer Name (Left + Middle) and Date (Right)
        col1, col2 = st.columns([2, 1])
        with col1:
            customer_name = st.text_input('Customer Name:', key='customer_name')
        with col2:
            invoice_date = st.date_input('Date:', date.today(), key='invoice_date')

        # 2nd row: Phone (Left) and Address (Middle + Right)
        col3, col4 = st.columns([1, 3])
        with col3:
            customer_mobile = st.text_input('Mobile:', key='customer_mobile')
        with col4:
            customer_address = st.text_input('Address:', key='customer_address')

        # Store customer info in a dictionary
        customer_info = {
            'date': invoice_date,
            'name': customer_name,
            'address': customer_address,
            'mobile': customer_mobile
        }

        col5, col6 = st.columns([2, 1])
        with col5:
            product_names = get_registered_products(conn)
            product_names = np.append(product_names, 'Manual Entry')
            selected_product_name = st.selectbox('Select Product', product_names, key='selected_product_name')
        with col6:
            value_type = st.selectbox('Value Type', ['Piece', 'Weight'], key='value_type')

        cols4 = st.columns([1, 2, 1])
        if selected_product_name and selected_product_name != 'Manual Entry':
            selected_product = get_product_details_by_name(conn, selected_product_name)
            dp_price = cols4[0].number_input('Price:', value=float(selected_product['dp_price']), min_value=0.0)

            if value_type == 'Weight':
                weight = cols4[1].number_input('Weight (kg):', min_value=0.0, value=0.0, step=0.001)
                if cols4[2].button('Add to Invoice'):
                    current_stock = get_current_stock(conn, selected_product['name'])
                    if current_stock is not None:
                        if weight <= current_stock:
                            total_price = dp_price * weight
                            st.session_state.invoice.append({
                                'Product Name': selected_product['name'],
                                'Quantity': f"{weight} kg",
                                'DP Price': dp_price,
                                'Total Price': total_price,
                                'Pieces': weight  # Store weight for stock update
                            })
                        else:
                            st.error(
                                f"Not enough stock for {selected_product['name']}. Available: {current_stock} kg, Required: {weight} kg")
            elif value_type == 'Piece':
                pieces = cols4[1].number_input('Number of Pieces:', min_value=0, value=0)
                if cols4[2].button('Add to Invoice'):
                    current_stock = get_current_stock(conn, selected_product['name'])
                    if current_stock is not None:
                        if pieces <= current_stock:
                            total_price = dp_price * pieces
                            st.session_state.invoice.append({
                                'Product Name': selected_product['name'],
                                'Quantity': f"{pieces} P",
                                'DP Price': dp_price,
                                'Total Price': total_price,
                                'Pieces': pieces  # Store pieces for stock update
                            })
                        else:
                            st.error(
                                f"Not enough stock for {selected_product['name']}. Available: {current_stock} pieces, Required: {pieces} pieces")
        elif selected_product_name == 'Manual Entry':
            product_name = cols4[0].text_input('Product Name:')
            dp_price = cols4[1].number_input('Price:', min_value=0.0)

            if value_type == 'Weight':
                weight = cols4[1].number_input('Weight (kg):', min_value=0.0, value=0.0, step=0.001)
                if cols4[2].button('Add Manual Entry to Invoice'):
                    total_price = dp_price * weight
                    st.session_state.invoice.append({
                        'Product Name': product_name,
                        'Quantity': f"{weight} kg",
                        'DP Price': dp_price,
                        'Total Price': total_price,
                        'Pieces': weight  # Store weight for stock update
                    })
            elif value_type == 'Piece':
                pieces = cols4[1].number_input('Number of Pieces:', min_value=0, value=1)
                if cols4[2].button('Add Manual Entry to Invoice'):
                    total_price = dp_price * pieces
                    st.session_state.invoice.append({
                        'Product Name': product_name,
                        'Quantity': f"{pieces} P",
                        'DP Price': dp_price,
                        'Total Price': total_price,
                        'Pieces': pieces  # Store pieces for stock update
                    })

        # Display the current invoice
        st.subheader('Invoice')
        invoice_df = pd.DataFrame(st.session_state.invoice)

        if not invoice_df.empty:
            for i, row in invoice_df.iterrows():
                cols = st.columns([4, 1])  # Two columns: one for displaying product info, one for the remove button

                with cols[0]:  # Product info display
                    st.write(f"**{row['Product Name']}**")
                    st.write(
                        f"Quantity: {row['Quantity']}, DP Price: {row['DP Price']}, Total Price: {row['Total Price']}")

                with cols[1]:  # Remove button
                    if st.button(f'Remove', key=f'remove_{i}'):
                        st.session_state.invoice.pop(i)
                        st.button("OK")
                      # Refresh the page after removing


            total_invoice_price = invoice_df['Total Price'].sum()

            # Summary inputs
            cols5 = st.columns(3)
            rej = cols5[0].number_input('Return Product:', min_value=0.0, value=0.0)
            prev_due = cols5[1].number_input('Previous Due:', min_value=0.0, value=0.0)
            payment = cols5[2].number_input('Payment:', min_value=0.0, value=0.0)

            due = prev_due + total_invoice_price - payment - rej
            amt = total_invoice_price - rej + prev_due

            summary_data = {
                'Total Price': total_invoice_price,
                'Return Product': rej,
                'Previous Due': prev_due,
                'Final Amount': amt,
                'Payment': payment,
                'New Due': due
            }
            summary_df = pd.DataFrame([summary_data])
            st.write(summary_df)

            if st.button('Done'):

                insert_invoice(conn, customer_info, total_invoice_price, rej, prev_due, amt, payment, due)
                # Update stock in the database
                try:
                    for item in invoice_df.to_dict(orient='records'):
                        product_name = item['Product Name']
                        quantity_sold = item['Pieces']
                        current_stock = get_current_stock(conn, product_name)

                        if current_stock is not None:
                            new_stock = current_stock - quantity_sold
                            if new_stock < 0:
                                st.error(
                                    f"Not enough stock for {product_name}. Available: {current_stock}, Required: {quantity_sold}")
                                return
                            update_product_stock(conn, product_name, new_stock)

                    updated_invoice_df = invoice_df.copy()

                    # Generate and download PDF after successful stock update
                    buffer = create_pdf(updated_invoice_df, customer_info, total_invoice_price, rej, prev_due, amt, payment, due)
                    file_name = f"{customer_info['name'].replace(' ', '_')}_invoice.pdf"
                    st.download_button(
                        label="Download Invoice as PDF",
                        data=buffer,
                        file_name=file_name,
                        mime="application/pdf"
                    )
                    st.session_state.invoice.clear()  # Clear the invoice after download
                except Exception as e:
                    st.error(f"Error updating stock: {e}")
        else:
            st.warning('Invoice is empty. Add products before finalizing.')



    elif choice == "Search Single Product":
        st.subheader("Search Product")
        products = get_registered_products(conn)

        if products:
            selected_product = st.selectbox("Select Product", products)

            if selected_product:
                product_details = get_product_details_by_name(conn, selected_product)

                if product_details:

                    st.write(f"**Product Name:** {product_details['name']}")
                    st.write(f"**Distributor Price (DP:):** {product_details['dp_price']}")
                    st.write(f"**MRP Price:** {product_details['mrp_price']}")
                    st.write(f"**Group Name:** {product_details['group_name']}")
                    st.write(f"**Available Stock:** {product_details['available_stock']}")
                else:
                    st.error(f"Product {selected_product} not found.")
        else:
            st.warning("No registered products found!")

    elif choice == "Search Group Product":
        st.title('Search Group')

        # Input to search group name
        group_search = st.text_input('Enter Group Name to Search:', '')

        if group_search:
            # Fetch available groups matching the search term
            matching_groups = search_group_by_name(conn, group_search)  # Function to get group names by search term

            if matching_groups:
                # Selectbox to show matching groups
                selected_group = st.selectbox('Matching Groups:', matching_groups)

                if selected_group:
                    # Fetch product details for the selected group
                    group_products = get_products_by_group(conn, selected_group)

                    if not group_products.empty:
                        # Display the group product details in a table
                        st.subheader(f"Products in group: {selected_group}")
                        st.dataframe(group_products)
                    else:
                        st.warning(f"No products found for the group: {selected_group}")
            else:
                st.error("No matching group found. Please check the group name.")
        else:
            st.info("Please enter a group name to search.")

    elif choice == "Log Out":
        st.sidebar.warning("Are you sure you want to log out?")

        # Display Yes and No buttons
        col1, col2, col3 = st.sidebar.columns(3)
        with col1:
            yes = st.button("Yes")

        with col3:
            no = st.button("No")

        col4, col5, col6 = st.sidebar.columns(3)
        with col5:
            st.button("OK")

        if yes:
            # Log out the user and redirect to the login page
            st.success(" Thank you.")
            logout_user()  # Call the log-out function
        elif no:
            # Stay on the current page
            st.sidebar.info("Staying No Problem.")

# Main function to control the flow
def main():
    conn = create_connection()
    if conn:
        if st.session_state['logged_in']:
            if st.session_state['user_role'] == "admin":
                admin_workplace(conn)
            elif st.session_state['user_role'] == "staff":
                staff_workplace(conn)
        else:
            login_page()
    else:
        st.error("Failed to connect to the database")

if __name__ == "__main__":
    main()
