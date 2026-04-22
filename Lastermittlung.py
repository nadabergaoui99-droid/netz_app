
import streamlit as st
import math 
import base64
import pandas as pd
from pathlib import Path
st.set_page_config(
    page_title="Lastberechnung",
    page_icon="⚡",
)
st.set_page_config(layout="wide")
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
    "Mischgebiete": {
        "Beschreibung": "Kombination aus Wohnen und kleinteiligem Gewerbe.",
        "Typische Verbraucher": "Haushalte, Wärmepumpen, private Ladepunkte, kleinere Gewerbelasten",
        "Charakteristik": "Mittlere Lastdichte, gemischtes Verbrauchsprofil"
    },
    "Allgemeine Wohngebiete": {
        "Beschreibung": "Überwiegend Wohnnutzung mit Ein- und Mehrfamilienhäusern.",
        "Typische Verbraucher": "Haushalte, Wärmepumpen, private Ladepunkte",
        "Charakteristik": "Hoher Wohnanteil, eher gleichmäßige Laststruktur"
    },
    "Gewerbegebiete": {
        "Beschreibung": "Schwerpunkt auf gewerblicher Nutzung.",
        "Typische Verbraucher": "Gewerbe, öffentliche Ladeinfrastruktur, Bandlasten",
        "Charakteristik": "Höhere Lastdichte, stärkere Tagesabhängigkeit"
    }
}
typen = ["Haushalt", "Wärmepumpe", "E-Mobilität" , "Gewerbe"]
Einspeiser=["Photovoltaik"]
gebäudeclustering_typen = [
    "Neubau ohne Gas/Wärme",
    "Neubau mit Gas/Wärme",
    "Gebäud älter 10 Jahren"]

st.divider()
# Session State initialisieren
if "step" not in st.session_state:
    st.session_state.step = 1
if "selected" not in st.session_state:
    st.session_state.selected = []
if "gebietstyp" not in st.session_state:
    st.session_state.gebietstyp = list(gebietsdaten.keys())[0]
if "gebäudeclustering" not in st.session_state:
    st.session_state.gebäudeclustering = gebäudeclustering_typen[0]

