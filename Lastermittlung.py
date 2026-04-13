
import streamlit as st
import math 
import base64
import pandas as pd
from pathlib import Path
st.set_page_config(
    page_title="Lastberechnung",
    page_icon="⚡",
)
def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = base64.b64encode(f.read()).decode()
    return data
img = get_base64_of_bin_file('images/badenova_background.jpg')
st.markdown(f"""
<style>
    .stApp {{
        background-image: url(data:image/jpg;base64,{img});
        background-size: cover;
    }}
</style>
""", unsafe_allow_html=True)
st.markdown("""
<style>
    .block-container {
        max-width: 950px;
        padding-top: 3rem;
        padding-bottom: 3rem;
        padding-left: 3rem;
        padding-right: 3rem;
    }
    h1, h2, h3 {
        margin-bottom: 0.3rem;
    }
    .stCaption {
        margin-bottom: 1rem;
    }
    .stButton > button {
        border-radius: 12px;
        min-height: 42px;
    }
    div[data-baseweb="select"] > div {
        border-radius: 12px;
        min-height: 44px;
    }
    details {
        border-radius: 14px;
        background: rgba(255,255,255,0.72);
        padding: 0.4rem 0.7rem;
    }
</style>
""", unsafe_allow_html=True)
def gleichzeitigkeitsfaktor(typ, n):
    if n <= 0:
        return 0.0
    if typ == "Haushalt":
        g_inf = 0.07
        g = g_inf + (1 - g_inf) * (n ** -0.75)
    elif typ == "Wärmepumpe":
        g = 1.05 * (n ** -0.03)
    elif typ == "E-Mobilität":
        
        g_inf = 0.1081
        a = 1.4343
        b = -0.5203
        if n == 1:
            g = 1.0
        else:
            g = g_inf + (1 - g_inf) * a * ((n - 1) ** b)
    elif typ == "Photovoltaik":
        g = 1.0
    elif typ == "Nachtspeicherheizung":
        g_inf = 0.7
        a = -0.5
        g = g_inf + (1 - g_inf) * (n ** a)
    elif typ == "Gewerbe":
        g_inf = 0.7
        a = -0.5
        g = g_inf + (1 - g_inf) * (n ** a)
    elif typ == "Straßenbeleuchtung":
        g_inf = 0.7
        a = -0.5
        g = g_inf + (1 - g_inf) * (n ** a)

    else:
        g = 1.0
    return g 
  

gebietsdaten = {
    "Mischgebiet": {
        "Beschreibung": "Kombination aus Wohnen und kleinteiligem Gewerbe.",
        "Typische Verbraucher": "Haushalte, Wärmepumpen, private Ladepunkte, kleinere Gewerbelasten",
        "Charakteristik": "Mittlere Lastdichte, gemischtes Verbrauchsprofil"
    },
    "Vorstädtisches Gebiet": {
        "Beschreibung": "Überwiegend Wohnnutzung mit Ein- und Mehrfamilienhäusern.",
        "Typische Verbraucher": "Haushalte, Wärmepumpen, private Ladepunkte",
        "Charakteristik": "Hoher Wohnanteil, eher gleichmäßige Laststruktur"
    },
    "Gewerbegebiet": {
        "Beschreibung": "Schwerpunkt auf gewerblicher Nutzung.",
        "Typische Verbraucher": "Gewerbe, öffentliche Ladeinfrastruktur, Bandlasten",
        "Charakteristik": "Höhere Lastdichte, stärkere Tagesabhängigkeit"
    }
}
typen = ["Haushalt", "Wärmepumpe", "E-Mobilität", "Photovoltaik", "Nachtspeicherheizung", "Gewerbe"]
gebäudeclustering_typen = [
    "Neubau ohne Gas/Wärme",
    "Neubau mit Gas/Wärme",
    "Gebäude älter 10 Jahren",
    "Ländlicher Bereich",
    "Speckgürtel"]

st.divider()
# Session State initialisieren
if "step" not in st.session_state:
    st.session_state.step = 1
if "selected" not in st.session_state:
    st.session_state.selected = []
if "gebietstyp" not in st.session_state:
    st.session_state.gebietstyp = list(gebietsdaten.keys())[0]
if "gebaeudeclustering" not in st.session_state:
    st.session_state.gebaeudeclustering = gebäudeclustering_typen[0]
st.subheader("Lastabschätzung von Neubaugebieten ")

def step1():
    st.subheader("1. Eigenschaften des Gebietstyps")
    gebietstyp = st.selectbox(
        "Gebietstyp auswählen:",
        list(gebietsdaten.keys()),
        index=list(gebietsdaten.keys()).index(st.session_state.gebietstyp),
    )
    st.session_state.gebietstyp = gebietstyp
    with st.expander("ℹ️ Eigenschaften anzeigen", expanded=False):
        st.write(f"**Beschreibung:** {gebietsdaten[gebietstyp]['Beschreibung']}")
        st.write(f"**Typische Verbraucher:** {gebietsdaten[gebietstyp]['Typische Verbraucher']}")
        st.write(f"**Charakteristik:** {gebietsdaten[gebietstyp]['Charakteristik']}")
    if st.button("Weiter zu Netzteilnehmertypen"):
        st.session_state.step = 2
        st.rerun()
 
