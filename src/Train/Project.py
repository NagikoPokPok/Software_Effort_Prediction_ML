import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import matplotlib.pyplot as plt
import seaborn as sns
import joblib

# 1. Tải dữ liệu
print("Step 1: Loading data")
data = pd.read_csv('../../dataset/COCOMO-81.csv', sep=',')
print(f"Number of samples: {data.shape[0]}")
print(f"Features: {', '.join(data.columns)}")
print("\nDescriptive statistics:")
print(data.describe())

# 2. Tiền xử lý dữ liệu
print("\nStep 2: Data preprocessing")

# 2.1 Chọn đặc trưng và biến mục tiêu
cost_drivers = ['rely', 'data', 'cplx', 'time', 'stor', 'virt', 'turn', 
                'acap', 'aexp', 'pcap', 'vexp', 'lexp', 'modp', 'tool', 'sced']

# Add development mode as categorical feature using one-hot encoding
data_encoded = pd.get_dummies(data, columns=['dev_mode'], prefix=['mode'])

# Create feature set with LOC and cost drivers
X = pd.concat([
    data[['loc'] + cost_drivers], 
    data_encoded[['mode_embedded', 'mode_organic', 'mode_semidetached']]
], axis=1)

y = data['actual']  # Actual effort is the target variable

# 2.2 Kiểm tra và xử lý giá trị thiếu
missing_values = X.isnull().sum()
print(f"Missing values in each feature:\n{missing_values}")

# Handle missing values like in Project_2.py
for col in X.columns:
    if X[col].dtype == 'object':  # Categorical data
        fill_value = X[col].mode()[0]
    else:  # Numerical data
        fill_value = X[col].median()
    X[col].fillna(fill_value, inplace=True)

print(f"Number of samples after handling missing values: {X.shape[0]}")

# 2.3 Chuẩn hóa dữ liệu
print("\nStep 2.3: Feature scaling")
scaler = StandardScaler()
# Lưu trữ các cột cần chuẩn hóa
numeric_features = X.select_dtypes(include=['float64', 'int64']).columns
# Tạo bản sao để giữ lại phiên bản chưa chuẩn hóa
X_unscaled = X.copy()
# Chuẩn hóa dữ liệu
X[numeric_features] = scaler.fit_transform(X[numeric_features])
y_log = np.log1p(y)

# Hiển thị thông tin chuẩn hóa
stats_df = pd.DataFrame({
    "Feature": numeric_features,
    "Mean": scaler.mean_,
    "Standard Deviation": scaler.scale_
})

print("\nMean and Standard Deviation for each feature:")
print(stats_df.to_string(index=False))

# In dữ liệu đã chuẩn hóa (5 dòng đầu)
print("\nNormalized data (first 5 rows):")
print(X.head())

# 3. Chia dữ liệu thành tập huấn luyện và tập kiểm tra
print("\nStep 3: Splitting data into training and testing sets")
X_train, X_test, y_train, y_test = train_test_split(X, y_log, test_size=0.2, random_state=42)
print(f"Training samples: {X_train.shape[0]}")
print(f"Testing samples: {X_test.shape[0]}")

# 4. Huấn luyện các mô hình Machine Learning
print("\nStep 4: Training Machine Learning models")

# 4.1 Linear Regression
print("Training Linear Regression model...")
lr_model = LinearRegression()
lr_model.fit(X_train, y_train)
print(f"Regression coefficients: {lr_model.coef_}")
print(f"Intercept: {lr_model.intercept_}")

# 4.2 Decision Tree
print("\nTraining Decision Tree model...")
dt_model = DecisionTreeRegressor(max_depth=5, random_state=42)
dt_model.fit(X_train, y_train)
print(f"Tree depth: {dt_model.get_depth()}")
print(f"Number of leaf nodes: {dt_model.get_n_leaves()}")

# 4.3 Random Forest
print("\nTraining Random Forest model...")
rf_model = RandomForestRegressor(n_estimators=100, random_state=42)
rf_model.fit(X_train, y_train)
print(f"Number of trees: {rf_model.n_estimators}")

# 5. COCOMO II
print("\nStep 5: Implementing COCOMO models")

# Function to calculate COCOMO I effort
def calculate_cocomo_effort(row):
    # Get development mode coefficients
    if 'mode_organic' in row and row['mode_organic'] == 1:
        a, b = 2.4, 1.05
    elif 'mode_semidetached' in row and row['mode_semidetached'] == 1:
        a, b = 3.0, 1.12
    elif 'mode_embedded' in row and row['mode_embedded'] == 1:
        a, b = 3.6, 1.20
    elif 'dev_mode' in row:
        if row['dev_mode'] == 'organic':
            a, b = 2.4, 1.05
        elif row['dev_mode'] == 'semidetached':
            a, b = 3.0, 1.12
        else:  # embedded
            a, b = 3.6, 1.20
    else:
        # Default to embedded mode if no information is available
        a, b = 3.6, 1.20
    
    # Calculate Effort Multiplier (EM) based on cost drivers
    em = 1.0
    for driver in cost_drivers:
        if driver in row:
            em *= row[driver]
    
    # Calculate COCOMO effort: E = a × (KLOC)^b × EM
    kloc = row['loc'] 
    effort = a * (kloc ** b) * em
    
    return np.log1p(effort)

