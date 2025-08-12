# app.py
import streamlit as st
import json
import hashlib
from datetime import datetime, timedelta
import pandas as pd

# --- CONFIGURACIÓN DE LA PÁGINA Y ESTILOS ---
# (Sin cambios en esta sección)
st.set_page_config(page_title="Gestión de Turnos", layout="wide")

def load_css():
    st.markdown("""<style> ... </style>""", unsafe_allow_html=True) # CSS Omitido por brevedad

load_css()

# --- CONSTANTES Y GESTIÓN DE DATOS ---
DATA_FILE = "data.json"
# <-- CAMBIO: La clave secreta ya no está aquí.

def load_data():
    # (Sin cambios en esta función)
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        default_data = {
            "admin_creds": None,
            "costs": { "A": {"text": "A (2hs)","duration": 2.0,"cost": 190000},"B": {"text": "B (1.5hs)","duration": 1.5,"cost": 87000},"C": {"text": "C (0.5hs)","duration": 0.5,"cost": 55000},"D": {"text": "D (1h)","duration": 1.0,"cost": 76000}},
            "appointments": []
        }
        with open(DATA_FILE, 'w') as f:
            json.dump(default_data, f, indent=2)
        return default_data

def save_data(data):
    # (Sin cambios en esta función)
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def hash_password(password):
    # (Sin cambios en esta función)
    return hashlib.sha256(password.encode()).hexdigest()

# --- INICIALIZACIÓN DEL ESTADO DE LA SESIÓN ---
# (Sin cambios en esta sección)
if 'initialized' not in st.session_state:
    st.session_state.initialized = True
    st.session_state.data = load_data()
    st.session_state.role = None
    st.session_state.logged_in = False
    st.session_state.cal_date = datetime.now()
    st.session_state.selected_date = None

# --- VISTAS DE LA APLICACIÓN ---
def display_login():
    # (La única modificación es dentro del formulario de registro)
    st.title("Bienvenido al Sistema de Turnos")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Soy Cliente"):
            st.session_state.role = "client"
            st.rerun()
    with col2:
        if st.button("Soy Administrador"):
            st.session_state.show_admin_login = not st.session_state.get('show_admin_login', False)
    
    if st.session_state.get('show_admin_login', False):
        st.markdown("---")
        if st.session_state.data['admin_creds']:
            # (Sin cambios en el formulario de login)
            with st.form("admin_login_form"):
                st.subheader("Acceso de Administrador")
                # ...
                submitted = st.form_submit_button("Ingresar")
                # ...
        else:
            # Formulario de Registro (Única Vez)
            with st.form("admin_register_form"):
                st.subheader("Registro de Administrador (Única Vez)")
                email = st.text_input("Su Email")
                password = st.text_input("Elija una Contraseña", type="password")
                reg_key = st.text_input("Clave de Registro Única", type="password")
                submitted = st.form_submit_button("Registrar y Entrar")
                if submitted:
                    # <-- CAMBIO: Leemos la clave desde st.secrets
                    ONE_TIME_REGISTRATION_KEY = st.secrets["REG_KEY"]
                    if reg_key == ONE_TIME_REGISTRATION_KEY:
                        hashed_pass = hash_password(password)
                        st.session_state.data['admin_creds'] = {"email": email, "hash": hashed_pass}
                        save_data(st.session_state.data)
                        st.session_state.logged_in = True
                        st.session_state.role = "admin"
                        st.toast("Administrador registrado con éxito.", icon="✅")
                        st.rerun()
                    else:
                        st.error("Clave de Registro incorrecta.")
    
# ... El resto de las funciones (display_client_view, display_admin_view, etc.) no tienen cambios ...
def display_calendar(): #
    pass              # Omitido por brevedad
def display_client_view(): #
    pass              # Omitido por brevedad
def display_admin_view(): #
    pass              # Omitido por brevedad

# --- LÓGICA PRINCIPAL ---
if st.session_state.role == "client":
    display_client_view()
elif st.session_state.role == "admin" and st.session_state.logged_in:
    display_admin_view()
else:
    display_login()
 # Ignorar la carpeta de configuración de Streamlit que contiene los secretos
.streamlit/secrets.toml   
