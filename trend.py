import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.gridspec as gridspec
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import TimeSeriesSplit, RandomizedSearchCV
from statsmodels.tsa.arima.model import ARIMA
import tensorflow as tf
from keras.models import Sequential
from keras.layers import LSTM, Dense, Dropout
from keras.callbacks import EarlyStopping
from keras.optimizers import Adam
import shap
import datetime
import warnings
warnings.filterwarnings('ignore')

class BusinessTrendPredictor:
    def __init__(self, root):
        self.root = root
        self.root.title("Advanced Business Trend Predictor")
        self.root.geometry("1200x750")
        self.root.configure(bg="#f0f0f0")
        
        self.data = None
        self.models = {
            "Linear Regression": LinearRegression(),
            "Random Forest": RandomForestRegressor(n_estimators=100, random_state=42),
            "ARIMA": "ARIMA",  # Handled separately
            "LSTM": "LSTM",    # Handled separately
            "Hybrid (Prophet+LSTM)": "Hybrid",  # Handled separately
            "AutoML": "AutoML"  # Handled separately
        }
        
        self.anomaly_models = {
            "None": None,
            "Isolation Forest": IsolationForest(contamination=0.05, random_state=42),
            "Local Outlier Factor": LocalOutlierFactor(contamination=0.05, novelty=True)
        }
        
        self.setup_ui()
    
    def setup_ui(self):
        # Create notebook for tabbed interface
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Main tab
        main_tab = ttk.Frame(self.notebook)
        self.notebook.add(main_tab, text="Dashboard")
        
        # Anomaly Detection tab
        anomaly_tab = ttk.Frame(self.notebook)
        self.notebook.add(anomaly_tab, text="Anomaly Detection")
        
        # Explainable AI tab
        xai_tab = ttk.Frame(self.notebook)
        self.notebook.add(xai_tab, text="Explainable AI")
        
        # Setup main dashboard tab
        self.setup_main_tab(main_tab)
        
        # Setup anomaly detection tab
        self.setup_anomaly_tab(anomaly_tab)
        
        # Setup XAI tab
        self.setup_xai_tab(xai_tab)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready. Import data to begin.")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def setup_main_tab(self, parent):
    # Main frame
        main_frame = ttk.Frame(parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    # Left sidebar for controls - NOW WITH SCROLLING
        control_outer_frame = ttk.LabelFrame(main_frame, text="Controls")
        control_outer_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
    
    # Add a canvas and scrollbar for scrolling
        control_canvas = tk.Canvas(control_outer_frame, width=200)
        scrollbar = ttk.Scrollbar(control_outer_frame, orient="vertical", command=control_canvas.yview)
        control_frame = ttk.Frame(control_canvas)
    
        # Configure the canvas
        control_canvas.configure(yscrollcommand=scrollbar.set)
        control_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Add the frame to the canvas
        canvas_frame = control_canvas.create_window((0, 0), window=control_frame, anchor="nw")
        
        # Configure scrolling behavior
        def configure_canvas(event):
            control_canvas.configure(scrollregion=control_canvas.bbox("all"))
            control_canvas.itemconfig(canvas_frame, width=control_canvas.winfo_width())
            
        control_frame.bind("<Configure>", configure_canvas)
        control_canvas.bind("<Configure>", lambda e: control_canvas.itemconfig(canvas_frame, width=control_canvas.winfo_width()))
        
        # Enable mousewheel scrolling
        def _on_mousewheel(event):
            control_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            control_canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Data import section
        ttk.Label(control_frame, text="Data Source:").pack(anchor=tk.W, padx=5, pady=5)
        self.btn_import = ttk.Button(control_frame, text="Import CSV", command=self.import_data)
        self.btn_import.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Separator(control_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=5, pady=10)
        
        # Feature selection
        ttk.Label(control_frame, text="Target Feature:").pack(anchor=tk.W, padx=5, pady=5)
        self.target_var = tk.StringVar()
        self.target_select = ttk.Combobox(control_frame, textvariable=self.target_var, state="readonly")
        self.target_select.pack(fill=tk.X, padx=5, pady=5)
        self.target_select.bind("<<ComboboxSelected>>", self.update_feature_list)
        
        ttk.Label(control_frame, text="Date Column:").pack(anchor=tk.W, padx=5, pady=5)
        self.date_var = tk.StringVar()
        self.date_select = ttk.Combobox(control_frame, textvariable=self.date_var, state="readonly")
        self.date_select.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(control_frame, text="Predictor Features:").pack(anchor=tk.W, padx=5, pady=5)
        self.feature_frame = ttk.Frame(control_frame)
        self.feature_frame.pack(fill=tk.X, padx=5, pady=5)
        self.feature_vars = []
        
        ttk.Separator(control_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=5, pady=10)
        
        # Model selection
        ttk.Label(control_frame, text="Prediction Model:").pack(anchor=tk.W, padx=5, pady=5)
        self.model_var = tk.StringVar(value="Linear Regression")
        for model_name in self.models.keys():
            ttk.Radiobutton(control_frame, text=model_name, value=model_name, 
                        variable=self.model_var).pack(anchor=tk.W, padx=20, pady=2)
        
        ttk.Separator(control_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=5, pady=10)
        
        # Anomaly detection
        ttk.Label(control_frame, text="Anomaly Detection:").pack(anchor=tk.W, padx=5, pady=5)
        self.anomaly_var = tk.StringVar(value="None")
        for model_name in self.anomaly_models.keys():
            ttk.Radiobutton(control_frame, text=model_name, value=model_name, 
                        variable=self.anomaly_var).pack(anchor=tk.W, padx=20, pady=2)
        
        ttk.Separator(control_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=5, pady=10)
        
        # Forecast parameters
        ttk.Label(control_frame, text="Forecast Period (days):").pack(anchor=tk.W, padx=5, pady=5)
        self.forecast_days = tk.IntVar(value=30)
        forecast_spin = ttk.Spinbox(control_frame, from_=1, to=365, textvariable=self.forecast_days, width=10)
        forecast_spin.pack(anchor=tk.W, padx=5, pady=5)
        
        # AutoML options
        self.use_automl = tk.BooleanVar(value=False)
        ttk.Checkbutton(control_frame, text="Use AutoML to tune parameters", 
                    variable=self.use_automl).pack(anchor=tk.W, padx=5, pady=5)
        
        # Run prediction button
        self.btn_predict = ttk.Button(control_frame, text="Run Prediction", command=self.run_prediction)
        self.btn_predict.pack(fill=tk.X, padx=5, pady=20)
        self.btn_predict.config(state=tk.DISABLED)
        
        # Right side for visualizations
        viz_frame = ttk.Frame(main_frame)
        viz_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Data summary 
        self.summary_frame = ttk.LabelFrame(viz_frame, text="Data Summary")
        self.summary_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.summary_text = tk.Text(self.summary_frame, height=5, width=50)
        self.summary_text.pack(fill=tk.X, padx=5, pady=5)
        self.summary_text.config(state=tk.DISABLED)
        
        # Matplotlib figure for trend visualization
        self.fig_frame = ttk.LabelFrame(viz_frame, text="Trend Visualization")
        self.fig_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.fig = plt.Figure(figsize=(6, 4), dpi=100)
        self.plot_canvas = FigureCanvasTkAgg(self.fig, self.fig_frame)
        self.plot_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Cleanup function for when tab is closed
        def _on_tab_close():
            control_canvas.unbind_all("<MouseWheel>")
            
        parent.bind("<Destroy>", lambda e: _on_tab_close())
    
    def setup_anomaly_tab(self, parent):
        # Frame for anomaly detection
        anomaly_frame = ttk.Frame(parent)
        anomaly_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left side controls
        control_frame = ttk.LabelFrame(anomaly_frame, text="Anomaly Detection Settings")
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        
        ttk.Label(control_frame, text="Anomaly Threshold:").pack(anchor=tk.W, padx=5, pady=5)
        self.threshold_var = tk.DoubleVar(value=0.05)
        threshold_spin = ttk.Spinbox(control_frame, from_=0.01, to=0.5, increment=0.01, 
                                     textvariable=self.threshold_var, width=10)
        threshold_spin.pack(anchor=tk.W, padx=5, pady=5)
        
        ttk.Label(control_frame, text="Detection Methods:").pack(anchor=tk.W, padx=5, pady=5)
        self.iso_forest_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(control_frame, text="Isolation Forest", 
                       variable=self.iso_forest_var).pack(anchor=tk.W, padx=20, pady=2)
        
        self.lof_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(control_frame, text="Local Outlier Factor", 
                       variable=self.lof_var).pack(anchor=tk.W, padx=20, pady=2)
        
        self.zscore_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(control_frame, text="Z-Score Method", 
                       variable=self.zscore_var).pack(anchor=tk.W, padx=20, pady=2)
        
        self.btn_detect_anomalies = ttk.Button(control_frame, text="Detect Anomalies", 
                                              command=self.detect_anomalies)
        self.btn_detect_anomalies.pack(fill=tk.X, padx=5, pady=20)
        self.btn_detect_anomalies.config(state=tk.DISABLED)
        
        # Right side visualization
        viz_frame = ttk.Frame(anomaly_frame)
        viz_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.anomaly_fig_frame = ttk.LabelFrame(viz_frame, text="Anomaly Visualization")
        self.anomaly_fig_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.anomaly_fig = plt.Figure(figsize=(6, 4), dpi=100)
        self.anomaly_canvas = FigureCanvasTkAgg(self.anomaly_fig, self.anomaly_fig_frame)
        self.anomaly_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def setup_xai_tab(self, parent):
        # Frame for XAI
        xai_frame = ttk.Frame(parent)
        xai_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Controls
        control_frame = ttk.LabelFrame(xai_frame, text="Explainable AI Settings")
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        
        ttk.Label(control_frame, text="Explainability Method:").pack(anchor=tk.W, padx=5, pady=5)
        self.xai_method_var = tk.StringVar(value="SHAP")
        ttk.Radiobutton(control_frame, text="SHAP Values", value="SHAP", 
                       variable=self.xai_method_var).pack(anchor=tk.W, padx=20, pady=2)
        ttk.Radiobutton(control_frame, text="Feature Importance", value="Importance", 
                       variable=self.xai_method_var).pack(anchor=tk.W, padx=20, pady=2)
        
        ttk.Label(control_frame, text="Sample to Explain:").pack(anchor=tk.W, padx=5, pady=5)
        self.explain_var = tk.StringVar(value="Recent")
        ttk.Radiobutton(control_frame, text="Most Recent Period", value="Recent", 
                       variable=self.explain_var).pack(anchor=tk.W, padx=20, pady=2)
        ttk.Radiobutton(control_frame, text="Average Prediction", value="Average", 
                       variable=self.explain_var).pack(anchor=tk.W, padx=20, pady=2)
        
        self.btn_explain = ttk.Button(control_frame, text="Generate Explanation", 
                                     command=self.generate_explanation)
        self.btn_explain.pack(fill=tk.X, padx=5, pady=20)
        self.btn_explain.config(state=tk.DISABLED)
        
        # Visualization
        viz_frame = ttk.Frame(xai_frame)
        viz_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.xai_fig_frame = ttk.LabelFrame(viz_frame, text="Feature Impact Visualization")
        self.xai_fig_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.xai_fig = plt.Figure(figsize=(6, 4), dpi=100)
        self.xai_canvas = FigureCanvasTkAgg(self.xai_fig, self.xai_fig_frame)
        self.xai_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def import_data(self):
        file_path = filedialog.askopenfilename(
            title="Select CSV file",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                self.data = pd.read_csv(file_path)
                
                # Update date column dropdown
                self.date_select['values'] = self.data.columns.tolist()
                for col in self.data.columns:
                    if 'date' in col.lower() or 'time' in col.lower():
                        self.date_var.set(col)
                        break
                
                # Update target selection
                self.target_select['values'] = [c for c in self.data.columns if self.data[c].dtype in ['int64', 'float64']]
                if len(self.target_select['values']) > 0:
                    self.target_select.current(0)
                    self.update_feature_list()
                    self.btn_predict.config(state=tk.NORMAL)
                    self.btn_detect_anomalies.config(state=tk.NORMAL)
                    self.btn_explain.config(state=tk.NORMAL)
                
                # Convert date column if selected
                if self.date_var.get():
                    try:
                        self.data[self.date_var.get()] = pd.to_datetime(self.data[self.date_var.get()])
                        self.data.sort_values(by=self.date_var.get(), inplace=True)
                    except:
                        messagebox.showwarning("Warning", "Could not convert the selected column to datetime format.")
                
                # Show data summary
                self.update_summary()
                
                self.status_var.set(f"Data imported: {len(self.data)} rows, {len(self.data.columns)} columns")
            except Exception as e:
                messagebox.showerror("Import Error", f"Failed to import data: {str(e)}")
                self.status_var.set("Import failed.")
    
    def update_feature_list(self, event=None):
        # Clear existing checkboxes
        for widget in self.feature_frame.winfo_children():
            widget.destroy()
        self.feature_vars = []
        
        # Create new checkboxes for features
        current_target = self.target_var.get()
        for col in self.data.columns:
            if col != current_target and col != self.date_var.get() and self.data[col].dtype in ['int64', 'float64']:
                var = tk.BooleanVar(value=True)
                self.feature_vars.append((col, var))
                ttk.Checkbutton(self.feature_frame, text=col, variable=var).pack(anchor=tk.W)
    
    def update_summary(self):
        if self.data is not None:
            summary_text = f"Dataset Shape: {self.data.shape[0]} rows × {self.data.shape[1]} columns\n\n"
            
            # Add date range if available
            date_col = self.date_var.get()
            if date_col and pd.api.types.is_datetime64_any_dtype(self.data[date_col]):
                start_date = self.data[date_col].min().strftime('%Y-%m-%d')
                end_date = self.data[date_col].max().strftime('%Y-%m-%d')
                summary_text += f"Date Range: {start_date} to {end_date}\n\n"
            
            # Add basic stats for numerical columns
            num_cols = self.data.select_dtypes(include=['int64', 'float64']).columns[:3]  # Limit to first 3
            if len(num_cols) > 0:
                summary_text += "Key Metrics:\n"
                for col in num_cols:
                    summary_text += f"{col}: avg={self.data[col].mean():.2f}, min={self.data[col].min():.2f}, max={self.data[col].max():.2f}\n"
            
            self.summary_text.config(state=tk.NORMAL)
            self.summary_text.delete(1.0, tk.END)
            self.summary_text.insert(tk.END, summary_text)
            self.summary_text.config(state=tk.DISABLED)
    
    def prepare_data_for_models(self):
        if self.data is None:
            messagebox.showwarning("Warning", "Please import data first.")
            return None
        
        target = self.target_var.get()
        selected_features = [col for col, var in self.feature_vars if var.get()]
        
        if not selected_features:
            messagebox.showwarning("Warning", "Please select at least one predictor feature.")
            return None
        
        # Check if date column is selected and valid
        date_col = self.date_var.get()
        if date_col and date_col in self.data.columns:
            self.data[date_col] = pd.to_datetime(self.data[date_col])
            self.data.sort_values(by=date_col, inplace=True)
            
            # Generate some time-based features
            if 'day_of_week' not in self.data.columns:
                self.data['day_of_week'] = self.data[date_col].dt.dayofweek
                self.feature_vars.append(('day_of_week', tk.BooleanVar(value=True)))
                selected_features.append('day_of_week')
            
            if 'month' not in self.data.columns:
                self.data['month'] = self.data[date_col].dt.month
                self.feature_vars.append(('month', tk.BooleanVar(value=True)))
                selected_features.append('month')
            
            dates = self.data[date_col]
            future_dates = pd.date_range(
                start=dates.iloc[-1] + pd.Timedelta(days=1),
                periods=self.forecast_days.get(),
                freq='D'
            )
        else:
            # Use row indices if no date column
            dates = pd.RangeIndex(len(self.data))
            future_dates = pd.RangeIndex(len(self.data), len(self.data) + self.forecast_days.get())
        
        # Prepare X and y
        X = self.data[selected_features]
        y = self.data[target]
        
        return {
            'X': X,
            'y': y,
            'dates': dates,
            'future_dates': future_dates,
            'target': target,
            'features': selected_features
        }
    
    def run_prediction(self):
        data_dict = self.prepare_data_for_models()
        if data_dict is None:
            return
        
        X, y = data_dict['X'], data_dict['y']
        dates = data_dict['dates']
        future_dates = data_dict['future_dates']
        target = data_dict['target']
        selected_features = data_dict['features']
        
        try:
            # Model selection and training
            model_name = self.model_var.get()
            use_automl = self.use_automl.get()
            
            # For storing predictions
            future_pred = None
            model_info = {}
            
            # Update status
            self.status_var.set(f"Training {model_name} model...")
            self.root.update_idletasks()
            
            if model_name == "ARIMA":
                # ARIMA only needs the target variable
                model = ARIMA(y, order=(5,1,0))
                model_fit = model.fit()
                forecast = model_fit.forecast(steps=self.forecast_days.get())
                future_pred = forecast
                model_info['name'] = "ARIMA(5,1,0)"
                
            elif model_name == "LSTM":
                # Prepare data for LSTM
                scaler_X = StandardScaler()
                scaler_y = StandardScaler()
                
                X_scaled = scaler_X.fit_transform(X)
                y_scaled = scaler_y.fit_transform(y.values.reshape(-1, 1))
                
                # Create sequences
                seq_length = 10
                X_seq, y_seq = [], []
                for i in range(len(X_scaled) - seq_length):
                    X_seq.append(X_scaled[i:i+seq_length])
                    y_seq.append(y_scaled[i+seq_length])
                
                X_seq = np.array(X_seq)
                y_seq = np.array(y_seq)
                
                # Build LSTM model
                model = Sequential([
                    LSTM(50, return_sequences=True, input_shape=(seq_length, X.shape[1])),
                    Dropout(0.2),
                    LSTM(50),
                    Dropout(0.2),
                    Dense(1)
                ])
                
                model.compile(optimizer=Adam(0.001), loss='mse')
                
                # Train with early stopping
                early_stop = EarlyStopping(monitor='val_loss', patience=10)
                model.fit(
                    X_seq, y_seq, 
                    epochs=100, 
                    batch_size=32, 
                    validation_split=0.2,
                    callbacks=[early_stop],
                    verbose=0
                )
                
                # Prepare data for prediction
                last_sequence = X_scaled[-seq_length:].reshape(1, seq_length, X.shape[1])
                
                # Generate predictions
                predictions = []
                current_seq = last_sequence.copy()
                
                for _ in range(self.forecast_days.get()):
                    # Get prediction for next step
                    next_pred = model.predict(current_seq, verbose=0)
                    predictions.append(next_pred[0, 0])
                    
                    # Create feature vector for the next time step
                    # For simplicity, we'll just repeat the last features
                    next_features = current_seq[0, -1:].copy()
                    
                    # Update the sequence by removing the first entry and adding prediction
                    current_seq = np.append(current_seq[:, 1:], 
                                           np.expand_dims(next_features, axis=1), 
                                           axis=1)
                
                # Inverse transform to get actual values
                future_pred = scaler_y.inverse_transform(np.array(predictions).reshape(-1, 1)).flatten()
                model_info['name'] = "LSTM (50 units, 2 layers)"
                
            elif model_name == "Hybrid":
                # Implement a simple hybrid model: average of ARIMA and LSTM
                # First, train ARIMA
                arima_model = ARIMA(y, order=(5,1,0))
                arima_fit = arima_model.fit()
                arima_forecast = arima_fit.forecast(steps=self.forecast_days.get())
                
                # Then train LSTM
                scaler_X = StandardScaler()
                scaler_y = StandardScaler()
                
                X_scaled = scaler_X.fit_transform(X)
                y_scaled = scaler_y.fit_transform(y.values.reshape(-1, 1))
                
                # Create sequences
                seq_length = 10
                X_seq, y_seq = [], []
                for i in range(len(X_scaled) - seq_length):
                    X_seq.append(X_scaled[i:i+seq_length])
                    y_seq.append(y_scaled[i+seq_length])
                
                X_seq = np.array(X_seq)
                y_seq = np.array(y_seq)
                
                # Build LSTM model
                lstm_model = Sequential([
                    LSTM(50, return_sequences=True, input_shape=(seq_length, X.shape[1])),
                    Dropout(0.2),
                    LSTM(50),
                    Dropout(0.2),
                    Dense(1)
                ])
                
                lstm_model.compile(optimizer=Adam(0.001), loss='mse')
                lstm_model.fit(X_seq, y_seq, epochs=50, batch_size=32, validation_split=0.2, verbose=0)
                
                # Prepare data for prediction
                last_sequence = X_scaled[-seq_length:].reshape(1, seq_length, X.shape[1])
                
                # Generate predictions
                lstm_predictions = []
                current_seq = last_sequence.copy()
                
                for _ in range(self.forecast_days.get()):
                    next_pred = lstm_model.predict(current_seq, verbose=0)
                    lstm_predictions.append(next_pred[0, 0])
                    
                    next_features = current_seq[0, -1:].copy()
                    current_seq = np.append(current_seq[:, 1:], 
                                           np.expand_dims(next_features, axis=1), 
                                           axis=1)
                
                lstm_forecast = scaler_y.inverse_transform(np.array(lstm_predictions).reshape(-1, 1)).flatten()
                
                # Combine forecasts (simple average)
                future_pred = (arima_forecast + lstm_forecast) / 2
                model_info['name'] = "Hybrid (ARIMA + LSTM)"
                
            elif model_name == "AutoML":
                # AutoML using RandomizedSearchCV
                model = RandomForestRegressor()
                
                # Define parameter space
                param_space = {
                    'n_estimators': [50, 100, 200, 300],
                    'max_depth': [None, 10, 20, 30, 40],
                    'min_samples_split': [2, 5, 10],
                    'min_samples_leaf': [1, 2, 4],
                    'bootstrap': [True, False]
                }
                
                # Setup cross-validation for time series
                tscv = TimeSeriesSplit(n_splits=5)
                
                # Perform randomized search
                random_search = RandomizedSearchCV(
                    model, param_distributions=param_space,
                    n_iter=20, cv=tscv, verbose=0, random_state=42, n_jobs=-1
                )
                
                random_search.fit(X, y)
                
                # Get best model and parameters
                best_model = random_search.best_estimator_
                
                # For simplicity, repeat last row for future prediction
                # In real applications, you'd want to do proper time series feature engineering
                last_features = X.iloc[-1:].values
                future_features = np.repeat(last_features, self.forecast_days.get(), axis=0)
                
                future_pred = best_model.predict(future_features)
                model_info['name'] = f"AutoML RandomForest: {random_search.best_params_}"
                model_info['best_params'] = random_search.best_params_
                
            else:
                # For other models (Linear Regression, Random Forest)
                model = self.models[model_name]
                
                if use_automl and model_name == "Random Forest":
                    # Setup simple parameter tuning if AutoML requested
                    param_space = {
                        'n_estimators': [50, 100, 200],
                        'max_depth': [None, 10, 20, 30],
                        'min_samples_split': [2, 5, 10]
                    }
                    
                    tscv = TimeSeriesSplit(n_splits=3)
                    random_search = RandomizedSearchCV(
                        model, param_distributions=param_space,
                        n_iter=10, cv=tscv, verbose=0, random_state=42, n_jobs=-1
                    )
                    
                    random_search.fit(X, y)
                    model = random_search.best_estimator_
                    model_info['name'] = f"{model_name} with AutoML"
                    model_info['best_params'] = random_search.best_params_
                
                else:
                    # Regular training without AutoML
                    model.fit(X, y)
                    model_info['name'] = model_name
                
                # For simplicity, repeat last row for future prediction
                # In real applications, you'd want to do proper time series feature engineering
                last_features = X.iloc[-1:].values
                future_features = np.repeat(last_features, self.forecast_days.get(), axis=0)
                
                future_pred = model.predict(future_features)
            
            # Store the results for later use
            self.forecast_result = future_pred
            self.model_info = model_info
            self.forecast_dates = future_dates
            
            # Plot the results
            self.plot_forecast(dates, y, future_dates, future_pred, target)
            
            # Update status
            self.status_var.set(f"Prediction complete using {model_info['name']}")
            
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred during prediction: {str(e)}")
            self.status_var.set("Prediction failed.")
    
    def plot_forecast(self, dates, historical_values, future_dates, forecast_values, target_name):
        # Clear previous plot
        self.fig.clear()
        
        # Create plot
        ax = self.fig.add_subplot(111)
        
        # Plot historical data
        if isinstance(dates, pd.DatetimeIndex) or isinstance(dates, pd.Series) and pd.api.types.is_datetime64_any_dtype(dates):
            # If dates are datetime
            # Get the most recent month of data for display
            if len(historical_values) > 30:
                start_idx = len(historical_values) - 30
                display_hist_dates = dates[start_idx:]
                display_hist_values = historical_values[start_idx:]
            else:
                display_hist_dates = dates
                display_hist_values = historical_values
                
            # Plot the data
            ax.plot(display_hist_dates, display_hist_values, 'b-', label='Historical Data')
            ax.plot(future_dates, forecast_values, 'r--', label='Forecast')
            
            # Format x-axis to show days
            from matplotlib.dates import DateFormatter
            date_format = DateFormatter('%m-%d')
            ax.xaxis.set_major_formatter(date_format)
            
            # Ensure reasonable number of tick marks
            plt.xticks(rotation=45)
            ax.set_xlabel('Date (MM-DD)')
        else:
            # If dates are just indices
            if len(historical_values) > 30:
                start_idx = len(historical_values) - 30
                display_range = range(start_idx, len(historical_values))
                display_values = historical_values[start_idx:]
            else:
                display_range = range(len(historical_values))
                display_values = historical_values
                
            ax.plot(display_range, display_values, 'b-', label='Historical Data')
            ax.plot(range(len(historical_values), len(historical_values) + len(forecast_values)), 
                forecast_values, 'r--', label='Forecast')
            ax.set_xlabel('Time Period (Days)')
        
        ax.set_ylabel(target_name)
        ax.set_title(f'{target_name} Forecast (Last Month + {len(forecast_values)} Days)')
        ax.legend()
        
        # Add confidence interval (simplified)
        if isinstance(forecast_values, np.ndarray) and len(forecast_values) > 0:
            std_dev = historical_values.std() * 0.5  # Simplified assumption
            if isinstance(dates, pd.DatetimeIndex) or isinstance(dates, pd.Series) and pd.api.types.is_datetime64_any_dtype(dates):
                ax.fill_between(
                    future_dates,
                    forecast_values - std_dev,
                    forecast_values + std_dev,
                    color='r', alpha=0.2,
                    label='Confidence Interval'
                )
            else:
                ax.fill_between(
                    range(len(historical_values), len(historical_values) + len(forecast_values)),
                    forecast_values - std_dev,
                    forecast_values + std_dev,
                    color='r', alpha=0.2,
                    label='Confidence Interval'
                )
        
        # Adjust layout to make room for dates
        self.fig.tight_layout()
        
        # Redraw canvas
        self.plot_canvas.draw()
    
    def detect_anomalies(self):
        data_dict = self.prepare_data_for_models()
        if data_dict is None:
            return
        
        X, y = data_dict['X'], data_dict['y']
        dates = data_dict['dates']
        target = data_dict['target']
        
        try:
            self.status_var.set("Detecting anomalies...")
            self.root.update_idletasks()
            
            # Clear previous plot
            self.anomaly_fig.clear()
            ax = self.anomaly_fig.add_subplot(111)
            
            # Focus on recent data (last month/30 points)
            if len(y) > 30:
                start_idx = len(y) - 30
                display_slice = slice(start_idx, None)
            else:
                display_slice = slice(None)
            
            # Plot original data
            if isinstance(dates, pd.DatetimeIndex) or isinstance(dates, pd.Series) and pd.api.types.is_datetime64_any_dtype(dates):
                display_dates = dates[display_slice]
                display_y = y[display_slice]
                ax.plot(display_dates, display_y, 'b-', label='Original Data')
                x_values = display_dates
                
                # Format x-axis to show days
                from matplotlib.dates import DateFormatter
                date_format = DateFormatter('%m-%d')
                ax.xaxis.set_major_formatter(date_format)
                plt.xticks(rotation=45)
                ax.set_xlabel('Date (MM-DD)')
            else:
                display_range = range(len(y))[display_slice]
                display_y = y[display_slice]
                ax.plot(display_range, display_y, 'b-', label='Original Data')
                x_values = display_range
                ax.set_xlabel('Time Period (Days)')
            
            # Initialize anomaly detection results for all data
            anomalies = np.zeros(len(y), dtype=bool)
            
            # Apply selected methods
            methods_used = []
            
            if self.iso_forest_var.get():
                # Isolation Forest
                iso_forest = IsolationForest(contamination=self.threshold_var.get(), random_state=42)
                iso_anomalies = iso_forest.fit_predict(X) == -1
                anomalies = anomalies | iso_anomalies
                methods_used.append("Isolation Forest")
            
            if self.lof_var.get():
                # Local Outlier Factor
                lof = LocalOutlierFactor(contamination=self.threshold_var.get(), novelty=False)
                lof_anomalies = lof.fit_predict(X) == -1
                anomalies = anomalies | lof_anomalies
                methods_used.append("LOF")
            
            if self.zscore_var.get():
                # Z-score method
                z_scores = np.abs((y - y.mean()) / y.std())
                z_threshold = 3.0  # Standard 3-sigma rule
                zscore_anomalies = z_scores > z_threshold
                anomalies = anomalies | zscore_anomalies
                methods_used.append("Z-score")
            
            # Get the anomalies for the display range
            display_anomalies = anomalies[display_slice]
            
            # Plot anomalies
            if isinstance(x_values, pd.DatetimeIndex) or isinstance(x_values, pd.Series) and pd.api.types.is_datetime64_any_dtype(x_values):
                ax.scatter(x_values[display_anomalies], display_y[display_anomalies], color='red', label='Anomalies', s=50, zorder=5)
            else:
                ax.scatter(np.array(x_values)[display_anomalies], display_y[display_anomalies], color='red', label='Anomalies', s=50, zorder=5)
            
            ax.set_ylabel(target)
            ax.set_title(f'Anomaly Detection for {target}')
            ax.legend()
            
            # Adjust layout
            self.anomaly_fig.tight_layout()
            
            # Redraw canvas
            self.anomaly_canvas.draw()
            
            # Update status
            anomaly_count = np.sum(anomalies)
            display_anomaly_count = np.sum(display_anomalies)
            self.status_var.set(f"Found {display_anomaly_count} anomalies in view, {anomaly_count} total using {', '.join(methods_used)}")
            
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred during anomaly detection: {str(e)}")
            self.status_var.set("Anomaly detection failed.")
    
    def generate_explanation(self):
        data_dict = self.prepare_data_for_models()
        if data_dict is None:
            return
        
        X, y = data_dict['X'], data_dict['y']
        selected_features = data_dict['features']
        
        try:
            self.status_var.set("Generating explanations...")
            self.root.update_idletasks()
            
            # Train a random forest model for explanation
            # (Using Random Forest even if another model was selected for prediction)
            explainer_model = RandomForestRegressor(n_estimators=100, random_state=42)
            explainer_model.fit(X, y)
            
            # Clear previous plot
            self.xai_fig.clear()
            
            # Choose method
            method = self.xai_method_var.get()
            
            if method == "SHAP":
                # SHAP values explanation
                try:
                    # Create a small subset for SHAP explanation to speed up calculation
                    X_sample = X.iloc[-20:] if len(X) > 20 else X
                    
                    # Create explainer
                    explainer = shap.TreeExplainer(explainer_model)
                    shap_values = explainer.shap_values(X_sample)
                    
                    # Plot
                    ax = self.xai_fig.add_subplot(111)
                    shap.summary_plot(shap_values, X_sample, plot_type="bar", show=False)
                    plt.tight_layout()
                    self.xai_canvas.draw()
                    
                    self.status_var.set("SHAP explanation generated successfully")
                except Exception as shap_error:
                    # Fallback to feature importance if SHAP fails
                    self.status_var.set(f"SHAP analysis failed, falling back to feature importance. Error: {str(shap_error)}")
                    method = "Importance"
            
            if method == "Importance":
                # Feature importance
                ax = self.xai_fig.add_subplot(111)
                
                # Get importance
                importances = explainer_model.feature_importances_
                indices = np.argsort(importances)[::-1]
                
                # Plot feature importances
                ax.barh(range(len(indices)), importances[indices], align='center')
                ax.set_yticks(range(len(indices)))
                ax.set_yticklabels([selected_features[i] for i in indices])
                ax.set_xlabel('Feature Importance')
                ax.set_title('Feature Importance for Prediction')
                
                self.xai_fig.tight_layout()
                self.xai_canvas.draw()
                
                self.status_var.set("Feature importance explanation generated successfully")
            
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred during explanation: {str(e)}")
            self.status_var.set("Explanation generation failed.")

if __name__ == "__main__":
    root = tk.Tk()
    app = BusinessTrendPredictor(root)
    root.mainloop()