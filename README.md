# 🍞 Bakery Order Management System (Costa Rica)

A streamlined, mobile-friendly web application built with Python and Streamlit to manage artisanal bakery orders. Designed specifically for the Costa Rican market, it automates the generation of order summaries, calculates totals in Colones (₡), and facilitates direct communication with customers via WhatsApp.

## 🚀 Key Features

- **Secure Authentication**: Integrated with `streamlit-authenticator` for secure access control.
- **Dynamic Order Generation**: Select from an embedded catalog of bakery products (bollos, empanadas, chiverre, etc.).
- **Smart WhatsApp Integration**: Automatically cleans phone numbers to 8-digit CR format, prepends the `+506` country code, and generates a pre-filled WhatsApp message.
- **Order Scheduling**: Select delivery dates and configurable time windows (Morning/Afternoon).
- **Payment Integration**: Includes SINPE Móvil payment instructions in the final order summary.
- **Automated Logging**:
  - Generates a detailed `.txt` file for every individual order.
  - Appends order metadata to `pedidos_historial.csv` for business analytics.
- **Mobile Optimized UI**: Clean, responsive interface designed for quick use on smartphones.

## 🛠️ Tech Stack

- Language: Python 3.12+
- Framework: Streamlit
- Authentication: streamlit-authenticator
- Data Handling: Pandas (for CSV logging)
- Deployment: Streamlit Cloud / GitHub

## 📂 Project Structure

```
├── app.py                # Main application logic and UI
├── requirements.txt      # Python dependencies for deployment
├── pedidos/              # Directory where individual .txt orders are stored
└── pedidos_historial.csv # Centralized log of all bakery transactions
```

## ⚙️ Installation & Setup

1. Clone the repository:

```bash
git clone https://github.com/your-username/panaderia.git
cd panaderia
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run the application:

```bash
streamlit run app.py
```

## 📝 Configuration Note

The application uses pre-hashed passwords for security. To change credentials, generate a new hash using `stauth.Hasher.hash('your_password')` and update the `my_hashed_password` variable in 

 the secrets.toml file

## 💡 Tips for your GitHub Repository

- Add a `.gitignore`: Ignore `pedidos/` and `pedidos_historial.csv` if you don’t want customer data public.
- License: Add an MIT License or keep it private if this contains sensitive business logic.

