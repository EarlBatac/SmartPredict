import pandas as pd
import numpy as np
import xgboost as xgb
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split

def run_model_training():
    print("Loading Federated dataset...")
    df = pd.read_csv('Federated_Electronics_Data.csv')
    

    qty_col = 'Order Item Quantity' if 'Order Item Quantity' in df.columns else 'Quantity'
    if qty_col not in df.columns:
        print("Warning: Quantity column not found. Defaulting to 1 unit per order.")
        df[qty_col] = 1 
        
    df['Order Item Quantity'] = pd.to_numeric(df[qty_col], errors='coerce').fillna(1)
    
  
    if 'Order Date' in df.columns:
        df['Order Date'] = pd.to_datetime(df['Order Date'], errors='coerce')
        if 'Month' not in df.columns:
            df['Month'] = df['Order Date'].dt.month
        if 'DayOfWeek' not in df.columns:
            df['DayOfWeek'] = df['Order Date'].dt.dayofweek
        if 'Is_Holiday_Season' not in df.columns:
            df['Is_Holiday_Season'] = df['Month'].isin([11, 12, 6, 7]).astype(int)

     
    features = ['Month', 'DayOfWeek', 'Is_Holiday_Season', 'Square Meters']
    
    for col in features:
        df[col] = pd.to_numeric(df.get(col, 0), errors='coerce').fillna(0)
        
    X = df[features]
    y = df['Order Item Quantity']
    
    print("Splitting data: 80% Training / 20% Testing...")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    
    print("Training XGBoost Regressor...")
    model = xgb.XGBRegressor(objective='reg:squarederror', n_estimators=100, learning_rate=0.1, random_state=42)
    
    
    eval_set = [(X_train, y_train), (X_test, y_test)]
    model.fit(X_train, y_train, eval_set=eval_set, verbose=False)
    
   
    print("Generating Training Progress Graph")
    results = model.evals_result()
    epochs = len(results['validation_0']['rmse'])
    x_axis = range(0, epochs)
    
    plt.figure(figsize=(8, 5))
    plt.plot(x_axis, results['validation_0']['rmse'], label='Train Loss (RMSE)', color='blue')
    plt.plot(x_axis, results['validation_1']['rmse'], label='Test Validation Loss', color='orange')
    plt.legend()
    plt.ylabel('RMSE (Error Rate)')
    plt.xlabel('Training Epochs (Trees built)')
    plt.title('Machine Learning Training Progress: Loss Reduction')
    plt.tight_layout()
    plt.savefig('Training_Progress.png', dpi=300)
    print("✅ Saved: Training_Progress.png")
    
   
    print("Generating Feature Importance Graph")
    plt.figure(figsize=(8, 5))
    xgb.plot_importance(model, max_num_features=4, importance_type='weight', color='green')
    plt.title('XGBoost Feature Selection Importance')
    plt.tight_layout()
    plt.savefig('Feature_Importance.png', dpi=300)
    print("✅ Saved: Feature_Importance.png")
    
    print("\nTraining complete! \.")

if __name__ == "__main__":
    run_model_training()

