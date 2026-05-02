import os
from datetime import date

import pandas as pd
import plotly.express as px
import streamlit as st


CSV_FILE = "runs.csv"

COLUMNS = [
    "Fecha",
    "Tipo Run",
    "Km",
    "Tiempo",
    "HR prom",
    "HR Max",
    "Pace",
    "Cadence",
    "Esfuerzo",
    "Notas",
]


def load_data():
    if os.path.exists(CSV_FILE):
        return pd.read_csv(CSV_FILE)
    return pd.DataFrame(columns=COLUMNS)

def save_run(new_run):
    df = load_data()
    df = pd.concat([df, pd.DataFrame([new_run])], ignore_index=True)
    df.to_csv(CSV_FILE, index=False)

def delete_last_run():
    df = load_data()
    if not df.empty:
        df = df.iloc[:-1]
        df.to_csv(CSV_FILE, index=False)

def time_to_seconds(time_text):
    try:
        parts = str(time_text).split(":")
        if len(parts) == 3:
            hours, minutes, seconds = map(int, parts)
            return hours * 3600 + minutes * 60 + seconds
        if len(parts) == 2:
            minutes, seconds = map(int, parts)
            return minutes * 60 + seconds
        return None
    except Exception:
        return None


def seconds_to_pace(seconds_per_km):
    if seconds_per_km is None or seconds_per_km <= 0:
        return ""
    minutes = int(seconds_per_km // 60)
    seconds = int(round(seconds_per_km % 60))
    return f"{minutes:02d}:{seconds:02d}"

def pace_to_seconds(pace_text):
    try:
        parts = str(pace_text).split(":")
        if len(parts) == 2:
            minutes, seconds = map(int, parts)
            return minutes * 60 + seconds
        return None
    except Exception:
        return None


st.set_page_config(page_title="Running Analysis", page_icon="🏃", layout="wide")

st.markdown(
    """
    <style>
    .main-title {
        font-size: 46px;
        font-weight: 800;
        margin-bottom: 0px;
        color: #1f2937;
    }

    .subtitle {
        font-size: 18px;
        color: #6b7280;
        margin-top: 0px;
        margin-bottom: 30px;
    }

    .title-line {
        width: 100%;
        height: 1px;
        background: linear-gradient(to right, #ef4444, #e5e7eb);
        margin-top: 4px;
        margin-bottom: 28px;
    }
    ...
    </style>

    <div class="main-title">Running Analysis</div>
    <div class="subtitle">Tu dashboard personal para registrar, analizar y mejorar tus runs.</div>
    <div class="title-line"></div>
    """,
    unsafe_allow_html=True,
)

df = load_data()

tab1, tab2, tab3 = st.tabs(["Registrar run", "Historial", "Dashboard"])

with tab1:
    st.subheader("Nuevo run")

    with st.form("run_form"):
        col1, col2, col3 = st.columns(3)

        with col1:
            fecha = st.date_input("Fecha", value=date.today())
            tipo_run = st.selectbox(
                "Tipo Run",
                ["Easy", "Long", "Tempo", "Intervals", "Recovery", "Race", "Other"],
            )
            km = st.number_input("Km", min_value=0.0, step=0.1, format="%.2f")

        with col2:
            tiempo = st.text_input("Tiempo", placeholder="Ejemplo: 0:51:40")
            hr_prom = st.number_input("HR prom", min_value=0, step=1)
            hr_max = st.number_input("HR Max", min_value=0, step=1)

        with col3:
            cadence = st.number_input("Cadence", min_value=0, step=1)
            esfuerzo = st.number_input("Esfuerzo", min_value=0, step=1)
            notas = st.text_area("Notas", placeholder="Ejemplo: buen run, sin molestias")

        submitted = st.form_submit_button("Guardar run")

        if submitted:
            total_seconds = time_to_seconds(tiempo)

            if km <= 0:
                st.error("El campo Km debe ser mayor a 0.")
            elif total_seconds is None:
                st.error("El tiempo debe estar en formato HH:MM:SS o MM:SS.")
            else:
                pace_seconds = total_seconds / km
                pace = seconds_to_pace(pace_seconds)

                new_run = {
                    "Fecha": fecha.strftime("%d/%m/%y"),
                    "Tipo Run": tipo_run,
                    "Km": km,
                    "Tiempo": tiempo,
                    "HR prom": hr_prom,
                    "HR Max": hr_max,
                    "Pace": pace,
                    "Cadence": cadence,
                    "Esfuerzo": esfuerzo,
                    "Notas": notas,
                }

                save_run(new_run)
                st.success(f"Run guardado correctamente. Pace calculado: {pace} min/km")
                st.rerun()

with tab2:
    st.subheader("Historial de runs")

    df = load_data()

    if df.empty:
        st.info("Todavía no hay runs registrados.")
    else:
        st.dataframe(df, use_container_width=True)

        st.warning("Si registraste un run por error, puedes eliminar el último registro guardado.")

        if st.button("Eliminar último run"):
            delete_last_run()
            st.success("Último run eliminado correctamente.")
            st.rerun()

        csv_download = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Descargar CSV",
            data=csv_download,
            file_name="runs.csv",
            mime="text/csv",
        )

