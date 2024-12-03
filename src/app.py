import json
from flask import Flask, render_template, request, redirect, url_for, flash,jsonify 
import pandas as pd
import mysql.connector as con
import matplotlib.pyplot as plt
import os
import plotly
import plotly.express as px

app = Flask(__name__)
app.secret_key = '1234'  # Required for flash messages

# Database connection parameters
host = 'localhost'
user = 'root'
password = 'mouse@2010'
database = 'sales'

# Function to load data from MySQL database
def load_data_from_mysql():
    connection = con.connect(host=host, user=user, password=password, database=database)
    query = "SELECT * FROM sales_data"
    data = pd.read_sql(query, connection)
    connection.close()
    return data

# Function to save new sales data to the database
def save_sales_data(order_id, city, order_date, ship_date, customer_id, region, sales):
    connection = con.connect(host=host, user=user, password=password, database=database)
    cursor = connection.cursor()
    query = "INSERT INTO sales_data (Order_ID, City, Order_Date, Ship_Date, Customer_ID, Region, Sales) VALUES (%s, %s, %s, %s, %s, %s, %s)"
    cursor.execute(query, (order_id, city, order_date, ship_date, customer_id, region, sales))
    connection.commit()
    cursor.close()
    connection.close()


def perform_sales_analysis():
    data = load_data_from_mysql()
    
    # Total Sales by Region
    total_sales_by_region = data.groupby('City').agg(Total_Sales=('Sales', 'sum')).reset_index()
    total_sales_fig = px.bar(total_sales_by_region, x='City', y='Total_Sales', title='Total Sales by Region',
                              labels={'Total_Sales': 'Total Sales ($)', 'City': 'Region'})
    
    # Average Sales per Transaction
    average_sales_per_transaction = data.groupby('City').agg(Average_Sales=('Sales', 'mean')).reset_index()
    average_sales_fig = px.bar(average_sales_per_transaction, x='City', y='Average_Sales', title='Average Sales per Transaction',
                                labels={'Average_Sales': 'Average Sales ($)', 'City': 'Region'})
    
    
    # Convert figures to JSON
    total_sales_json = json.dumps(total_sales_fig, cls=plotly.utils.PlotlyJSONEncoder)
    average_sales_json = json.dumps(average_sales_fig, cls=plotly.utils.PlotlyJSONEncoder)
    
    return total_sales_json, average_sales_json 

@app.route('/')
def index():
    data = load_data_from_mysql()
    columns = ['Order ID', 'City', 'Order Date', 'Ship Date', 'Customer ID', 'Region', 'Sales']
    
    # Perform sales analysis and get the graph JSONs
    total_sales_json, average_sales_json= perform_sales_analysis()
    
    return render_template('index.html', 
                           data=data.values.tolist(), 
                           columns=columns, 
                           total_sales_json=total_sales_json,
                           average_sales_json=average_sales_json)

@app.route('/view_data')
def view_data():
    data = load_data_from_mysql()
    columns = ['Order ID', 'City', 'Order Date', 'Ship Date', 'Customer ID', 'Region', 'Sales']  # Include 'Sales' column
    return render_template('view_data.html', data=data.values.tolist(), columns=columns)

@app.route('/add_data', methods=['GET', 'POST'])
def add_data():
    if request.method == 'POST':
        try:
            order_id = request.form['order_id'] 
            city = request.form['city']
            order_date = request.form['order_date']
            ship_date = request.form['ship_date']
            customer_id = request.form['customer_id']
            region = request.form['region']
            sales = float(request.form['sales'])  # Convert sales to float

            # Here you would typically save the data to a database
            # save_sales_data(order_id, city, order_date, ship_date, customer_id, region, sales)

            flash('Data added successfully!', 'success')  # Flash success message
            return redirect(url_for('add_data'))  # Redirect to the same page to show the message
        except Exception as e:
            flash('Error occurred: ' + str(e), 'danger')  # Flash error message
            return redirect(url_for('add_data'))  # Redirect back to the add data page

    return render_template('add_data.html')

@app.route('/analyze_data')
def analyze_data():
    plot_url = perform_sales_analysis()
    return render_template('analyze_data.html', plot_url=plot_url)

if __name__ == '__main__':
    app.run(debug=True)