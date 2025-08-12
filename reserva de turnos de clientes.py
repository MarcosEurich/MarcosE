# app.py
import streamlit as st
import json
import hashlib
from datetime import datetime, timedelta
import pandas as pd

# --- CONFIGURACIÓN DE LA PÁGINA Y ESTILOS ---
st.set_page_config(page_title="Gestión de Turnos", layout="wide")

# Replicamos los estilos CSS del proyecto original
def load_css():
    st.markdown("""
    <style>
        .stButton>button {
            width: 100%;
            border-radius: 8px;
            padding: 0.8em 0.2em; /* Ajuste para que el texto no se corte */
        }
        .main-container { max-width: 1200px; margin: auto; }
        .card {
            background-color: #FFFFFF;
            border-radius: 12px;
            padding: 2rem;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
            margin-bottom: 1.5rem;
        }
        h1 { color: #4A90E2; }
        h2 { border-bottom: 2px solid #EAF2FB; padding-bottom: 0.75rem; }
        
        /* <-- CAMBIO: Contenedor específico para forzar la cuadrícula del calendario */
        .calendar-grid-container .stHorizontalBlock {
            display: flex;
            flex-wrap: wrap;
            justify-content: space-between;
        }
        .calendar-grid-container .stButton {
            flex-basis: 13%; /* Aproximadamente 1/7 */
            max-width: 13%;
            padding: 2px;
        }

        .day-btn-available { background-color: #d4edda; }
        .day-btn-one-slot { background-color: #fff3cd; }
        .day-btn-full, .day-btn-weekend { 
            background-color: #f8d7da;
            color: #7A8188 !important; /* Asegurar color del texto en fines de semana */
        }
        .day-btn-selected { 
            border: 2px solid #4A90E2 !important;
            background-color: #EAF2FB !important;
        }
        .calendar-legend { display: flex; flex-wrap: wrap; justify-content: center; gap: 1rem; margin-top: 1.5rem; font-size: 0.8rem; }
        .legend-item { display: flex; align-items: center; gap: 0.5rem; }
        .legend-color { width: 15px; height: 15px; border-radius: 4px; }
    </style>
    """, unsafe_allow_html=True)

load_css()

# --- CONSTANTES Y GESTIÓN DE DATOS ---
DATA_FILE = "data.json"
ONE_TIME_REGISTRATION_KEY = "REFRIGERACION_2024"

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
    st.session_state.cal_date = datetime.now()
    st.session_state.selected_date = None

# --- VISTAS DE LA APLICACIÓN ---
def display_login():
    # Esta función no tiene cambios
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