st.markdown(
    """
    <style>
    /* Expander header */
    div[data-testid="stExpander"] summary {
        background-color: #e8f0ff;
        border-radius: 10px;
        padding: 6px;
        font-weight: 600;
    }

    /* Expander body */
    div[data-testid="stExpander"] > div {
        background-color: #f7f9fc;
        border-radius: 10px;
        padding: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True
)


def step1():
 
    st.subheader("1. Eigenschaften des Gebietstyps")
    gebietstyp = st.selectbox(
        "Gebietstyp auswählen:",
        list(gebietsdaten.keys()),
        index=list(gebietsdaten.keys()).index(st.session_state.gebietstyp),
    )
    st.session_state.gebietstyp = gebietstyp
    
    

    col1, col2 = st.columns([3, 1])

    with col2:
     st.write("")  # spacer
     st.write("")  # spacer
     st.write("")  # spacer
     if st.button("Starten"):
        st.session_state.step = 2
        st.rerun()

def step2():   
    
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Bezug")
        selected_bezug = st.multiselect(
            label="Wähle Bezug:",
            options=typen,
            default=st.session_state.get("selected_bezug", []),
            key="bezug_select",
            placeholder="Tippen zum Hinzufügen..."
        )

    with col2:
        st.subheader("Einspeisung")
        selected_einspeisung = st.multiselect(
            label="Wähle Einspeiser:",
            options=Einspeiser,
            default=st.session_state.get("selected_einspeisung", []),
            key="einspeisung_select",
            placeholder="Tippen zum Hinzufügen..."
        )

    col1, spacer, col2 = st.columns([1, 3, 1])
    with col1:
        if st.button("Zurück", key="zurueck_step2"):
            st.session_state.step = 1
            st.rerun()
    with col2:
        if st.button("Weiter", key="weiter_step2"):
            
        # 👉 VALIDIERUNG
         if not selected_bezug and not selected_einspeisung:
            st.error("⚠️ Bitte wähle mindestens einen Bezug oder Einspeiser aus.")
         else:
            st.session_state.selected_bezug = selected_bezug
            st.session_state.selected_einspeisung = selected_einspeisung

            st.session_state.step = 3
            st.rerun()
def step3():
    st.text("Eingaben")
    n_h = 0 

    selected_bezug = st.session_state.get("selected_bezug", [])
    selected_einspeisung = st.session_state.get("selected_einspeisung", [])
    ergebnisse = []
# Inputs only for selected types
    if "Haushalt" in selected_bezug:
        st.markdown("**Anzahl der Wohneinheiten**")
        n_h = st.number_input(
            "Wie viele Wohneinheiten sind vorhanden?",
            min_value=0,
            step=1,
            key="n_h",
            label_visibility="collapsed"
        )
        g_h = gleichzeitigkeitsfaktor("Haushalt", int(n_h))
        ergebnisse.append(("Haushalt", int(n_h), g_h))
        # 👉 Wärmepumpe
    
   
    
    st.session_state.ergebnisse = ergebnisse
    st.session_state.n_haushalte = n_h
    col1, spacer, col2 = st.columns([1, 3, 1])
    with col1:
        if st.button("Zurück", key="zurueck_step2"):
            st.session_state.step = 2
            st.rerun()
    with col2:
        if st.button("Weiter", key="weiter_step2"):
            st.session_state.selected_bezug = selected_bezug
            st.session_state.selected_einspeisung = selected_einspeisung
            st.session_state.step = 4
            st.rerun()


def step4():
    st.markdown("####  Gebäudeclustering")
    clustering = st.selectbox(
        "Gebäudeclustering auswählen:",
        gebäudeclustering_typen,
        index=gebäudeclustering_typen.index(st.session_state.gebäudeclustering),
        key="gebäudeclustering_selectbox_step4",
    )

    st.session_state.gebäudeclustering = clustering
   
    col1, spacer, col2 = st.columns([1, 3, 1])
    with col1:
        if st.button("Zurück", key="zurueck_step2"):
            st.session_state.step = 3
            st.rerun()
    with col2:
        if st.button("Weiter", key="weiter_step2"):
            
            st.session_state.step = 5
            st.rerun()

def step5():
    st.markdown("### Gleichzeitigkeitsfaktor und Lastabschätzung")
       # 👉 get Haushalte from step 3
    
    # 1. Gather data from previous steps
    n_h = st.session_state.get("n_haushalte", 0)
    clustering = st.session_state.get("gebäudeclustering", "")
    selected_bezug = st.session_state.get("selected_bezug", [])
    selected_einspeisung = st.session_state.get("selected_einspeisung", [])
    
    if n_h <= 0:
        n_wp = 0
    elif clustering == "Neubau ohne Gas/Wärme":
        n_wp = n_h
    elif clustering == "Neubau mit Gas/Wärme":
        n_wp = int(0.5 * n_h)
    elif clustering == "Gebäude älter 10 Jahren":
        n_wp = int(0.1 * n_h)

    else:
        n_wp = 0



    # Combine all active types into one list for the display loop
    display_data = []
    
    if "Haushalt" in selected_bezug:
        display_data.append(("Haushalt", n_h))
    if "Wärmepumpe" in selected_bezug:
        display_data.append(("Wärmepumpe", n_wp))
    if "Wärmepumpe" in selected_bezug:
        display_data.append(("Wärmepumpe", n_wp))

    # 3. Header Row 
    col1, col2, col3 = st.columns([2, 2, 2])
    with col1: st.markdown("**Netzteilnehmertyp**")
    with col2: st.markdown("**Anzahl n**")
    with col3: st.markdown("**g(n)**")
    
    st.divider()

    # 4. Data Rows 
    for typ, n_val in display_data:
        g_val = gleichzeitigkeitsfaktor(typ, n_val)
        
        col1, col2, col3 = st.columns([2, 2, 2])
        with col1:
            st.write(typ)
        with col2:
            # Instead of number_input, we just show the value from previous steps
            st.write(f"{n_val}")
        with col3:
            st.write(f"{g_val:.4f}") # Formatted to 4 decimal places

    # 5. Navigation
    st.write("")


    col1, spacer, col2 = st.columns([1, 3, 1])
    with col1:
        if st.button("Zurück", key="zurueck_step2"):
            st.session_state.step = 3
            st.rerun()
    with col2:
        if st.button("Weiter", key="weiter_step2"):
            
            st.session_state.step = 5
            st.rerun()

steps = {
    1: step1,
    2: step2,
    3: step3,
    4: step4,
    5: step5,
   
}
steps[st.session_state.step]()
st.divider()
