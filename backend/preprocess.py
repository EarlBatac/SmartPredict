import pandas as pd
import numpy as np

def run_federation():
    print("Loading datasets with ISO-8859-1 encoding to handle special characters...")
    try:
        sales = pd.read_csv('Sales.csv', encoding='ISO-8859-1')
        products = pd.read_csv('Products.csv', encoding='ISO-8859-1')
        stores = pd.read_csv('Stores.csv', encoding='ISO-8859-1')
        customers = pd.read_csv('Customers.csv', encoding='ISO-8859-1')
    except Exception as e:
        print(f"Error loading raw files: {e}")
        return

    print("Datasets loaded successfully. Merging files...")
    df = sales.merge(products, on='ProductKey', how='left')
    df = df.merge(stores, on='StoreKey', how='left')
    df = df.merge(customers, on='CustomerKey', how='left')

    print("Filtering for United States ONLY...")
    if 'Country' in df.columns:
        df = df[df['Country'] == 'United States']
    if 'Country_cust' in df.columns:
        df = df[df['Country_cust'] == 'United States']
    if 'Currency Code' in df.columns:
        df = df[df['Currency Code'] == 'USD']

    print("Processing dates and calculating Delivery Gaps...")
    df['Order Date'] = pd.to_datetime(df['Order Date'], errors='coerce')
    df['Delivery Date'] = pd.to_datetime(df['Delivery Date'], errors='coerce')
    
    missing_delivery = df['Delivery Date'].isnull()
    if missing_delivery.any():
        np.random.seed(42)
        df.loc[missing_delivery, 'Delivery Date'] = df.loc[missing_delivery, 'Order Date'] + pd.to_timedelta(np.random.randint(1, 8, size=missing_delivery.sum()), unit='D')

    df['delivery_gap'] = (df['Delivery Date'] - df['Order Date']).dt.days

    print("Assigning dynamic Supplier Reliability...")
    def assign_reliability(gap):
        if gap <= 3: return 'High Performance'
        elif gap <= 5: return 'Average'
        else: return 'Low Performance'
    df['Supplier_Reliability'] = df['delivery_gap'].apply(assign_reliability)

    print("Engineering Seasonal and Machine Learning Features...")
    df['Month'] = df['Order Date'].dt.month
    df['DayOfWeek'] = df['Order Date'].dt.dayofweek
    df['Is_Holiday_Season'] = df['Month'].isin([11, 12, 6, 7]).astype(int)

    print("Categorizing Demand Nodes...")
    product_counts = df['Product Name'].value_counts()
    top_selling_names = product_counts.nlargest(20).index
    df['Is_Top_Selling'] = df['Product Name'].isin(top_selling_names)

    def assign_node(row):
        if product_counts.get(row['Product Name'], 0) < 50: return 'Occasional'
        elif row['Is_Holiday_Season'] == 1: return 'Seasonal'
        else: return 'Daily'
        
    df['Demand_Node'] = df.apply(assign_node, axis=1)

    print("Saving federated dataset...")
    try:
        df.to_csv('Federated_Electronics_Data.csv', index=False)
        print("Federated_Electronics_Data.csv generated!")
    except PermissionError:
        print("\n❌ CRITICAL ERROR: Permission Denied.")
        print("Please CLOSE the 'Federated_Electronics_Data.csv' file if it is open in Excel.")
        print("Also, make sure to STOP the Flask server (app.py) before running this script.")

if __name__ == "__main__":
    run_federation()

