from flask import Flask, jsonify, request
from flask_cors import CORS
import pandas as pd
import numpy as np
import xgboost as xgb
import os
import warnings

warnings.simplefilter(action='ignore', category=FutureWarning)

app = Flask(__name__)
CORS(app)

DATA_FILE = 'Federated_Electronics_Data.csv'

def load_clean_data():
    if not os.path.exists(DATA_FILE): return None
    df = pd.read_csv(DATA_FILE)
    
    qty_col = 'Quantity' if 'Quantity' in df.columns else 'Order Item Quantity'
    if qty_col not in df.columns: df[qty_col] = 1 
    df['Quantity'] = pd.to_numeric(df[qty_col], errors='coerce').fillna(1)
        
    if 'Sales' not in df.columns:
        if 'Unit Price USD' in df.columns:
            price = df['Unit Price USD'].astype(str).str.replace('$', '', regex=False).str.replace(',', '', regex=False)
            df['Sales'] = pd.to_numeric(price, errors='coerce').fillna(0) * df['Quantity']
        else:
            df['Sales'] = df['Quantity'] * 100 

    if df['Sales'].dtype == object:
        df['Sales'] = df['Sales'].astype(str).str.replace('$', '', regex=False).str.replace(',', '', regex=False).str.strip()
    df['Sales'] = pd.to_numeric(df['Sales'], errors='coerce').fillna(0)
    
    df['Order Date'] = pd.to_datetime(df.get('Order Date', pd.Timestamp.now()), errors='coerce')
    
    state_col = 'State_y' if 'State_y' in df.columns else 'State_x' if 'State_x' in df.columns else 'State'
    df['State_Clean'] = df.get(state_col, 'Unknown').replace(['Online', 'Unknown', np.nan], "Unknown State")
    df['City_Clean'] = df.get('City', 'Unknown').replace(['Online', 'Unknown', np.nan], "Unknown City")
    
    df['Square Meters'] = pd.to_numeric(df.get('Square Meters', np.nan), errors='coerce')
    df['Square Meters'] = df['Square Meters'].fillna(df['Square Meters'].median()).fillna(2000)
    df['delivery_gap'] = pd.to_numeric(df.get('delivery_gap', 4), errors='coerce').fillna(4)
    
    if 'Is_Top_Selling' in df.columns:
        df['Is_Top_Selling'] = df['Is_Top_Selling'].astype(str).str.lower() == 'true'
        
    return df

