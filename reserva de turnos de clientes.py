# app.py
import streamlit as st
import json
import hashlib
from datetime import datetime, timedelta
import pandas as pd
from collections import defaultdict

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Gestión de Turnos", layout="centered")

# --- ESTILOS CSS ---
def load_css():
    st.markdown("""
    <style>
        .stButton>button { width: 100%; border-radius: 8px; }
        h1, h2, h3 { color: #333A40; }
        h1 { color: #4A90E2; text-align: center; }
        h2 { border-bottom: 2px solid #EAF2FB; padding-bottom: 0.75rem; }
    </style>
    """, unsafe_allow_html=True)

load_css()

# --- CONSTANTES Y GESTIÓN DE DATOS ---
DATA_FILE = "data.json"

def load_data():
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
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# --- INICIALIZACIÓN DEL ESTADO DE LA SESIÓN ---
if 'initialized' not in st.session_state:
    st.session_state.initialized = True
    st.session_state.data = load_data()
    st.session_state.role = None
    st.session_state.logged_in = False
    st.session_state.step = 1
    st.session_state.client_data = {}

def reset_client_flow():
    st.session_state.step = 1
    st.session_state.client_data = {}

# --- VISTAS DE LA APLICACIÓN ---

def display_login():
    """Muestra la interfaz de selección de rol y login/registro de admin."""
    st.title("Bienvenido al Sistema de Turnos")
    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Soy Cliente"):
            st.session_state.role = "client"
            reset_client_flow()
            st.rerun()
    with col2:
        if st.button("Soy Administrador"):
            st.session_state.show_admin_login = not st.session_state.get('show_admin_login', False)
    
    if st.session_state.get('show_admin_login', False):
        st.markdown("---")
        if st.session_state.data['admin_creds']:
            with st.form("admin_login_form"):
                st.subheader("Acceso de Administrador")
                email = st.text_input("Email")
                password = st.text_input("Contraseña", type="password")
                submitted = st.form_submit_button("Ingresar")
                if submitted:
                    stored_creds = st.session_state.data['admin_creds']
                    if email == stored_creds['email'] and hash_password(password) == stored_creds['hash']:
                        st.session_state.logged_in = True
                        st.session_state.role = "admin"
                        st.rerun()
                    else:
                        st.error("Email o contraseña incorrectos.")
        else:
            with st.form("admin_register_form"):
                st.subheader("Registro de Administrador (Única Vez)")
                email = st.text_input("Su Email")
                password = st.text_input("Elija una Contraseña", type="password")
                reg_key = st.text_input("Clave de Registro Única", type="password")
                submitted = st.form_submit_button("Registrar y Entrar")
                if submitted:
                    try:
                        ONE_TIME_REGISTRATION_KEY = st.secrets["REG_KEY"]
                    except (FileNotFoundError, KeyError):
                        st.error("La configuración de secretos no está disponible. Contacte al desarrollador.")
                        return

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