# Apply COCOMO calculation
data['effort_cocomo'] = data.apply(calculate_cocomo_effort, axis=1)

# Get predictions for test set
test_indices = y_test.index
cocomo_pred = data.loc[test_indices, 'effort_cocomo'].values

# 6. Make predictions and evaluate models
print("\nStep 6: Making predictions and evaluating models")

# Predictions from ML models
lr_pred = lr_model.predict(X_test)
dt_pred = dt_model.predict(X_test)
rf_pred = rf_model.predict(X_test)

# Evaluation function
def evaluate_model(y_true, y_pred, model_name):
    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    r2 = r2_score(y_true, y_pred)
    
    print(f"--- {model_name} ---")
    print(f"MAE: {mae:.2f}")
    print(f"RMSE: {rmse:.2f}")
    print(f"R²: {r2:.2f}")
    
    return {'mae': mae, 'rmse': rmse, 'r2': r2}

# Evaluate all models, including COCOMO
results = {}
results['COCOMO I'] = evaluate_model(y_test, cocomo_pred, "COCOMO I")
results['Linear Regression'] = evaluate_model(y_test, lr_pred, "Linear Regression")
results['Decision Tree'] = evaluate_model(y_test, dt_pred, "Decision Tree")
results['Random Forest'] = evaluate_model(y_test, rf_pred, "Random Forest")

results_df = pd.DataFrame({
    'Actual': y_test,
    'COCOMO': cocomo_pred,
    'Linear Regression': lr_pred,
    'Decision Tree': dt_pred,
    'Random Forest': rf_pred
})
print("Dự đoán nỗ lực cho 10 mẫu thử đầu tiên (tính bằng tháng-người):")
print(results_df.head(10))

# 7. Visualize results
print("\nStep 7: Visualizing results")

plt.figure(figsize=(16, 14))

# 7.1 Scatter plot comparing actual vs predicted values
plt.subplot(2, 2, 1)
plt.scatter(y_test, cocomo_pred, label='COCOMO I', alpha=0.5, color='blue')
plt.scatter(y_test, lr_pred, label='Linear Regression', alpha=0.5, color='red')
plt.scatter(y_test, dt_pred, label='Decision Tree', alpha=0.5, color='green')
plt.scatter(y_test, rf_pred, label='Random Forest', alpha=0.5, color='purple')
plt.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 'k--', lw=2)
plt.xlabel('Actual Effort (person-months)')
plt.ylabel('Predicted Effort (person-months)')
plt.title('Actual vs Predicted Effort')
plt.legend()
plt.grid(True)

# 7.2 Compare errors across models
plt.subplot(2, 2, 2)
models = list(results.keys())
mae_values = [results[model]['mae'] for model in models]
rmse_values = [results[model]['rmse'] for model in models]

x = np.arange(len(models))
width = 0.35

plt.bar(x - width/2, mae_values, width, label='MAE')
plt.bar(x + width/2, rmse_values, width, label='RMSE')
plt.xticks(x, models, rotation=45)
plt.ylabel('Error (person-months)')
plt.title('MAE and RMSE Comparison Across Models')
plt.legend()
plt.grid(True)

# 7.3 R² comparison
plt.subplot(2, 2, 3)
r2_values = [results[model]['r2'] for model in models]
plt.bar(models, r2_values, color='lightgreen')
plt.ylabel('R² Score')
plt.title('R² Comparison Across Models')
plt.xticks(rotation=45)
plt.axhline(y=0, color='r', linestyle='-')
plt.grid(True)

# Save visualizations
plt.figure(1)
plt.tight_layout()
plt.savefig('../../img/cocomo_effort_prediction_results.png')

# 8. Find best model and provide conclusions
print("\nStep 8: Conclusions and recommendations")
best_model = min(results, key=lambda x: results[x]['rmse'])
print(f"Best performing model based on RMSE: {best_model}")
print(f"MAE: {results[best_model]['mae']:.2f}")
print(f"RMSE: {results[best_model]['rmse']:.2f}")
print(f"R²: {results[best_model]['r2']:.2f}")

# Create a dictionary mapping model names to their objects
model_objects = {
    'COCOMO I': None,  # COCOMO không có model object
    'Linear Regression': lr_model,
    'Decision Tree': dt_model,
    'Random Forest': rf_model
}

# Save the best model if it's not COCOMO
if best_model != 'COCOMO I':
    best_model_object = model_objects[best_model]
    joblib.dump(best_model_object, 'trained_model.pkl')
    joblib.dump(scaler, 'scaler.pkl')
    print(f"Saved {best_model} model and scaler to disk")
else:
    print("COCOMO I was the best model but it doesn't need to be saved as it's a formula-based approach")