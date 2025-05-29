# Hack with Gujarat Challenge 2025

**Team Name** - CODE4CHANGE
**Team Members** -  Debshata Choudhury
                 -  Niranjan Praveen
                 -  Abhishek Chaubhey
                 -  Vaibhav Jain
**Problem Statement** - Transport & Logistics Optimization for Rural India
**Team Leader Email** - [debshatachoudhury@gmail.com](mailto:debshatachoudhury@gmail.com)

---

## A Brief of the Prototype:

**Interact and Test the models here** – [https://agrilogistics-optimizer.netlify.app](https://agrilogistics-optimizer.netlify.app)

The solution presented by Team CODE4CHANGE aims to revolutionize rural transport logistics through a web application that facilitates **circular logistics** for **truck drivers** while maximizing value for **farmers** and **input dealers**. Built with **Next.js** on the frontend and backed by **Python-based AI models**, our platform addresses critical inefficiencies in agricultural transportation networks in rural India.

Our system optimizes delivery routes, predicts transportation demand, and connects farmers to available truck capacity in real time. It helps reduce empty return loads, minimize delivery delays, and ensure the affordability and sustainability of agricultural logistics. The app is built with scalability and inclusivity at its core — designed to grow from local village-level implementations to regional and national deployments.

---

## Key Features Include:

* **AI-Powered Route Optimization**: Smart algorithms compute optimal delivery routes for minimal fuel usage and time.
* **Real-Time Tracking**: Live updates and route monitoring for logistics managers and drivers.
* **Demand Forecasting**: Predictive models forecast transport needs to reduce delays and spoilage.
* **Farmer-Truck Coordination**: Matches farmers' crop delivery needs with nearby truck drivers to avoid vehicle under-utilization.
* **Circular Logistics System**: Encourages profit-sharing models where truck drivers are incentivized for round trips instead of returning empty.
* **Multi-User Roles**: The app supports:

  * **Farmers** – Post crop delivery requests
  * **Truck Drivers** – Find available loads and optimize returns
  * **Input Dealers** – Request or supply transportation for agri-inputs

---

## Technology Stack:

* **Frontend**: Next.js (React Framework)
* **Backend**: Python (FastAPI/Flask), AI Models (Scikit-learn, TensorFlow)
* **Database**: MongoDB / PostgreSQL (Optional scalable backend integration)
* **Real-Time**: WebSockets / GPS APIs for live tracking
* **Deployment**: Netlify (Frontend), Railway / Render / Heroku (Backend)

---

## Code Execution Instruction:

### How to Run the Full Stack Application

#### 1. Clone the Repository

Open your terminal and run:

```bash
git clone https://github.com/YourUsername/agrilogistics-optimizer.git  
cd agrilogistics-optimizer
```

---

### 2. Install Frontend Dependencies (Next.js)

```bash
cd client
npm install
```

---

### 3. Install Backend Dependencies (Python API)

```bash
cd ../server
pip install -r requirements.txt
```

---

### 4. Start the Application

* **Frontend (Next.js)**

```bash
cd ../client
npm run dev
```

* **Backend (FastAPI/Flask)**

```bash
cd ../server
python app.py
```

---

### 5. Access the Application

Visit `http://localhost:3000` in your web browser to use the platform.

---

## Scalability, Sustainability, and Affordability Plan:

* **Farmer Reach**: Local onboarding drives via FPOs, agri-input dealers, and mobile agents.
* **Scalability**: Modular architecture supports multi-region rollout with region-specific data models.
* **Sustainability**: Monetized through service fees from bulk transporters and data analytics packages.
* **Affordability**: Free for farmers; revenue from B2B logistics insights sustains operations.

---

This project stands out for addressing one of rural India's most overlooked problems using modern AI and web technologies. With its focus on circular logistics, real-time insights, and community-wide impact, this app promises to become a transformative tool in agricultural transportation.

---