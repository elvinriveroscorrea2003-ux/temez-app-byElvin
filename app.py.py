import streamlit as st
import pandas as pd

# Configuración de la página
st.set_page_config(page_title="Modelo Témez", layout="wide")

st.title("💧 Modelo Hidrológico Témez")
st.write(
    "Calculadora mensual para transformar precipitación (P) y evapotranspiración (ETP) "
    "en escorrentía usando la formulación clásica corregida del modelo Témez."
)

# -------------------------------------------------------------------
# FORMULACIÓN CORRECTA DEL MODELO TÉMEZ
# -------------------------------------------------------------------
def temez(P, ETP, Hmax, C, H0):
    meses = ["Ene", "Feb", "Mar", "Abr", "May", "Jun",
             "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]

    H_prev = H0
    filas = []

    for i in range(12):
        P_t = float(P[i])
        ETP_t = float(ETP[i])

        # Fórmulas oficiales:
        delta = Hmax - H_prev + ETP_t
        P0 = C * (Hmax - H_prev)

        # Escorrentía T
        if P_t <= P0:
            T = 0.0
        else:
            den = P_t + delta - 2 * P0
            T = (P_t - P0)**2 / den if den > 0 else 0.0

        # Balance hídrico
        X = H_prev + P_t - T

        if X <= ETP_t:
            ER = X
            H = 0.0
        else:
            ER = ETP_t
            H = X - ER

        filas.append([meses[i], P_t, ETP_t, P0, delta, T, X, ER, H])

        H_prev = H

    return pd.DataFrame(
        filas,
        columns=["Mes", "P (mm)", "ETP (mm)", "P0 (mm)", "Delta (mm)",
                 "T (Escorrentía, mm)", "X (mm)", "ER (mm)", "H (mm)"]
    )

# -------------------------------------------------------------------
# SECCIÓN 1: CARGA DE DATOS (MANUAL o EXCEL)
# -------------------------------------------------------------------
st.subheader("📥 Ingreso de datos")

modo = st.radio(
    "Elige cómo deseas ingresar los valores:",
    ["Ingreso manual (columna)", "Cargar archivo Excel"]
)

# -------------------------
# OPCIÓN 1: INGRESO MANUAL
# -------------------------
if modo == "Ingreso manual (columna)":

    default_P = """110.96
49.23
15.98
35.10
54.13
85.48
94.60
162.65
218.76
91.22
73.42
63.63"""

    default_ETP = """163.87
128.27
141.93
137.51
118.99
101.85
107.55
123.74
140.47
168.19
179.25
185.38"""

    P_text = st.text_area("Precipitación P (12 valores en columna):", value=default_P, height=260)
    ETP_text = st.text_area("Evapotranspiración ETP (12 valores en columna):", value=default_ETP, height=260)

# -------------------------
# OPCIÓN 2: CARGAR EXCEL
# -------------------------
else:
    archivo = st.file_uploader("Sube un archivo Excel (.xlsx)", type=["xlsx"])

    if archivo:
        try:
            df_excel = pd.read_excel(archivo)

            st.write("📄 **Contenido del archivo:**")
            st.dataframe(df_excel)

            if "P" not in df_excel.columns or "ETP" not in df_excel.columns:
                st.error("El archivo debe tener columnas llamadas **P** y **ETP**.")
                st.stop()

            P_text = "\n".join(df_excel["P"].astype(str))
            ETP_text = "\n".join(df_excel["ETP"].astype(str))

        except Exception as e:
            st.error(f"Error al leer el archivo: {e}")
            st.stop()
    else:
        st.info("Sube un archivo para continuar.")
        st.stop()

# -------------------------------------------------------------------
# PARÁMETROS DEL MODELO
# -------------------------------------------------------------------
st.subheader("⚙️ Parámetros del modelo")

col1, col2, col3 = st.columns(3)
with col1:
    Hmax = st.number_input("Hmax (mm)", value=150.0)
with col2:
    C = st.number_input("Coeficiente C", min_value=0.0, max_value=1.0, value=0.40)
with col3:
    H0 = st.number_input("H inicial (mm)", value=75.0)

# -------------------------------------------------------------------
# CÁLCULO DEL MODELO
# -------------------------------------------------------------------
if st.button("Calcular Modelo Témez"):

    try:
        # Convertir texto o datos del excel a listas numéricas
        P = [float(x) for x in P_text.replace(",", ".").split()]
        ETP = [float(x) for x in ETP_text.replace(",", ".").split()]

        if len(P) != 12 or len(ETP) != 12:
            st.error("❌ Debes ingresar exactamente 12 valores para P y 12 para ETP.")
            st.stop()

        df = temez(P, ETP, Hmax, C, H0)

        st.success("✅ Cálculo realizado correctamente.")

        # Resultados
        st.subheader("📊 Resultados mensuales del modelo Témez")

        columnas_num = ["P (mm)", "ETP (mm)", "P0 (mm)", "Delta (mm)", "T (Escorrentía, mm)",
                        "X (mm)", "ER (mm)", "H (mm)"]

        st.dataframe(df.style.format(subset=columnas_num, formatter="{:.2f}"))

        esc_total = df["T (Escorrentía, mm)"].sum()
        st.subheader(f"🌧️ Escorrentía total anual: **{esc_total:.2f} mm**")

    except Exception as e:
        st.error(f"❌ Error: {e}")