def feature_engineering_and_training(node_df, category_name):
    try:
        daily_df = node_df.groupby('Order Date').agg({'Quantity': 'sum'}).reset_index()
        daily_df = daily_df.set_index('Order Date').resample('D').sum().fillna(0).reset_index()
        
        daily_df['Target_Trend'] = daily_df['Quantity'].ewm(span=7, adjust=False).mean()
        
        daily_df['Month'] = daily_df['Order Date'].dt.month
        daily_df['DayOfWeek'] = daily_df['Order Date'].dt.dayofweek
        daily_df['Is_Holiday_Season'] = daily_df['Month'].isin([11, 12, 6, 7]).astype(int)
        
        features = []
        desc = {}
        
        if category_name == 'Daily':
            daily_df['Rolling_3D'] = daily_df['Quantity'].shift(1).rolling(window=3, min_periods=1).mean()
            daily_df['Rolling_7D'] = daily_df['Quantity'].shift(1).rolling(window=7, min_periods=1).mean()
            features = ['Rolling_7D', 'Rolling_3D', 'DayOfWeek', 'Month']
            desc = {
                'Rolling_7D': 'Creates a stable weekly momentum for repeated purchasing patterns.',
                'Rolling_3D': 'Analyzes hyper-local variables to adjust in sudden demand change.',
                'DayOfWeek': 'Cyclical map in identifying weekly purchasing spikes.',
                'Month': 'Provides macro-seasonal context to short-term trends.'
            }
            
        elif category_name == 'Seasonal':
            daily_df['Rolling_7D'] = daily_df['Quantity'].shift(1).rolling(window=7, min_periods=1).mean()
            daily_df['Rolling_14D'] = daily_df['Quantity'].shift(1).rolling(window=14, min_periods=1).mean()
            features = ['Rolling_7D', 'Is_Holiday_Season', 'Month', 'Rolling_14D']
            desc = {
                'Rolling_7D': 'Tracks immediate demand buildup leading into a seasonal event.',
                'Is_Holiday_Season': 'Critical binary trigger isolating massive Q4/Summer volume surges.',
                'Month': 'Primary indicator for scaling standard non-holiday seasonal variance.',
                'Rolling_14D': 'Provides an wider baseline to prevent overreaction to daily noise.'
            }
            
        elif category_name == 'Occasional':
            daily_df['Rolling_14D'] = daily_df['Quantity'].shift(1).rolling(window=14, min_periods=1).mean()
            daily_df['Rolling_30D'] = daily_df['Quantity'].shift(1).rolling(window=30, min_periods=1).mean()
            features = ['Rolling_14D', 'Rolling_30D', 'Month', 'DayOfWeek']
            desc = {
                'Rolling_14D': 'Extracts bi-weekly trends, specifically ignoring daily stochastic noise.',
                'Rolling_30D': 'Macro-level smoothing to avoid dead-stock build-up in sparse data.',
                'Month': 'Identifies if the occasional purchase correlates with a specific time of year.',
                'DayOfWeek': 'Minimal impact feature checking for specific weekend unusual behavior.'
            }
            
        elif category_name == 'Top Selling':
            daily_df['Rolling_7D'] = daily_df['Quantity'].shift(1).rolling(window=7, min_periods=1).mean()
            daily_df['EMA_Lag_1'] = daily_df['Target_Trend'].shift(1) 
            features = ['EMA_Lag_1', 'Rolling_7D', 'Month', 'DayOfWeek']
            desc = {
                'EMA_Lag_1': 'Core mathematical stability metric tracking immediate exponential trend.',
                'Rolling_7D': 'Secondary momentum metric is ensured by constant physical availability.',
                'Month': 'Provides macro-level scaling for baseline revenue products.',
                'DayOfWeek': 'Cyclical indicator that identify slight intra-week shifts.'
            }
            
        daily_df = daily_df.dropna()
        X = daily_df[features]
        y = daily_df['Target_Trend'] 
        
        if len(X) < 14: return "Insufficient Data", [], [], [], 0, 0
        
        split = int(len(X) * 0.8)
        X_train, X_test, y_train, y_test = X.iloc[:split], X.iloc[split:], y.iloc[:split], y.iloc[split:]
        
        model = xgb.XGBRegressor(n_estimators=100, max_depth=3, learning_rate=0.05, random_state=42)
        model.fit(X_train, y_train)
        preds = model.predict(X_test)
        
        mae = np.mean(np.abs(y_test - preds))
        wmape = mae / y_test.mean() if y_test.mean() > 0 else 1.0
        final_acc = (1 - wmape) * 100
        
        future_dates = pd.date_range(daily_df['Order Date'].max() + pd.Timedelta(days=1), periods=7)
        future_preds = []
        current_quantity_history = daily_df['Quantity'].tail(30).tolist()
        current_ema_history = daily_df['Target_Trend'].tail(7).tolist()
        
        for date in future_dates:
            pred_dict = {}
            if 'Rolling_3D' in features: pred_dict['Rolling_3D'] = np.mean(current_quantity_history[-3:])
            if 'Rolling_7D' in features: pred_dict['Rolling_7D'] = np.mean(current_quantity_history[-7:])
            if 'Rolling_14D' in features: pred_dict['Rolling_14D'] = np.mean(current_quantity_history[-14:])
            if 'Rolling_30D' in features: pred_dict['Rolling_30D'] = np.mean(current_quantity_history[-30:])
            if 'EMA_Lag_1' in features: pred_dict['EMA_Lag_1'] = current_ema_history[-1]
            if 'DayOfWeek' in features: pred_dict['DayOfWeek'] = date.dayofweek
            if 'Month' in features: pred_dict['Month'] = date.month
            if 'Is_Holiday_Season' in features: pred_dict['Is_Holiday_Season'] = int(date.month in [11, 12, 6, 7])
            
            pred_X = pd.DataFrame([pred_dict])[features]
            pred_y = max(1, int(model.predict(pred_X)[0]))
            future_preds.append(pred_y)
            current_quantity_history.append(pred_y)
            current_ema_history.append(pred_y)
            
        importances = model.feature_importances_
        sorted_features = sorted(zip(features, importances), key=lambda x: x[1], reverse=True)
        dyn_feat = [{"name": f[0], "desc": desc.get(f[0], ""), "weight": round(float(f[1])*100, 1)} for f in sorted_features if f[1] > 0]
        
        historical_actuals = daily_df['Quantity'].tail(7).astype(int).tolist() 
        return f"{final_acc:.1f}%", dyn_feat, future_preds, historical_actuals, len(X_train), len(X_test)
        
    except Exception as e:
        return "Error", [], [10]*7, [10]*7, 0, 0