def display_client_view():
    """Asistente paso a paso para la reserva de cliente."""
    st.title("Reserva de Turno")
    if st.button("<< Volver al inicio"):
        reset_client_flow()
        st.session_state.role = None
        st.rerun()

    step = st.session_state.get('step', 1)

    if step == 1:
        st.header("Paso 1: Tus Datos y el Trabajo")
        with st.form("step1_form"):
            client_name = st.text_input("Nombre y Apellido", value=st.session_state.client_data.get('name', ''))
            address = st.text_input("Dirección", value=st.session_state.client_data.get('address', ''))
            phone = st.text_input("Teléfono", value=st.session_state.client_data.get('phone', ''))
            
            st.markdown("---")
            costs = st.session_state.data['costs']
            job_options = {f"{job_id}: {details['text']} - ${details['cost']:,}": job_id for job_id, details in costs.items()}
            selected_jobs_display = st.multiselect( "Tipo de Trabajo", options=job_options.keys(), default=[k for k,v in job_options.items() if v in st.session_state.client_data.get('jobs', [])])
            ac_quantity = st.number_input("Cantidad de Aires", min_value=1, value=st.session_state.client_data.get('quantity', 1), step=1)
            
            submitted = st.form_submit_button("Siguiente: Elegir Día")
            if submitted:
                if not all([client_name, address, phone, selected_jobs_display]):
                    st.error("Por favor, complete todos los campos.")
                else:
                    st.session_state.client_data['name'] = client_name
                    st.session_state.client_data['address'] = address
                    st.session_state.client_data['phone'] = phone
                    st.session_state.client_data['jobs'] = [job_options[d] for d in selected_jobs_display]
                    st.session_state.client_data['quantity'] = ac_quantity
                    st.session_state.step = 2
                    st.rerun()
    elif step == 2:
        st.header("Paso 2: Elegí un Día Disponible")
        if st.button("<< Volver a mis datos"):
            st.session_state.step = 1
            st.rerun()
        st.markdown("Los días no disponibles o fines de semana están deshabilitados.")

        slots_booked_per_day = defaultdict(int)
        for appt in st.session_state.data['appointments']:
            slots_booked_per_day[appt['date']] += len(appt['timeSlots'])

        days_to_show = 15; today = datetime.now().date(); available_days = []; d = today
        while len(available_days) < days_to_show:
            if d.weekday() < 5: available_days.append(d)
            d += timedelta(days=1)
        
        cols = st.columns(2); col_idx = 0
        for day in available_days:
            date_str = day.strftime("%Y-%m-%d"); slots_booked = slots_booked_per_day.get(date_str, 0); is_full = slots_booked >= 2
            with cols[col_idx]:
                if st.button(day.strftime("%A, %d de %B"), key=date_str, disabled=is_full):
                    st.session_state.client_data['date'] = date_str; st.session_state.step = 3; st.rerun()
            col_idx = (col_idx + 1) % 2
    elif step == 3:
        selected_date_str = st.session_state.client_data.get('date')
        selected_date = datetime.strptime(selected_date_str, "%Y-%m-%d").date()
        st.header(f"Paso 3: Elegí un Horario para el {selected_date.strftime('%A, %d de %B')}")
        if st.button("<< Cambiar Día"): st.session_state.step = 2; st.rerun()

        all_slots = ["16:00 - 18:00hs", "18:00 - 20:00hs"]
        booked_slots = [slot for appt in st.session_state.data['appointments'] if appt['date'] == selected_date_str for slot in appt['timeSlots']]
        available_slots = [s for s in all_slots if s not in booked_slots]

        selected_slots = st.multiselect("Selecciona uno o más horarios", options=available_slots)
        
        if st.button("Siguiente: Confirmar Turno"):
            if not selected_slots: st.error("Debes seleccionar al menos un horario.")
            else: st.session_state.client_data['timeSlots'] = selected_slots; st.session_state.step = 4; st.rerun()
    elif step == 4:
        st.header("Paso 4: Confirma tu Turno")
        
        data = st.session_state.client_data; costs = st.session_state.data['costs']
        base_duration = sum(costs[job_id]['duration'] for job_id in data['jobs']); total_duration = base_duration * data['quantity']
        total_cost = sum(costs[job_id]['cost'] for job_id in data['jobs']) * data['quantity']; selected_capacity = len(data['timeSlots']) * 2

        st.markdown(f"**Nombre:** {data['name']}")
        st.markdown(f"**Fecha:** {datetime.strptime(data['date'], '%Y-%m-%d').strftime('%A, %d de %B')}")
        st.markdown(f"**Horario(s):** {', '.join(data['timeSlots'])}"); st.markdown(f"**Trabajo:** {', '.join(data['jobs'])} (x{data['quantity']})")
        st.markdown(f"**Duración estimada:** {total_duration}hs"); st.markdown(f"**Costo total estimado:** ${total_cost:,}")
        st.markdown("---")

        if total_duration > selected_capacity:
            st.error(f"¡Atención! La duración del trabajo ({total_duration}hs) es mayor que el espacio en los horarios seleccionados ({selected_capacity}hs). Por favor, vuelve atrás y elige más horarios o ajusta el trabajo.")
            if st.button("<< Volver a elegir horario"): st.session_state.step = 3; st.rerun()
        else:
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Confirmar y Guardar Turno", type="primary"):
                    new_appointment = { "id": int(datetime.now().timestamp()), "status": "pending", "clientName": data['name'], "address": data['address'], "phone": data['phone'], "date": data['date'], "quantity": data['quantity'], "jobs": data['jobs'], "timeSlots": data['timeSlots'], "totalDuration": total_duration }
                    st.session_state.data['appointments'].append(new_appointment); save_data(st.session_state.data)
                    st.success("¡Tu turno ha sido guardado con éxito!"); st.balloons()
                    reset_client_flow(); st.button("Reservar otro turno")
            with col2:
                if st.button("<< Volver a elegir horario"): st.session_state.step = 3; st.rerun()

