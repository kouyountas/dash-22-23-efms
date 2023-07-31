import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import plotly.graph_objects as go

# Load data
@st.cache_data
def load_data():
    df = pd.read_csv('Data.csv')
    return df

df = load_data()


# Define function to calculate IQR range
def iqr_range(df, column_name):
    Q1 = df[column_name].quantile(0.25)
    Q3 = df[column_name].quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    return max(lower_bound, 0), upper_bound  # Ensure lower_bound is non-negative

# Sidebar
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Page 1 - Overview", "Page 2 - Overconsumption Analysis", "Page 3 - Consumption by Category"])

if page == "Page 1 - Overview":
    st.title("EFMS DATA DASHBOARD")
    
    # Get the unique values from the 'Long Description' column for the dropdown menu
    options = df['Long Description'].unique()

    # Add an 'All' option
    options = np.insert(options, 0, 'All')

    # Dropdown menu
    selected_option = st.sidebar.selectbox('Select equipment from the list', options)

    # Filter data based on the selected option
    if selected_option == 'All':
        filtered_df = df
    else:
            
        filtered_df = df[df['Long Description'] == selected_option]


    # Create a histogram of 'Txn FCU' for the filtered data
    # Plot only non-negative data and within IQR range
    range1 = iqr_range(filtered_df, 'Txn FCU')
    fig1 = px.histogram(filtered_df[(filtered_df['Txn FCU'] >= range1[0]) & (filtered_df['Txn FCU'] <= range1[1])], x="Txn FCU", nbins=30, title=f'( {selected_option} ) Histogram of Txn FCU')
    
    # Display the histogram
    st.plotly_chart(fig1)
    
    # Create a histogram of 'Fuel Qty' for the filtered data
    # Plot only non-negative data and within IQR range
    range2 = iqr_range(filtered_df, 'Fuel Qty')
    fig2 = px.histogram(filtered_df[(filtered_df['Fuel Qty'] >= range2[0]) & (filtered_df['Fuel Qty'] <= range2[1])], x="Fuel Qty", nbins=30, title=f'( {selected_option} ) Histogram of Fuel Qty')
    
    # Display the histogram
    st.plotly_chart(fig2)
    
    
    # Create a scatter plot of sum of 'ODO Diff' vs sum of 'Fuel Qty' for each plate
    grouped_df = filtered_df.groupby('Plate #').agg({'ODO Diff':'sum', 'Fuel Qty':'sum'}).reset_index()
    
    # Only include non-negative 'ODO Diff' values
    grouped_df = grouped_df[grouped_df['ODO Diff'] >= 0]
    
    fig3 = px.scatter(grouped_df, x="ODO Diff", y="Fuel Qty", hover_data=['Plate #'], title=f'( {selected_option} ) Scatter Plot of ODO Diff & Total Fuel Qty')
    fig3.update_traces(marker=dict(size=12, line=dict(width=2, color='DarkSlateGrey')))
    
    # Calculate IQR range for 'ODO Diff' and 'Fuel Qty' in grouped_df
    range_odo_diff = iqr_range(grouped_df, 'ODO Diff')
    range_fuel_qty = iqr_range(grouped_df, 'Fuel Qty')
    
    # Filter data within IQR range
    filtered_grouped_df = grouped_df[(grouped_df['ODO Diff'] >= range_odo_diff[0]) & (grouped_df['ODO Diff'] <= range_odo_diff[1]) & 
                                     (grouped_df['Fuel Qty'] >= range_fuel_qty[0]) & (grouped_df['Fuel Qty'] <= range_fuel_qty[1])]
    
    # Calculate the coefficients of the linear regression line using data within IQR range
    m, b = np.polyfit(filtered_grouped_df['ODO Diff'], filtered_grouped_df['Fuel Qty'], 1)
    
    # Add the regression line to the scatter plot
    fig3.add_trace(
        go.Scatter(
            x=grouped_df['ODO Diff'],
            y=m*grouped_df['ODO Diff'] + b,
            mode='lines',
            name='Regression Line',
            line=dict(color='red'),
            showlegend=False  # Do not show this trace in the legend
        )
    )

    # Display the scatter plot
    st.plotly_chart(fig3)
    
    # Display the slope in bold and with a larger font
    st.markdown(f"<h4 style='text-align: left; color: black;'>The slope of the regression line is <b>{m:.2f}</b></h4>", unsafe_allow_html=True)



#PAGE 2_____________________________________________________________________________________________