# <-- CAMBIO: Función del calendario completamente reescrita para ser responsiva
def display_calendar():
    """Muestra un calendario interactivo que funciona en móvil y escritorio."""
    st.subheader("3. Seleccione un día disponible")

    col1, col2, col3 = st.columns([1, 2, 1])
    if col1.button("< Mes Anterior"):
        st.session_state.cal_date -= timedelta(days=st.session_state.cal_date.day)
        st.rerun()
    col2.write(f"<p style='text-align:center; font-weight:bold; font-size:1.2rem;'>{st.session_state.cal_date.strftime('%B %Y')}</p>", unsafe_allow_html=True)
    if col3.button("Mes Siguiente >"):
        st.session_state.cal_date += timedelta(days=31)
        st.rerun()

    # Pre-calcular disponibilidad para el mes
    appts_df = pd.DataFrame(st.session_state.data['appointments'])
    slots_per_day = pd.Series(dtype=int)
    if not appts_df.empty:
        appts_df['date_dt'] = pd.to_datetime(appts_df['date'])
        slots_per_day = appts_df.explode('timeSlots').groupby(appts_df['date_dt'].dt.date).size()

    # Abrir contenedor con la clase CSS para forzar la cuadrícula
    st.markdown("<div class='calendar-grid-container'>", unsafe_allow_html=True)
    
    days_of_week = ["L", "M", "X", "J", "V", "S", "D"]
    cols = st.columns(7)
    for i, day_name in enumerate(days_of_week):
        cols[i].write(f"<p style='text-align:center; font-weight:bold;'>{day_name}</p>", unsafe_allow_html=True)

    first_day = st.session_state.cal_date.replace(day=1)
    last_day_of_month = (first_day.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
    
    cols = st.columns(7)
    # Rellenar días en blanco al inicio del mes
    for i in range(first_day.weekday()):
        cols[i].empty()
    
    current_col = first_day.weekday()
    for day_num in range(1, last_day_of_month.day + 1):
        day_date = first_day.replace(day=day_num)
        
        is_weekend = day_date.weekday() >= 5
        slots_booked = slots_per_day.get(day_date.date(), 0)
        is_full = slots_booked >= 2
        is_selected = st.session_state.selected_date and st.session_state.selected_date == day_date.date()
        is_disabled = is_weekend or is_full

        # Aquí no podemos aplicar CSS a los botones directamente
        # En su lugar, el CSS se aplicará a través del contenedor padre
        with cols[current_col]:
            if st.button(f"{day_num}", key=f"day_{day_num}", disabled=is_disabled):
                st.session_state.selected_date = day_date.date()
                st.rerun()
            
            # Placeholder para dar espacio, esto se podría mejorar con CSS más avanzado
            if not is_disabled:
                 st.write("")


        current_col = (current_col + 1) % 7

    st.markdown("</div>", unsafe_allow_html=True) # Cerrar el contenedor

    # Leyenda de colores (los colores no se pueden aplicar a los botones, es una limitación)
    st.markdown("""<p style="font-size: 0.9em; text-align: center; margin-top: 1em;">
    La disponibilidad se indica deshabilitando los días llenos o de fin de semana.</p>""", unsafe_allow_html=True)
    
    
# El resto de las funciones (display_client_view, display_admin_view) no necesitan cambios
def display_client_view():
    st.title("Reserva de Turno")
    col1, col2 = st.columns([1.2, 1])

    with col1:
        with st.container(border=True):
            st.subheader("Datos del Turno")
            with st.form("appointment_form"):
                name = st.text_input("Nombre y Apellido")
                address = st.text_input("Dirección")
                phone = st.text_input("Teléfono")
                st.markdown("---")
                
                st.subheader("1. Tipo de Trabajo")
                costs = st.session_state.data['costs']
                job_options = {f"{job_id}: {details['text']} - ${details['cost']:,}": job_id for job_id, details in costs.items()}
                selected_jobs_display = st.multiselect("Seleccione uno o más trabajos", options=job_options.keys())
                selected_job_ids = [job_options[d] for d in selected_jobs_display]

                st.subheader("2. Cantidad de Aires")
                ac_quantity = st.number_input("Indique la cantidad", min_value=1, value=1, step=1)
                
                st.subheader("4. Horario(s) Disponibles")
                available_time_slots = ["16:00 - 18:00hs", "18:00 - 20:00hs"]
                if st.session_state.selected_date:
                    booked_slots = [
                        slot for appt in st.session_state.data['appointments']
                        if appt['date'] == st.session_state.selected_date.strftime('%Y-%m-%d')
                        for slot in appt['timeSlots']
                    ]
                    available_time_slots = [slot for slot in available_time_slots if slot not in booked_slots]

                selected_time_slots = st.multiselect(
                    "Seleccione los horarios", options=available_time_slots, 
                    disabled=(not st.session_state.selected_date),
                    placeholder= "Seleccione un día del calendario primero" if not st.session_state.selected_date else "Elija un horario"
                )
                if st.session_state.selected_date:
                    st.info(f"Día seleccionado: {st.session_state.selected_date.strftime('%d/%m/%Y')}")

                submitted = st.form_submit_button("Guardar Turno")
                if submitted:
                    base_duration = sum(costs[job_id]['duration'] for job_id in selected_job_ids)
                    total_duration = base_duration * ac_quantity
                    selected_capacity = len(selected_time_slots) * 2
                    
                    if not all([name, address, phone, selected_job_ids, st.session_state.selected_date, selected_time_slots]):
                        st.error("Por favor, complete todos los campos y seleccione fecha y horario.")
                    elif total_duration > selected_capacity:
                        st.error(f"Error: La duración del trabajo ({total_duration}hs) excede la capacidad del horario seleccionado ({selected_capacity}hs).")
                    else:
                        new_appointment = { "id": int(datetime.now().timestamp()), "status": "pending", "clientName": name, "address": address, "phone": phone, "date": st.session_state.selected_date.strftime('%Y-%m-%d'), "quantity": ac_quantity, "jobs": selected_job_ids, "timeSlots": selected_time_slots, "totalDuration": total_duration }
                        st.session_state.data['appointments'].append(new_appointment)
                        save_data(st.session_state.data)
                        st.session_state.selected_date = None
                        st.success("¡Turno guardado con éxito!")
                        st.toast("Recargando calendario...", icon="🔄")
                        st.rerun()

    with col2:
        with st.container(border=True):
            display_calendar()


def display_admin_view():
    st.title("Panel de Administración")
    if st.button("Salir"):
        st.session_state.logged_in = False
        st.session_state.role = None
        st.rerun()

    tab1, tab2, tab3 = st.tabs(["📊 Turnos Agendados", "⚙️ Gestionar Costos", "⚡ Otras Acciones"])
    
    with tab1:
        st.subheader("Filtro Semanal")
        week_filter = st.date_input("Seleccione una fecha para filtrar por esa semana", value=None)

        appts_df = pd.DataFrame(st.session_state.data['appointments'])
        if appts_df.empty:
            st.info("No hay turnos agendados.")
            return

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
                    statuses = ["pending", "completed", "not_completed"]
                    current_status_index = statuses.index(appt['status'])
                    new_status = st.selectbox( "Estado", statuses, index=current_status_index, key=f"status_{appt['id']}")
                    if new_status != appt['status']:
                        for original_appt in st.session_state.data['appointments']:
                            if original_appt['id'] == appt['id']: original_appt['status'] = new_status; break
                        save_data(st.session_state.data)
                        st.toast(f"Turno de {appt['clientName']} actualizado a {new_status}", icon="✔️")
                        st.rerun()

    with tab2:
        st.subheader("Gestionar Costos de Trabajos")
        with st.form("costs_form"):
            new_costs = {}
            for job_id, details in st.session_state.data['costs'].items():
                new_costs[job_id] = st.number_input(f"Costo Trabajo {job_id} ({details['text']})", value=details['cost'], min_value=0)
            if st.form_submit_button("Guardar Cambios"):
                for job_id, cost in new_costs.items(): st.session_state.data['costs'][job_id]['cost'] = cost
                save_data(st.session_state.data)
                st.success("Costos actualizados correctamente.")

    with tab3:
        st.subheader("Acción 'Día de Lluvia'")
        st.warning("Esta acción reprograma TODOS los turnos pendientes al siguiente día hábil (L-V).")
        if st.button("Activar 'Día de Lluvia'", type="primary"):
            updated_count = 0
            for appt in st.session_state.data['appointments']:
                if appt['status'] == 'pending':
                    current_date = datetime.strptime(appt['date'], '%Y-%m-%d')
                    next_day = current_date + timedelta(days=1)
                    while next_day.weekday() >= 5: next_day += timedelta(days=1)
                    appt['date'] = next_day.strftime('%Y-%m-%d')
                    updated_count += 1
            if updated_count > 0:
                save_data(st.session_state.data)
                st.success(f"{updated_count} turnos pendientes han sido reprogramados.")
            else: st.info("No había turnos pendientes para reprogramar.")
            st.rerun()

# --- LÓGICA PRINCIPAL ---
if st.session_state.role == "client":
    display_client_view()
elif st.session_state.role == "admin" and st.session_state.logged_in:
    display_admin_view()
else:
    display_login()