def display_admin_view():
    """Panel de administración con todas sus funcionalidades."""
    st.set_page_config(layout="wide")
    st.title("Panel de Administración")

    if st.button("Salir"):
        st.session_state.logged_in = False; st.session_state.role = None
        st.set_page_config(layout="centered"); st.rerun()

    tab1, tab2, tab3 = st.tabs(["📊 Turnos Agendados", "⚙️ Gestionar Costos", "⚡ Otras Acciones"])
    
    with tab1:
        st.header("Turnos Agendados")
        st.subheader("Filtro Semanal")
        week_filter = st.date_input("Seleccione una fecha para filtrar", value=None, label_visibility="collapsed")
        
        appts_df = pd.DataFrame(st.session_state.data['appointments'])
        if appts_df.empty:
            st.info("No hay turnos agendados.")
        else:
            appts_df['date'] = pd.to_datetime(appts_df['date'])
            if week_filter:
                start_of_week = week_filter - timedelta(days=week_filter.weekday())
                end_of_week = start_of_week + timedelta(days=6)
                appts_df = appts_df[(appts_df['date'].dt.date >= start_of_week) & (appts_df['date'].dt.date <= end_of_week)]
            appts_df = appts_df.sort_values(by='date')

            for index, appt in appts_df.iterrows():
                with st.container(border=True):
                    col1, col2 = st.columns([2,1])
                    with col1:
                        total_cost = sum(st.session_state.data['costs'][job]['cost'] for job in appt['jobs']) * appt['quantity']
                        st.markdown(f"**Cliente:** {appt['clientName']}")
                        st.markdown(f"**Fecha:** {appt['date'].strftime('%A, %d de %B de %Y')}")
                        st.markdown(f"**Detalle:** {appt['quantity']} x Aires, {', '.join(appt['jobs'])} ({appt['totalDuration']}hs)")
                        st.markdown(f"**Costo Total:** ${total_cost:,.0f}")
                    with col2:
                        statuses = ["pending", "completed", "not_completed"]; current_status_index = statuses.index(appt['status'])
                        new_status = st.selectbox("Estado", statuses, index=current_status_index, key=f"status_{appt['id']}")
                        if new_status != appt['status']:
                            for original_appt in st.session_state.data['appointments']:
                                if original_appt['id'] == appt['id']: original_appt['status'] = new_status; break
                            save_data(st.session_state.data)
                            st.toast(f"Turno de {appt['clientName']} actualizado a {new_status}", icon="✔️"); st.rerun()
    with tab2:
        st.header("Gestionar Costos de Trabajos")
        with st.form("costs_form"):
            new_costs = {}
            for job_id, details in st.session_state.data['costs'].items():
                new_costs[job_id] = st.number_input(f"Costo Trabajo {job_id} ({details['text']})", value=details['cost'], min_value=0)
            if st.form_submit_button("Guardar Cambios"):
                for job_id, cost in new_costs.items(): st.session_state.data['costs'][job_id]['cost'] = cost
                save_data(st.session_state.data); st.success("Costos actualizados correctamente.")
    with tab3:
        st.header("Acción 'Día de Lluvia'")
        st.warning("Reprograma TODOS los turnos pendientes al siguiente día hábil (L-V).")
        if st.button("Activar 'Día de Lluvia'", type="primary"):
            updated_count = 0
            for appt in st.session_state.data['appointments']:
                if appt['status'] == 'pending':
                    current_date = datetime.strptime(appt['date'], '%Y-%m-%d'); next_day = current_date + timedelta(days=1)
                    while next_day.weekday() >= 5: next_day += timedelta(days=1)
                    appt['date'] = next_day.strftime('%Y-%m-%d'); updated_count += 1
            if updated_count > 0: save_data(st.session_state.data); st.success(f"{updated_count} turnos reprogramados.")
            else: st.info("No había turnos pendientes."); st.rerun()

# --- LÓGICA PRINCIPAL ---
if st.session_state.get('role') == "client":
    display_client_view()
elif st.session_state.get('role') == "admin" and st.session_state.get('logged_in'):
    display_admin_view()
else:
    display_login()
