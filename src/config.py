import os

# --- Paths ---
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DATA_PATH = os.path.join(PROJECT_ROOT, "data", "raw", "om_traders_sales_inventory.csv")
PROCESSED_DATA_PATH = os.path.join(PROJECT_ROOT, "data", "processed", "features.csv")
MODEL_PATH = os.path.join(PROJECT_ROOT, "models", "xgboost_stockout_model.json")

# --- Branches (Om Traders has 3 counters) ---
BRANCHES = ["Main Market", "Station Road", "College Chowk"]

# --- Book catalog: Publisher x Class x Subject ---
PUBLISHERS = ["S Chand", "Oxford", "NCERT", "Navneet", "Full Circle"]
CLASSES = list(range(1, 11))           # Class 1 to Class 10
SUBJECTS = ["Maths", "Science", "English", "Hindi"]

# --- Notebook catalog: type x page count ---
NOTEBOOK_VARIANTS = [
    ("Fair Notebook", 172),
    ("Fair Notebook", 100),
    ("Rough Notebook", 172),
    ("Rough Notebook", 100),
]

# --- Stationery catalog: simple item list ---
STATIONERY_ITEMS = [
    "Pen", "Pencil", "Eraser", "Sharpener", "Geometry Box",
    "Scale", "Glue Stick", "Crayons Box", "Sketch Pens", "Highlighter",
]

# --- Simulation settings ---
N_DAYS = 365
RANDOM_SEED = 42

# --- Business definition ---
STOCKOUT_HORIZON_DAYS = 7