elif page == "Page 2 - Overconsumption Analysis":

    st.title("Transaction Analysis")

    # 1) Count of transactions
    transaction_count = df['Transaction Id'].count()
    st.markdown(f"<h2 style='text-align: left; color: black;'>Total number of Tnxs: <b>{transaction_count}</b></h2>", unsafe_allow_html=True)

    # 2) Count of overconsumption
    overconsumption_count = df['Overconsumption %'].dropna().count()  # Assuming non-blank means non-NA/null
    st.markdown(f"<h2 style='text-align: left; color: black;'>Count of Tnxs exceeding Limits: <b>{overconsumption_count}</b></h2>", unsafe_allow_html=True)

    # 3) Percentage of non-overconsuming transactions
    non_overconsumption_percentage = (transaction_count - overconsumption_count) / transaction_count * 100
    st.markdown(f"<h2 style='text-align: left; color: black;'>Percentage of Tnx within Limits: <b>{non_overconsumption_percentage:.2f}%</b></h2>", unsafe_allow_html=True)




    st.title("")
    st.title("Overconsuming Vehicles by Category")
    
    # Table: Overconsumption by 'Long Description'
    overconsumption_df = df.groupby('Long Description').agg({
        'Overconsumption %': 'count',
        'Overconsumption Liter': 'sum'
    }).reset_index()

    # Remove rows with 0 in 'Overconsumption %'
    overconsumption_df = overconsumption_df[overconsumption_df['Overconsumption %'] != 0]

    # Reset index starting from 1
    overconsumption_df.index = overconsumption_df.index + 1

    # Round 'Overconsumption Liter' to the nearest whole number
    overconsumption_df['Overconsumption Liter'] = overconsumption_df['Overconsumption Liter'].round(0)

    # Rename columns
    overconsumption_df = overconsumption_df.rename(columns={
        'Overconsumption %': 'No. of Tnxs above Limit',
        'Overconsumption Liter': 'Sum of LTRs above Limit'
    })

    st.dataframe(overconsumption_df)
    
    
    st.title("")
    st.title("Overconsumption by Plate")
    
    # Table: Overconsumption by 'Plate #'
    overconsumption_df = df.groupby('Plate #').agg({
        'Overconsumption Liter': 'sum',
        'Overconsumption %': 'count'
        
    }).reset_index()
    
    # Remove rows with 0 in 'Overconsumption %'
    overconsumption_df = overconsumption_df[overconsumption_df['Overconsumption %'] != 0]
    
    # Reset index starting from 1
    overconsumption_df.index = overconsumption_df.index + 1
    
    # Round 'Overconsumption Liter' to the nearest whole number
    overconsumption_df['Overconsumption Liter'] = overconsumption_df['Overconsumption Liter'].round(2)
    
    # Rename columns
    overconsumption_df = overconsumption_df.rename(columns={
        'Overconsumption Liter': 'Sum of LTRs above Limit',
        'Overconsumption %': 'No. of Tnxs above Limit'
        
    })

    # Create 'Tnx Weight' column
    overconsumption_df['Tnx Weight'] = overconsumption_df['Sum of LTRs above Limit'] / overconsumption_df['No. of Tnxs above Limit']
    
    st.dataframe(overconsumption_df)
    
    
    # Round the columns to the nearest whole number
    overconsumption_df["Sum of LTRs above Limit"] = np.round(overconsumption_df["Sum of LTRs above Limit"])
    overconsumption_df["No. of Tnxs above Limit"] = np.round(overconsumption_df["No. of Tnxs above Limit"])
    overconsumption_df["Tnx Weight"] = np.round(overconsumption_df["Tnx Weight"])

    # Scatter plot
    fig = px.scatter(overconsumption_df, x="Sum of LTRs above Limit", y="No. of Tnxs above Limit",
                     size='Tnx Weight', hover_data=['Plate #'],
                     title="Scatter Plot of Ltrs above Limit and Tnxs above Limit")
    
    # Update x-axis to start at 0
    fig.update_xaxes(range=[0, max(overconsumption_df["Sum of LTRs above Limit"])])

    st.plotly_chart(fig)
    
    
    
    
    
elif page == "Page 3 - Consumption by Category":

    st.title("Consumption by Category")
    
    st.header("By Long Description")

    # Group the dataframe by 'Long Description' and calculate the sum of 'Fuel Qty' and 'ODO Diff'
    consumption_df = df.groupby('Long Description').agg({'Fuel Qty': 'sum', 'ODO Diff': 'sum'}).reset_index()

    # Round the columns to the nearest whole number
    consumption_df = consumption_df.round()

    # Rename columns
    consumption_df = consumption_df.rename(columns={
        'Fuel Qty': 'Total Liters Qty',
        'ODO Diff': 'Total ODO'
    })

    # Add 'Average Consumption' column
    consumption_df['Average Consumption'] = consumption_df['Total Liters Qty'] / (consumption_df['Total ODO'] / 100)

    # Round 'Average Consumption' to two decimal places
    consumption_df['Average Consumption'] = consumption_df['Average Consumption'].round(2)

    # Display the table
    st.dataframe(consumption_df)

    st.header("By Plate #")

    # Group the dataframe by 'Plate #' and calculate the sum of 'Fuel Qty' and 'ODO Diff'
    consumption_df_plate = df.groupby('Plate #').agg({'Fuel Qty': 'sum', 'ODO Diff': 'sum'}).reset_index()

    # Round the columns to the nearest whole number
    consumption_df_plate = consumption_df_plate.round()

    # Rename columns
    consumption_df_plate = consumption_df_plate.rename(columns={
        'Fuel Qty': 'Total Liters Qty',
        'ODO Diff': 'Total ODO'
    })

    # Add 'Average Consumption' column
    consumption_df_plate['Average Consumption'] = consumption_df_plate['Total Liters Qty'] / (consumption_df_plate['Total ODO'] / 100)

    # Round 'Average Consumption' to two decimal places
    consumption_df_plate['Average Consumption'] = consumption_df_plate['Average Consumption'].round(2)

    # Display the table
    st.dataframe(consumption_df_plate)