with tab3:
    st.markdown("## Running Coach Dashboard")
    st.caption("Analiza tu volumen, eficiencia aeróbica, pace y carga de entrenamiento.")

    df = load_data()

    if df.empty:
        st.info("Todavía no hay datos para mostrar gráficos.")
    else:
        df_chart = df.copy()

        df_chart["Fecha_dt"] = pd.to_datetime(
            df_chart["Fecha"], format="%d/%m/%y", errors="coerce"
        )
        df_chart["Km"] = pd.to_numeric(df_chart["Km"], errors="coerce")
        df_chart["HR prom"] = pd.to_numeric(df_chart["HR prom"], errors="coerce")
        df_chart["Esfuerzo"] = pd.to_numeric(df_chart["Esfuerzo"], errors="coerce")
        df_chart["Pace_seconds"] = df_chart["Pace"].apply(pace_to_seconds)
        df_chart["Pace_min_km"] = df_chart["Pace_seconds"] / 60
        tipo_options = sorted(df_chart["Tipo Run"].dropna().unique().tolist())
        selected_tipos = st.multiselect(
            "Filtrar por tipo de run",
            options=tipo_options,
            default=tipo_options,
        )

        df_filtered = df_chart[df_chart["Tipo Run"].isin(selected_tipos)]

        if df_filtered.empty:
            st.warning("No hay datos para los filtros seleccionados.")
            st.stop()

        col1, col2, col3, col4, col5 = st.columns(5)

        total_km = df_filtered["Km"].sum()
        total_runs = len(df_filtered)
        avg_hr = df_filtered["HR prom"].mean()
        total_esfuerzo = df_filtered["Esfuerzo"].sum()
        avg_pace_seconds = df_filtered["Pace_seconds"].mean()
        avg_pace = seconds_to_pace(avg_pace_seconds)
        longest_run = df_filtered["Km"].max()
        fastest_pace_seconds = df_filtered["Pace_seconds"].min()
        fastest_pace = seconds_to_pace(fastest_pace_seconds)

        df_weekly_temp = (
            df_filtered
            .dropna(subset=["Fecha_dt"])
            .set_index("Fecha_dt")
            .resample("W")["Km"]
            .sum()
            .reset_index()
        )

        best_week_km = df_weekly_temp["Km"].max() if not df_weekly_temp.empty else 0

        col1.metric("Km acumulados", f"{total_km:.1f}")
        col2.metric("Total runs", total_runs)
        col3.metric("Pace prom", f"{avg_pace} /km")
        col4.metric("HR prom", f"{avg_hr:.0f}")
        col5.metric("Esfuerzo", f"{total_esfuerzo:.0f}")

        st.markdown(
            f"""
            <div class="section-card">
                <h3 style="margin-top: 0;">Resumen del periodo</h3>
                <p style="font-size: 17px; color: #374151;">
                    Has registrado <b>{total_runs}</b> runs, acumulando <b>{total_km:.1f} km</b>,
                    con un pace promedio de <b>{avg_pace}/km</b> y HR promedio de <b>{avg_hr:.0f} bpm</b>.
                </p>
                <ul style="font-size: 16px; color: #374151; line-height: 1.8;">
                    <li>Run más largo: <b>{longest_run:.1f} km</b></li>
                    <li>Pace más rápido: <b>{fastest_pace}/km</b></li>
                    <li>Semana con mayor volumen: <b>{best_week_km:.1f} km</b></li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.divider()

        fig_km = px.bar(
            df_filtered,
            x="Fecha_dt",
            y="Km",
            color="Tipo Run",
            title="Distancia por run",
            labels={"Fecha_dt": "Fecha", "Km": "Kilómetros"},
        )
        st.plotly_chart(fig_km, use_container_width=True)
        df_weekly = (
            df_filtered
            .dropna(subset=["Fecha_dt"])
            .set_index("Fecha_dt")
            .resample("W")["Km"]
            .sum()
            .reset_index()
        )

        fig_weekly = px.bar(
            df_weekly,
            x="Fecha_dt",
            y="Km",
            title="Volumen semanal",
            labels={"Fecha_dt": "Semana", "Km": "Kilómetros"},
        )
        st.plotly_chart(fig_weekly, use_container_width=True)

        fig_pace = px.line(
            df_filtered,
            x="Fecha_dt",
            y="Pace_min_km",
            markers=True,
            color="Tipo Run",
            title="Evolución de pace",
            labels={"Fecha_dt": "Fecha", "Pace_min_km": "Pace min/km"},
        )
        fig_pace.update_yaxes(autorange="reversed")
        st.plotly_chart(fig_pace, use_container_width=True)

        fig_hr = px.line(
            df_filtered,
            x="Fecha_dt",
            y="HR prom",
            markers=True,
            title="Evolución de HR promedio",
            labels={"Fecha_dt": "Fecha", "HR prom": "HR promedio"},
        )
        st.plotly_chart(fig_hr, use_container_width=True)
        fig_pace_hr = px.scatter(
            df_filtered,
            x="HR prom",
            y="Pace_min_km",
            size="Km",
            color="Tipo Run",
            hover_data=["Fecha", "Km", "Pace", "Esfuerzo"],
            title="Pace vs HR promedio",
            labels={
                "HR prom": "HR promedio",
                "Pace_min_km": "Pace min/km",
                "Km": "Kilómetros",
            },
        )
        fig_pace_hr.update_yaxes(autorange="reversed")
        st.plotly_chart(fig_pace_hr, use_container_width=True)

        fig_effort = px.bar(
            df_filtered,
            x="Fecha_dt",
            y="Esfuerzo",
            color="Tipo Run",
            title="Esfuerzo por run",
            labels={"Fecha_dt": "Fecha", "Esfuerzo": "Esfuerzo"},
        )
        st.plotly_chart(fig_effort, use_container_width=True)