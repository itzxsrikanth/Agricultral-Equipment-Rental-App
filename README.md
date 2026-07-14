# AgriRent 🌾
> A Premium, Modern Agricultural Equipment Rental Platform

AgriRent is a professional Flask web application designed for hackathons. It bridges the gap between machinery owners (lenders) and farmers (renters), enabling them to rent out or request agricultural equipment like tractors, combine harvesters, irrigation systems, and soil cultivators.

---

## 🎨 Design Theme & Aesthetics

To reflect modern agriculture and sustainability, the application uses a custom-curated color palette:
* **Primary (Green)**: `#2E7D32`
* **Secondary (Light Green)**: `#81C784`
* **Accent (Orange)**: `#FF9800`
* **Background**: `#F8F9FA`
* **Text**: `#212121`

It uses the modern Google Fonts **Outfit** (headings) and **Inter** (body), and incorporates dynamic elements such as glassmorphism, responsive column grids, custom scrollbars, and interactive micro-animations.

---

## 🌾 Core Technology Stack

* **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5, Bootstrap Icons
* **Backend**: Python, Flask (with Blueprints structure)
* **Database**: SQLite (configured for local instance folders)
* **ORM**: SQLAlchemy
* **Authentication**: Flask-Login + Werkzeug Password Hashing

---

## 🚀 Key Features

- **Dynamic Homepage**: High-quality visual cards, interactive stats, step-by-step how-it-works overview, and dynamic FAQs.
- **Machinery Catalog**: Comprehensive equipment listing with sidebar filters (category, region, search queries).
- **Detail View**: Clear technical specification sheets and rental price calculators.
- **Automatic Seeding**: Seeds 3 sample users and 5 high-quality farm equipment listings automatically on initial database generation.

---

## 🛠️ Installation & Setup

Follow these simple steps to run AgriRent locally on your machine:

### 1. Prerequisite
Ensure you have **Python 3.8+** installed on your system.

### 2. Navigate to project root
```bash
cd AgriculturalRentalSystem
```

### 3. Create and activate a virtual environment
* **Windows**:
  ```powershell
  python -m venv venv
  .\venv\Scripts\activate
  ```
* **macOS/Linux**:
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```

### 4. Install dependencies
```bash
pip install -r requirements.txt
```

### 5. Launch the application
```bash
python app.py
```

The server will start on: **`http://127.0.0.1:5000`**

---

## 🔑 Sample Test Credentials

During initial startup, the database is auto-seeded with the following credentials (all passwords are `password`):

| Role    | Email | Name |
| ------- | ----- | ---- |
| **Owner** | `owner@agrirent.com` | Harpreet Singh |
| **Farmer** | `farmer@agrirent.com` | Rajesh Kumar |
| **Admin** | `admin@agrirent.com` | AgriRent System Admin |