def step2():   
    # The multiselect
    selected = st.multiselect(
        label="Wähle oder tippe neue Arten:",
        options=typen,
        accept_new_options=True,
        placeholder="Tippen zum Hinzufügen..."
    )
    col1, spacer, col2 = st.columns([1, 3, 1])
    with col1:
        if st.button("Zurück", key="zurueck_step2"):
            st.session_state.step = 1
            st.rerun()
    with col2:
        if st.button("Weiter", key="weiter_step2"):
            st.session_state.selected = selected
            st.session_state.step = 3
            st.rerun()
def step3():
    st.text("Eingaben")
    selected = st.session_state.get("selected", [])
    ergebnisse = []
# Inputs only for selected types
    if "Haushalt" in selected:
        st.markdown("**Anzahl der Haushalte**")
        n_h = st.number_input(
            "Wie viele Haushalte sind vorhanden?",
            min_value=0,
            step=1,
            key="n_h",
            label_visibility="collapsed"
        )
        g_h = gleichzeitigkeitsfaktor("Haushalt", int(n_h))
        ergebnisse.append(("Haushalt", int(n_h), g_h))
    if "Gewerbe" in selected:
        st.markdown("**Anzahl der Gewerbeeinheiten**")
        n_g = st.number_input(
            "Wie viele Gewerbeeinheiten sind vorhanden?",
            min_value=0,
            step=1,
            key="n_g",
            label_visibility="collapsed"
        )
        g_g = gleichzeitigkeitsfaktor("Gewerbe", int(n_g))
        ergebnisse.append(("Gewerbe", int(n_g), g_g))
    if "Wärmepumpe" in selected:
        st.markdown("**Anzahl der Wärmepumpen**")
        n_wp = st.number_input(
            "Wie viele Wärmepumpen sind vorhanden?",
            min_value=0,
            step=1,
            key="n_wp",
            label_visibility="collapsed"
        )
        g_wp = gleichzeitigkeitsfaktor("Wärmepumpe", int(n_wp))
        ergebnisse.append(("Wärmepumpe", int(n_wp), g_wp))
    if "E-Mobilität" in selected:
        st.markdown("**Anzahl der Ladepunkte / E-Mobilität**")
        n_em = st.number_input(
            "Wie viele E-Mobilitäts-Einheiten sind vorhanden?",
            min_value=0,
            step=1,
            key="n_em",
            label_visibility="collapsed"
        )
        g_em = gleichzeitigkeitsfaktor("E-Mobilität", int(n_em))
        ergebnisse.append(("E-Mobilität", int(n_em), g_em))
    if "Photovoltaik" in selected:
        st.markdown("**Anzahl der Photovoltaik-Anlagen**")
        n_pv = st.number_input(
            "Wie viele Photovoltaik-Anlagen sind vorhanden?",
            min_value=0,
            step=1,
            key="n_pv",
            label_visibility="collapsed"
        )
        g_pv = gleichzeitigkeitsfaktor("Photovoltaik", int(n_pv))
        ergebnisse.append(("Photovoltaik", int(n_pv), g_pv))
    if "Nachtspeicherheizung" in selected:
        st.markdown("**Anzahl der Nachtspeicherheizungen**")
        n_ns = st.number_input(
            "Wie viele Nachtspeicherheizungen sind vorhanden?",
            min_value=0,
            step=1,
            key="n_ns",
            label_visibility="collapsed"
        )
        g_ns = gleichzeitigkeitsfaktor("Nachtspeicherheizung", int(n_ns))
        ergebnisse.append(("Nachtspeicherheizung", int(n_ns), g_ns))
    st.session_state.ergebnisse = ergebnisse
    if ergebnisse:
        df_chart = pd.DataFrame(
            ergebnisse,
            columns=["Netzteilnehmertyp", "Anzahl n", "Gleichzeitigkeitsfaktor"]
        )
        st.subheader("Visualisierung der Gleichzeitigkeitsfaktoren")
        st.bar_chart(
                df_chart,
                x="Netzteilnehmertyp",
                y="Gleichzeitigkeitsfaktor"
            )
        st.subheader("Ergebnistabelle")
       
        with st.expander("📊 Eingaben anzeigen", expanded=True):
            st.dataframe(df_chart, use_container_width=True)
    col1, spacer, col2 = st.columns([1, 3, 1])
    with col1:
        if st.button("Zurück", key="zurueck_step2"):
            st.session_state.step = 2
            st.rerun()
    with col2:
        if st.button("Weiter", key="weiter_step2"):
            st.session_state.selected = selected
            st.session_state.step = 4
            st.rerun()

def step4():
    st.markdown("####  Gebäudeclustering")
    clustering = st.selectbox(
        "Gebäudeclustering auswählen:",
        gebäudeclustering_typen,
        index=gebäudeclustering_typen.index(st.session_state.gebaeudeclustering),
        key="gebaeudeclustering_selectbox_step4",
    )
    st.session_state.gebaeudeclustering = clustering
        
    if st.button("Zurück"):
        st.session_state.step = 3
        st.rerun()
steps = {
    1: step1,
    2: step2,
    3: step3,
    4: step4,
   
}
steps[st.session_state.step] ()
st.divider()
