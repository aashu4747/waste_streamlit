import streamlit as st
import pandas as pd
import base64
from pymongo import MongoClient
import plotly.express as px 
import plotly.graph_objects as go
import calendar

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['mydatabase']
form_data_collection = db['formdatas']
users_collection = db['users']

def login_page():
    st.title('Login')
    username = st.text_input('Username', key='login_username')  # Unique key for username input
    password = st.text_input('Password', type='password', key='login_password')  # Unique key for password input
    if st.button('Login'):
        # Authenticate user logic here (e.g., check credentials against database)
        user = users_collection.find_one({'username': username, 'password': password})
        if user:
            st.success('Login successful!')
            st.session_state.logged_in = True  # Store login state
            return True
        else:
            st.error('Invalid username or password.')
    return False

def signup_page():
    st.title('Signup')
    username = st.text_input('Username', key='signup_username')  # Unique key for username input
    password = st.text_input('Password', type='password', key='signup_password')  # Unique key for password input

    if st.button('Signup'):
        # Store user data in MongoDB or another database
        users_collection.insert_one({'username': username, 'password': password})
        st.success('Signup successful! Please login.')
        login_page()  # Redirect to login page after signup

# Define functions for different pages (e.g., signup, login, main app)
def main_app():
    st.title('Hazardous Waste Management Form')

    # Input for Date
    selected_date = st.date_input('Date')

    # Dropdown for Divisions
    division_options = ['GD ENGINE', 'TNGA ENGINE', 'Auto Parts', 'Utilities']
    selected_division = st.selectbox('Select Division', division_options)

    # Input for other fields
    inputs = {}
    input_labels = [
        ("Used oil from shopfloor", "1"),
        ("Used glove and cloth", "2"),
        ("Compressor filters", "3"),
        ("Band/oiled filter papers", "4"),
        ("Paint waste", "5"),
        ("Adhesive (FIPG)", "6"),
        ("DG Chimney", "7"),
        ("Softner resin", "8"),
        ("Carbuoys", "9"),
        ("Metal barrels", "10"),
        ("Chemical sludge", "11"),
        ("Skimmed oil", "12"),
        ("Grinding Muck:", "13"),
        ("Fuel Filters", "14"),
        ("Lapping Tape", "15"),
        ("Epoxy Waste", "16"),
        ("Test Bench Chimney", "17"),
        ("Plastic Barrels", "18"),
        ("Paint Containers", "19"),
        ("Oil Emulsion", "20"),
        ("DG Filers", "21"),
        ("Prowipe Paper", "22"),
        ("Canteen Chimney", "23"),
        ("Metal Buckets", "24"),
        ("Spray Containers", "25"),
        ("Saw Dust", "26"),
        ("Residue with Oil", "27"),
        ("Plastic Buckets", "28"),
    ]

    for label, id in input_labels:
        inputs[label] = st.number_input(label, key=id)

    # Submit Button
    if st.button('Submit'):
        # Handle form submission here
        form_data = {
            "Date": str(selected_date),  # Convert date to string
            "Division": selected_division,  # Store selected division
            **inputs  # Add other form inputs
        }
        
        # Insert form data into the existing collection
        form_data_collection.insert_one(form_data)  # Store form data in MongoDB
        st.success('Form submitted successfully!')

def view_data_page():
    st.title('View Data')

    # Retrieve data from MongoDB
    form_data_cursor = form_data_collection.find()
    form_data_list = list(form_data_cursor)
    data = pd.DataFrame(form_data_list)

    # Convert 'Date' column to datetime format
    data['Date'] = pd.to_datetime(data['Date'])

    # Display all data
    st.write('All Data:')
    st.write(data)

    # Download Button (visible only on view data page)
    if st.button('Download Data'):
        # Handle download functionality here
        csv = data.to_csv(index=False)
        b64 = base64.b64encode(csv.encode()).decode()
        href = f'<a href="data:file/csv;base64,{b64}" download="formData.csv">Download CSV</a>'
        st.markdown(href, unsafe_allow_html=True)

    # Dropdown menu to select specific category
    categories = [
        "Used oil (5.1) - Used oil from shopfloor, Skimmed oil",
        "Wastes containing oil (5.2) - Used Gloves & Cloth, Grinding muck, Oil emulsion, Saw dust, Compressor filters, Fuel filters, DG filters, Residue with oil, Band/oiled filter paper, Lapping tape, Prowipe paper",
        "Process waste (21.1) - Paint waste, Epoxy waste",
        "Wastes or residues (23.1) - Adhesive (FIPG)",
        "Exhaust Air or Gas cleaning residue (35.1) - DG Chimney, Test Bench Chimney, Canteen Chimney",
        "Spent resin (35.2) - Softener resin",
        "ETP wastes (35.3) - Chemical sludge",
        "Discarded containers (33.1) - Metal barrels, Plastic barrels, Metal buckets, Plastic buckets, Carbuoys, Paint containers, Spray containers, Others (specify)"
    ]
    selected_category = st.selectbox('Select Category', categories)

    # Generate graphs for the selected category and forecast
    if st.button('Generate Graph'):
        generate_graph_for_category(data, selected_category)

