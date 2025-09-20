from flask import Flask, render_template, request, jsonify
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
import warnings
warnings.filterwarnings("ignore")

app = Flask(__name__)

# Global variables
model = None
area_encoder = LabelEncoder()
item_encoder = LabelEncoder()
df = None

def load_and_train_model():
    global model, area_encoder, item_encoder, df
    
    print("Loading data...")
    # Load data
    df = pd.read_csv("yield_df.csv")
    
    # Remove unnamed column if it exists
    if 'Unnamed: 0' in df.columns:
        df.drop('Unnamed: 0', axis=1, inplace=True)
    
    # Remove duplicates
    df.drop_duplicates(inplace=True)
    print(f"Data loaded: {df.shape}")
    
    # Prepare data
    X = df[['Area', 'Item', 'Year', 'average_rain_fall_mm_per_year', 'pesticides_tonnes', 'avg_temp']].copy()
    y = df['hg/ha_yield']
    
    # Encode categorical variables
    X['Area_encoded'] = area_encoder.fit_transform(X['Area'])
    X['Item_encoded'] = item_encoder.fit_transform(X['Item'])
    
    # Use only numerical features
    X_numeric = X[['Area_encoded', 'Item_encoded', 'Year', 'average_rain_fall_mm_per_year', 'pesticides_tonnes', 'avg_temp']]
    
    print("Training model...")
    # Train simple Random Forest
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_numeric, y)
    
    print("Model trained successfully!")
    return True

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    try:
        if model is None:
            return jsonify({'error': 'Model not loaded'})
        
        # Get form data
        area = request.form['area']
        item = request.form['item']
        year = int(request.form['year'])
        rainfall = float(request.form['rainfall'])
        pesticides = float(request.form['pesticides'])
        temperature = float(request.form['temperature'])
        
        # Encode categorical variables
        try:
            area_encoded = area_encoder.transform([area])[0]
        except ValueError:
            # If area not in training data, use most common area
            area_encoded = 0
        
        try:
            item_encoded = item_encoder.transform([item])[0]
        except ValueError:
            # If item not in training data, use most common item
            item_encoded = 0
        
        # Create input array
        input_data = np.array([[area_encoded, item_encoded, year, rainfall, pesticides, temperature]])
        
        # Make prediction
        prediction = model.predict(input_data)[0]
        
        return jsonify({
            'success': True,
            'prediction': round(prediction, 2)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/get_areas')
def get_areas():
    if df is not None:
        areas = sorted(df['Area'].unique().tolist())
        return jsonify(areas)
    return jsonify([])

@app.route('/get_items')
def get_items():
    if df is not None:
        items = sorted(df['Item'].unique().tolist())
        return jsonify(items)
    return jsonify([])

if __name__ == '__main__':
    print("Starting application...")
    load_and_train_model()
    app.run(debug=True, port=5000)