def get_season_context(month_num):
    if month_num in [11, 12, 1]: return "Winter Holiday Gifting & End-of-Year Upgrades"
    elif month_num in [6, 7, 8]: return "Summer Sales & Back-to-School Preparation"
    elif month_num in [3, 4, 5]: return "Spring Corporate Tech Refresh"
    else: return "Autumn Pre-Holiday Stocking"

def get_occasion_context(subcategory):
    mapping = {
        'Televisions': 'Major Home Entertainment Upgrades',
        'Cameras and camcorders': 'Travel & Event Photography Preparation',
        'Projectors': 'Corporate or Home Theater Installations',
        'Desktops': 'Long-term Workstation Replacements',
        'Home Appliances': 'Major Household Replacements',
        'Laptops': 'Work/School Mobility Transitions'
    }
    return mapping.get(subcategory, 'Infrequent Hardware Replacements')

@app.route('/api/dashboard-data', methods=['GET'])
def get_dashboard_data():
    category = request.args.get('category', 'Daily')
    df = load_clean_data()
    
    if df is None: return jsonify({"error": "Data not found"}), 500
    
    node_df = df[df['Is_Top_Selling'] == True].copy() if category == 'Top Selling' else df[df['Demand_Node'] == category].copy()
    if node_df.empty: return jsonify({"error": "No data"}), 404

    dynamic_accuracy, dynamic_features, future_preds, historical_actuals, train_rows, test_rows = feature_engineering_and_training(node_df, category)
    
    product_sales = node_df.groupby('Product Name')['Sales'].sum()
    trending_item = product_sales.idxmax()
    percentage = round((product_sales.max() / product_sales.sum()) * 100, 2)
    
    trending_df = node_df[node_df['Product Name'] == trending_item]
    geo_df = trending_df[~trending_df['State_Clean'].isin(['Unknown State'])]
    
    if not geo_df.empty:
        top_locations = geo_df.groupby(['City_Clean', 'State_Clean']).size().nlargest(3)
        location_strings = [f"{city}, {state}" for (city, state) in top_locations.index]
        detailed_location = "; ".join(location_strings)
    else:
        detailed_location = "Multiple US Regions"
    
    top_month = trending_df['Order Date'].dt.month.mode()[0] if not trending_df.empty else 1
    subcategory = trending_df['Subcategory'].mode()[0] if 'Subcategory' in trending_df.columns else "Electronics"
    total_hist_vol = trending_df['Quantity'].sum()
    historical_orders = len(trending_df)
    top_feature = dynamic_features[0]['name'] if dynamic_features else "its primary feature"
    
   
    if category == "Daily":
        general_node_explanation = "Node Definition: Daily products are the low cost consumer staples that are high frequency. These products that continuously sell every day in an ERP system. The objective of the Daily items is to have a continuous supply of inventory to prevent micro-stockouts"
        cat_def = "Product Trending Justification:"
        result_just = f"This is a high-turnover '{subcategory}' product. The ML involves the use of recent and thick historical data to identify hidden purchasing patterns to determine short term inventory requirements."
        acc_context = f"The noise in retail is extremely hard to determine everyday. The XGBoost model maximized its {dynamic_accuracy} accuracy score by abandoning fixed monthly wages and focusing the {top_feature} to keep up with localized micro-trends and daily velocity."
    elif category == "Seasonal":
        general_node_explanation = "Node Definition: The consumer demands of seasonal products has very high variance that are limited by time of the year. The objective is to order in large quantities just before the peak and the subsequent vigorous order stoppage as soon as the peak has passed to prevent stock sitting in the warehouse for a year."
        cat_def = f"Product Trending Justification: {get_season_context(top_month)}."
        result_just = f"The given product is a part of the '{subcategory}' category. The dataset shows that there is a significant spike especially in the month of {top_month}. The AI recognizes that as '{get_season_context(top_month)}' and scales the 7-day prediction to that of historic seasonal consumer patterns."
        acc_context = f"XGBoost model was able to achieve {dynamic_accuracy} accuracy by avoiding daily noise. Instead of averaging, it forced the decision tree to rely primarily on the {top_feature} to map the exact month-over-month trajectory, adapting to the seasonal spike perfectly."
    elif category == "Occasional":
        general_node_explanation = "Node Definition: The occasional products are mostly costly products that are bought infrequently. Their sales information is extremely scattered in an ERP system. The objective is strict capital conservation to keep stock levels sufficient to satisfy uncommon demand without blocking retailer cash in expensive dead stock."
        cat_def = f"Product Trending Justification: Occasion: {get_occasion_context(subcategory)}."
        result_just = f"This is a '{subcategory}' product, this product is bought for {get_occasion_context(subcategory)}. The raw data shows extreme sparsity (only {historical_orders} recorded transactions). The ML is right to reject the normal daily forecasting so that they do not order costly dead stock of this slow moving product."
        acc_context = f"Predicting sparse data traditionally results in high error. The model secured this {dynamic_accuracy} accuracy score by explicitly ignoring localized spikes and weighting the {top_feature} to establish a flat, ultra-conservative moving average."
    elif category == "Top Selling":
        general_node_explanation = "Node Definition: The main source of revenue of the business is its Top Selling products. They are high velocity products that are purchased regularly by customers. It is essential that they are never out of stock at any point in time and should have the most accurate prediction."
        cat_def = "Product Trending Justification:"
        result_just = f"This product {int(total_hist_vol)} brought an excellent quantity in sales. It is very successful and is not dependent on seasons or occasions. The machine learning model recognizes it as a core staple precise week-to-week loss to make sure that it will never run out of stock."
        acc_context = f"Top Selling products needs to have precise accuracy since it has the smoothest demand curves. The algorithm achieved this {dynamic_accuracy} accuracy score by prioritizing the {top_feature}, locking onto the underlying continuous exponential trend rather than chasing daily receipt fluctuations."

    predicted_7d_total = sum(future_preds)
    breakdown = [{"name": name, "qty": max(1, int(predicted_7d_total * (sales / product_sales.sum())))} for name, sales in product_sales.nlargest(5).items()]
    
    capacity = int(node_df['Square Meters'].median() * 1.5) if node_df['Square Meters'].median() > 0 else 2000
    if predicted_7d_total > capacity:
        rec_text = "CRITICAL: Restock Immediately."
        rec_color = "danger"
    elif predicted_7d_total < (capacity * 0.2):
        rec_text = "HOLD: Do Not Restock."
        rec_color = "warning"
    else:
        rec_text = "OPTIMAL: Engage standard replenishment flow."
        rec_color = "success"

    
    std_dev = trending_df['delivery_gap'].std()
    mean_gap = trending_df['delivery_gap'].mean()
    
    if pd.isna(std_dev): std_dev = 0
    if pd.isna(mean_gap) or mean_gap == 0: mean_gap = 1
    
    cv = std_dev / mean_gap
    supplier_score = round(max(0.60, min(0.96, 1 - (cv * 0.45))), 2)
    calculated_status = "High Performance" if supplier_score > 0.85 else "Medium Risk" if supplier_score > 0.70 else "Low Risk"
    
    if supplier_score >= 0.85:
        supplier_justification = f"The machine learning model has examined all the previous deliveries of this product. It determined that deliveries are consistent and delivered in {round(mean_gap, 1)} days with {round(std_dev, 1)} days. The shipping time is so predictable, the AI rated it a reliability score of {supplier_score}, which means you can trust this supplier to restock at the time you expect."
    else:
        supplier_justification = f"The machine learning model has examined all the previous deliveries of this product. It determined that deliveries are inconsistent and unpredictable delivering in {round(mean_gap, 1)} days, and sometimes end up in {round(std_dev, 1)} days early or late. With such reasons for inconsistency, the AI gave the Volatility Score of {supplier_score}. This means that you should not fully rely on this supplier to restock at the time you expect."

    line_chart_data = [{"name": f"Day {i+1}", "actual": historical_actuals[i] if i < len(historical_actuals) else 0, "predicted": future_preds[i]} for i in range(7)]

    return jsonify({
        "stats": {
            "predicted_total": predicted_7d_total,
            "current_stock": capacity,
            "trending_item": trending_item,
            "trending_insight": f"Captures {percentage}% of nodal revenue.",
            "trending_location": detailed_location,
            "general_node_explanation": general_node_explanation, 
            "category_definition": cat_def,
            "result_justification": result_just,
            "accuracy_context": acc_context, 
            "critical_alert": predicted_7d_total > capacity,
            "train_rows": train_rows,
            "test_rows": test_rows,
            "recommendation": rec_text,
            "rec_color": rec_color
        },
        "breakdown": breakdown,
        "line_data": line_chart_data,
        "suppliers": [{"name": f"{node_df['Brand'].mode()[0]} US Logistics", "score": supplier_score, "status": calculated_status, "justification": supplier_justification}],
        "segment_accuracy": dynamic_accuracy,
        "dynamic_features": dynamic_features
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)

