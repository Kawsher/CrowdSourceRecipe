# 🍽️ CrowdSource Recipe

![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-000000?style=flat-square&logo=flask&logoColor=white)
![MongoDB](https://img.shields.io/badge/MongoDB-47A248?style=flat-square&logo=mongodb&logoColor=white)
![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=flat-square&logo=html5&logoColor=white)
![CSS3](https://img.shields.io/badge/CSS3-1572B6?style=flat-square&logo=css3&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=flat-square&logo=javascript&logoColor=black)
![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)

> A **community-driven recipe sharing platform** where users can submit, discover, search, and rate recipes from diverse culinary backgrounds — built as a full-stack web application using Flask and MongoDB.

---

## 📌 Overview

**CrowdSource Recipe** is a web application that aggregates culinary creations from users worldwide. Instead of relying on a single chef or cookbook, this platform leverages the power of **crowdsourcing** to build a diverse, ever-growing collection of dishes across various backgrounds and cooking styles.

This project was developed as a **Capstone Project** at **Kent State University** — Team Sigma.

---

## ✨ Features

- 👤 **User Authentication** — Secure registration, login, and session management
- 📝 **Recipe Submission** — Users can submit their own recipes with ingredients & steps
- 🔍 **Search & Filter** — Find recipes by name, ingredient, or cuisine type
- ⭐ **Ratings & Comments** — Users can rate and comment on recipes
- 📱 **Responsive UI** — Clean, mobile-friendly interface

---

## 🛠️ Tech Stack

| Category | Tools |
|----------|-------|
| Backend | Python, Flask |
| Database | MongoDB |
| Frontend | HTML5, CSS3, JavaScript |
| Templating | Jinja2 (Flask Templates) |
| Auth | Flask session management |
| Version Control | Git |

---

## 📁 Project Structure

```
CrowdSourceRecipe/
│
├── app.py                  # Main Flask application & routes
├── config.py               # App configuration settings
├── requirements.txt        # Python dependencies
├── templates/              # HTML Jinja2 templates
│   ├── index.html          # Home page
│   ├── login.html          # Login page
│   ├── register.html       # Registration page
│   ├── submit_recipe.html  # Recipe submission form
│   └── recipe.html         # Recipe detail page
├── static/                 # CSS, JS, images
│   ├── css/
│   ├── js/
│   └── images/
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites
```bash
pip install flask pymongo
```

### Setup & Run
```bash
# Clone the repo
git clone https://github.com/Kawsher/CrowdSourceRecipe.git
cd CrowdSourceRecipe

# Install dependencies
pip install -r requirements.txt

# Run the Flask app
python app.py
```

Then open 👉 `http://localhost:5000` in your browser.

### MongoDB Setup
Make sure MongoDB is running locally:
```bash
mongod --dbpath /data/db
```

---

## 🔬 My Contributions — Backend Development

As the primary **Backend Developer** on Team Sigma, my key contributions include:

- ⚙️ **Flask Application Architecture** — Designed and built the core `app.py` routing structure
- 🔐 **User Authentication System** — Implemented secure registration, login, and session handling
- 🗄️ **MongoDB Integration** — Designed the database schema and built all CRUD operations for recipes and users
- 🔍 **Search & Filter API** — Built the backend search logic for filtering recipes by name and ingredients
- ⭐ **Ratings & Comments Backend** — Developed the API endpoints for submitting and retrieving user ratings and comments
- 🔗 **Frontend-Backend Integration** — Connected Jinja2 templates with Flask routes and MongoDB data

---

## 👥 Team

**Team Sigma** — Kent State University Capstone Project

| Role | Contribution |
|------|-------------|
| Backend Developer | Flask routes, MongoDB, Auth, APIs |
| Frontend Developer | HTML/CSS/JS templates & UI design |
| Database Designer | Schema design & data modeling |
| Project Manager | Planning, documentation & final report |

---

## 📄 Documentation

- 📋 Final Report: `Final Report - Team Sigma.docx`
- 📊 Presentation: `Master_Capstone_Final_PPT.pdf`

---

## 🤝 Connect With Me

<p>
  <a href="https://www.linkedin.com/in/bharathi-d-72b78a1bb/">
    <img src="https://img.shields.io/badge/LinkedIn-Connect-0077B5?style=for-the-badge&logo=linkedin"/>
  </a>
  <a href="mailto:bharathidonku@gmail.com">
    <img src="https://img.shields.io/badge/Gmail-Say%20Hello-D14836?style=for-the-badge&logo=gmail&logoColor=white"/>
  </a>
  <a href="https://github.com/BharathiDonku7">
    <img src="https://img.shields.io/badge/GitHub-Follow-181717?style=for-the-badge&logo=github&logoColor=white"/>
  </a>
</p>

---

<p align="center"><i>"Building AI that's not just powerful, but trustworthy."</i></p>