def generate_graph_for_category(data, category):
    # Define category mappings and get fields for the selected category
    category_map = {
        'Used oil (5.1) - Used oil from shopfloor, Skimmed oil': {
            'fields': ['Used oil from shopfloor', 'Skimmed oil'],
            'kspcb_target': 12.05,
            'internal_target': 10.85,
        },
        'Wastes containing oil (5.2) - Used Gloves & Cloth, Grinding muck, Oil emulsion, Saw dust, Compressor filters, Fuel filters, DG filters, Residue with oil, Band/oiled filter paper, Lapping tape, Prowipe paper': {
            'fields': ['Used glove and cloth', 'Grinding Muck', 'Oil Emulsion', 'Saw Dust', 'Compressor filters', 'Fuel Filters', 'DG Filers', 'Residue with Oil', 'Band/oiled filter papers', 'Lapping Tape', 'Prowipe Paper'],
            'kspcb_target': 28.33,
            'internal_target': 25.50,
        },
        'Process waste (21.1) - Paint waste, Epoxy waste': {
            'fields': ['Paint waste', 'Epoxy Waste'],
            'kspcb_target': 0.33,
            'internal_target': 0.30,
        },
        'Wastes or residues (23.1) - Adhesive (FIPG)': {
            'fields': ['Adhesive (FIPG)'],
            'kspcb_target': 0.25,
            'internal_target': 0.23,
        },
        'Exhaust Air or Gas cleaning residue (35.1) - DG Chimney, Test Bench Chimney, Canteen Chimney': {
            'fields': ['DG chimney', 'Test Bench Chimney', 'Canteen Chimney'],
            'kspcb_target': 0.17,
            'internal_target': 0.15,
        },
        'Spent resin (35.2) - Softener resin': {
            'fields': ['Softener resin'],
            'kspcb_target': 0.38,
            'internal_target': 0.34,
        },
        'ETP wastes (35.3) - Chemical sludge': {
            'fields': ['Chemical sludge'],
            'kspcb_target': 125.0,
            'internal_target': 112.5,
        },
        'Discarded containers (33.1) - Metal barrels, Plastic barrels, Metal buckets, Plastic buckets, Carbuoys, Paint containers, Spray containers': {
            'fields': ['Metal barrels', 'Plastic barrels', 'Metal buckets', 'Plastic buckets', 'Carbuoys', 'Paint Containers', 'Spray Containers'],
            'kspcb_target': 3.0,
            'internal_target': 2.7,
        }
    }

    category_info = category_map[category]
    selected_fields = category_info['fields']
    kspcb_target = category_info['kspcb_target']
    internal_target = category_info['internal_target']

    # Filter data for the selected fields
    category_data = data[['Date'] + selected_fields]

    # Convert 'Date' column to YearMonth format
    category_data['YearMonth'] = category_data['Date'].dt.strftime('%B %Y')

    # Combine data from all related sub-categories
    category_data['Combined'] = category_data[selected_fields].sum(axis=1)

    # Group by 'YearMonth' and calculate the sum of combined data for each month
    monthly_aggregates = category_data.groupby('YearMonth')['Combined'].sum().reset_index()

    # Sort data by YearMonth in ascending order
    monthly_aggregates['YearMonth'] = pd.to_datetime(monthly_aggregates['YearMonth'], format='%B %Y')
    monthly_aggregates = monthly_aggregates.sort_values('YearMonth')

    # Calculate cumulative values for each target
    kspcb_cumulative = [kspcb_target * (i + 1) for i in range(len(monthly_aggregates))]
    cumulative_internal = [internal_target * (i + 1) for i in range(len(monthly_aggregates))]

    # Prepare the table data
    table_data = pd.DataFrame({
        f'{month}': [
            kspcb_target,
            kspcb_target * (i + 1),
            internal_target,
            internal_target * (i + 1),
            monthly_aggregates.loc[monthly_aggregates['YearMonth'] == month, 'Combined'].values[0],
            monthly_aggregates.loc[monthly_aggregates['YearMonth'] <= month, 'Combined'].sum(),
        ] for i, month in enumerate(monthly_aggregates['YearMonth'].dt.strftime('%B %Y'))
    }, index=['Monthly KSPCB Target (MT)', 'Cumulative KSPCB Target (MT)', 'Monthly Target (MT)', 'Cumulative Target (MT)', 'Monthly Actual (MT)', 'Cumulative Actual (MT)'])

    # Display the data table
    st.write('Data Table:')
    st.write(table_data)

    # Plot bar chart
    fig = go.Figure()

    # Add Cumulative KSPCB target line graph
    fig.add_trace(go.Scatter(x=monthly_aggregates['YearMonth'], y=kspcb_cumulative,
                             mode='lines', name='Cumulative KSPCB target'))

    # Add Cumulative internal target line graph
    fig.add_trace(go.Scatter(x=monthly_aggregates['YearMonth'], y=cumulative_internal,
                             mode='lines', name='Cumulative internal target'))

    # Add new bars for monthly actual and cumulative actual data
    fig.add_trace(go.Bar(x=monthly_aggregates['YearMonth'] - pd.DateOffset(days=15), y=monthly_aggregates['Combined'],
                         name='Monthly Actual (MT)', offsetgroup=1, marker_color='blue'))
    fig.add_trace(go.Bar(x=monthly_aggregates['YearMonth'] - pd.DateOffset(days=15), y=monthly_aggregates['Combined'].cumsum(),
                         name='Cumulative Actual (MT)', offsetgroup=2, marker_color='orange'))

    # Set y-axis range dynamically based on data
    max_y = max(monthly_aggregates['Combined'].max(), monthly_aggregates['Combined'].cumsum().max(), max(kspcb_cumulative), max(cumulative_internal))
    fig.update_yaxes(range=[0, max_y + 5])  # Add some buffer to the max value for better visualization

    # Display month names on the x-axis
    fig.update_xaxes(title='YearMonth')

    # Add legend and update layout
    fig.update_layout(barmode='relative', legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01))

    # Display the graph
    st.plotly_chart(fig)

    # Forecasting for the next six months using Simple Moving Average (SMA)
    st.title('Next Six Months Forecast')

    # Calculate Simple Moving Average (SMA)
    window_size = 3  # Example window size for SMA
    monthly_aggregates['SMA'] = monthly_aggregates['Combined'].rolling(window=window_size).mean()

    # Extend datetime index for forecasting future values
    future_dates = pd.date_range(start=monthly_aggregates['YearMonth'].max() + pd.DateOffset(months=1), periods=6, freq='MS')

    # Use the last SMA value to project future trends
    last_sma_value = monthly_aggregates['SMA'].iloc[-1]
    future_sma_values = [last_sma_value] * len(future_dates)

    # Prepare forecasted data
    forecast_data = pd.DataFrame({
        'YearMonth': future_dates,
        'Forecasted_SMA': future_sma_values
    })

    # Display forecasted data table
    st.write('Forecasted Data Table:')
    st.write(forecast_data)

    # Plot forecasted values
    fig_forecast = go.Figure()

    # Plot SMA forecast
    fig_forecast.add_trace(go.Scatter(
        x=monthly_aggregates['YearMonth'],
        y=monthly_aggregates['SMA'],
        mode='lines',
        name='SMA Forecast',
        line=dict(color='green', width=2, dash='dash')
    ))

    # Plot forecasted SMA values
    fig_forecast.add_trace(go.Scatter(
        x=forecast_data['YearMonth'],
        y=forecast_data['Forecasted_SMA'],
        mode='lines',
        name='Forecasted SMA',
        line=dict(color='purple', width=2, dash='dash')
    ))

    # Update layout and display the forecast graph
    fig_forecast.update_layout(
        title='Next Six Months Forecast',
        xaxis_title='YearMonth',
        yaxis_title='Metric Value'
    )

    st.plotly_chart(fig_forecast)

if __name__ == '__main__':
    st.title('Navigation')
    if 'logged_in' not in st.session_state or not st.session_state.logged_in:
        st.write('Please login or sign up.')
        if login_page():
            st.write('Welcome! You are logged in.')
            page = st.radio('Select Page', ['Main App', 'View Data'])

            if page == 'Main App':
                main_app()
            elif page == 'View Data':
                view_data_page()
    else:
        st.write('Welcome! You are logged in.')
        page = st.radio('Select Page', ['Main App', 'View Data'])

        if page == 'Main App':
            main_app()
        elif page == 'View Data':
            view_data_page()
