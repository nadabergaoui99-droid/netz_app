
import streamlit as st
import math 
import base64
import pandas as pd
from pathlib import Path
st.set_page_config(page_title="Lastberechnung", page_icon="⚡", layout="wide")
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
  
trafo_leistung= [
    160,
    250,
    400,
    630,
    800,
    1000,
    1250,
    1600,
    2000,
    2500,
]

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
    },
    "Dorfgebiete": {
        "Beschreibung": "Kombination aus Wohnen und landwirtschaftlicher Nutzung.",
        "Typische Verbraucher": "Haushalte, Wärmepumpen, private Ladepunkte, landwirtschaftliche Verbraucher",
        "Charakteristik": "Niedrige Lastdichte, gemischtes Verbrauchsprofil"
    },
    }

typen = ["Haushalt", "Wärmepumpe", "E-Mobilität" , "Gewerbe"]
Einspeiser=["Photovoltaik"]
gebäudeclustering_typen = [
    "Neubau ohne Gas/Wärme",
    "Neubau mit Gas/Wärme",
    "Gebäude älter 10 Jahren"]
 # Leistungen in kW
leistungen = {
        "Haushalt": 10,
        "Wärmepumpe": 4,
        "E-Mobilität": 11,
        "Gewerbe": 25,
    }

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
if "cluster_percentages" not in st.session_state:
    st.session_state.cluster_percentages = {}
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

 st.info(" Dieses Tool ermöglicht eine standardisierte Lastabschätzung für Neubaugebiete.Die Berechnung erfolgt anhand von Gebietstyp, Siedlungsstruktur sowie ausgewählten Verbrauchergruppen und Einspeisern. Ziel ist es, eine fundierte Grundlage für die Netzplanung zu schaffen.")
 st.write()
 st.write()
 st.write()
 st.write()
 st.subheader("Gebietstyp")
 gebietstyp = st.selectbox(
        "Gebietstyp definieren:",
        list(gebietsdaten.keys()),
        index=list(gebietsdaten.keys()).index(st.session_state.gebietstyp),
    )
 st.session_state.gebietstyp = gebietstyp


 st.markdown("####  Gebäudeclustering")
 
# Mehrfachauswahl
 clustering = st.multiselect(
    "Gebäudeclustering auswählen:",
    gebäudeclustering_typen,
    default=st.session_state.get("gebäudeclustering", []),
    key="gebäudeclustering_multiselect_step1",
)

# Prozentwerte speichern
 cluster_percentages = {}

# Für jede Auswahl Prozent eingeben
 for cluster in clustering:
    percentage = st.number_input(
        f"Prozentanteil für '{cluster}'",
        min_value=0,
        max_value=100,
        value=st.session_state.get("cluster_percentages", {}).get(cluster, 0),
        step=1,
    
        key=f"percentage_{cluster}",
    )
    cluster_percentages[cluster] = percentage
    st.session_state.gebäudeclustering = clustering
    st.session_state.cluster_percentages = cluster_percentages
    
 col1, col2 = st.columns([3, 1])
 with col2:
     st.write("")  # spacer
     st.write("")  # spacer
     st.write("")  # spacer
     if st.button("Starten", key="start_btn"):
            st.session_state.step = 2
            st.rerun()

 # chritt 2: Auswahl Bezug und Einspeisung

def step2():   
   
 
    col1, col2 = st.columns(2)

    with col1:

        st.subheader("Bezug")

        selected_bezug = st.pills(
            "Wähle Bezug:",
            options=typen,
            selection_mode="multi",
            default=st.session_state.get(
                "selected_bezug", []
            ),
        )

    with col2:

        st.subheader("Einspeisung")

        selected_einspeisung = st.pills(
            "Wähle Einspeiser:",
            width="content",
            options=Einspeiser,
            selection_mode="multi",
            default=st.session_state.get(
                "selected_einspeisung", []
            ),
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
   st.subheader("Eingaben")
   n_h = 0 
   n_g = 0
   selected_bezug = st.session_state.get("selected_bezug", [])
   selected_einspeisung = st.session_state.get("selected_einspeisung", [])
   ergebnisse = []
# Inputs only for selected types
   if "Haushalt" in selected_bezug:
        st.markdown("**Anzahl der Wohneinheiten**")
        n_h = st.number_input(
            "Wie viele Wohneinheiten sind vorhanden?",
            min_value=0,
            value=st.session_state.get("n_haushalte", 0),
            step=1,
            key="n_h",
            label_visibility="collapsed"
        )
        g_h = gleichzeitigkeitsfaktor("Haushalt", int(n_h))
        ergebnisse.append(("Haushalt", int(n_h), g_h))
        
    # Gewerbe NUR im Mischgebiet
   if st.session_state.gebietstyp == "Mischgebiete":

        st.markdown("**Anzahl der Gewerbeeinheiten**")

        n_g = st.number_input(
            "Wie viele Gewerbeeinheiten sind vorhanden?",
            min_value=0,
            value=st.session_state.get("n_gewerbe", 0),
            step=1,
            key="n_g",
            label_visibility="collapsed"
        )

        g_g = gleichzeitigkeitsfaktor("Gewerbe", int(n_g))
        ergebnisse.append(("Gewerbe", int(n_g), g_g))
   
    
   st.session_state.ergebnisse = ergebnisse
   st.session_state.n_haushalte = n_h
   st.session_state.n_gewerbe = n_g
   col1, spacer, col2 = st.columns([1, 3, 1])
   with col1:
        if st.button("Zurück", key="zurueck_step3"):
            st.session_state.step = 2
            st.rerun()
   with col2:
        if st.button("Weiter", key="weiter_step3"):
            # Skip Step 4 directly to Step 5 if E-mobility isn't selected
            if "E-Mobilität" in selected_bezug:
                st.session_state.step = 4
            else:
                st.session_state.step = 5
            st.rerun()
            st.session_state.selected_bezug = selected_bezug
            st.session_state.selected_einspeisung = selected_einspeisung
            


def step4():
  st.markdown("### E-Fahrzeuge Annahmen")
  siedlungstyp = st.selectbox(
    "Siedlungstyp auswählen:",
    [
        "Innenstadt",
        "Randbereich (Speckgürtel)",
        "Viele Einfamilienhäuser",
        "Pendlergegend",
    ],
    )
  
  # Faktoren festlegen
  if siedlungstyp == "Innenstadt":
      pkw_pro_we = 0.5
      ev_anteil = 0.4
  else:
      pkw_pro_we = 1.4
      ev_anteil = 0.5
  # Anzahl E-Fahrzeuge berechnen
  n_haushalte = st.session_state.get("n_haushalte", 0)
  n_ev_berechnet = int(n_haushalte * pkw_pro_we * ev_anteil)
  st.session_state["n_ev"] = n_ev_berechnet
  # anzeigen
  # Editierbares Feld

  n_ev = st.number_input(
        "Anzahl E-Fahrzeuge",
        min_value=0,
        step=1,
        key="n_ev",
    )

 
  col1, spacer, col2 = st.columns([1, 3, 1])
  with col1:
      if st.button("Zurück", key="zurueck_step4"):
          st.session_state.step = 3
          st.rerun()
  with col2:
      if st.button("Weiter", key="weiter_step4"): 
          st.session_state.step = 5
          st.rerun()

def step5():
    st.markdown("### Gleichzeitigkeitsfaktor und Lastabschätzung")
       # 👉 get Haushalte from step 3
    
    # 1. Gather data from previous steps
    n_h = st.session_state.get("n_haushalte", 0)
    n_g = st.session_state.get("n_gewerbe", 0)
    n_ev = st.session_state.get("n_ev", 0)
    selected_bezug = st.session_state.get("selected_bezug", [])
    cluster_percentages = st.session_state.get("cluster_percentages", {})
    n_wp = 0

    for cluster, percentage in cluster_percentages.items():
        anteil = percentage / 100

        if cluster == "Neubau ohne Gas/Wärme":
            faktor = 1.0
        elif cluster == "Neubau mit Gas/Wärme":
            faktor = 0.5
        elif cluster == "Gebäude älter 10 Jahren":
            faktor = 0.1
        else:
            faktor = 0

        n_wp += n_h * faktor * anteil

    # optional runden
    n_wp = int(n_wp)


    st.session_state.n_wp = n_wp

    display_data = []
    if "Haushalt" in selected_bezug:
        display_data.append(("Haushalt", n_h))
    if "Wärmepumpe" in selected_bezug:
        display_data.append(("Wärmepumpe", n_wp))
    if "Gewerbe" in selected_bezug:
        display_data.append(("Gewerbe", n_g))
    if "E-Mobilität" in selected_bezug:
        display_data.append(("E-Mobilität", n_ev))

    col1, col2, col3 = st.columns([2, 2, 2])
    with col1: st.markdown("**Netzteilnehmertyp**")
    with col2: st.markdown("**Anzahl n**")
    with col3: st.markdown("**g(n)**")
    
    st.divider()

    for typ, n_val in display_data:
        g_val = gleichzeitigkeitsfaktor(typ, n_val)
        col1, col2, col3 = st.columns([2, 2, 2])
        with col1: st.write(typ)
        with col2: st.write(f"{n_val}")
        with col3: st.write(f"{g_val:.4f}")

    col1, spacer, col2 = st.columns([1, 3, 1])
    with col1:
        if st.button("Zurück", key="zurueck_step5"):
            # Fix 4: If E-Mobility wasn't chosen, skip backwards past step 4 directly to step 3
            if "E-Mobilität" in selected_bezug:
                st.session_state.step = 4
            else:
                st.session_state.step = 3
            st.rerun()
    with col2:
        if st.button("Weiter", key="weiter_step5"):
            st.session_state.step = 6
            st.rerun()

def step6():
  st.subheader("Ergebnis der Lastabschätzung")
  p_ges = 0
    
  n_h = st.session_state.get("n_haushalte", 0)
  n_g = st.session_state.get("n_gewerbe", 0)
  n_ev = st.session_state.get("n_ev", 0)
  n_wp = st.session_state.get("n_wp", 0) # Accessible now
  selected_bezug = st.session_state.get("selected_bezug", [])

  werte = {
        "Haushalt": n_h,
        "Wärmepumpe": n_wp,
        "E-Mobilität": n_ev,
        "Gewerbe": n_g,
    }
  leistungen = {
        "Haushalt": 10,
        "Wärmepumpe": 4,
        "E-Mobilität": 11,
        "Gewerbe": 25,
    }

  detailed_results = []
  for typ in selected_bezug:
        n = werte.get(typ, 0)
        if n <= 0:
            continue
        p = leistungen[typ]
        g = gleichzeitigkeitsfaktor(typ, n)
        p_typ = n * p * g
        p_ges += p_typ
        detailed_results.append({"Typ": typ, "Anzahl": n, "Einzel-Leistung (kW)": p, "Gleichzeitigkeit": round(g,4), "Summe (kW)": round(p_typ,2)})
    
  if detailed_results:
        st.table(pd.DataFrame(detailed_results))

  st.success(f"### Gesamtleistung $P_{{ges}}$ = {p_ges:.2f} kW")

  # Trafo automatisch auswählen
  if p_ges <= 160:
      trafo = 160
  elif p_ges <= 250:
      trafo = 250
  elif p_ges <= 400:
      trafo = 400
  elif p_ges <= 630:
      trafo = 630
  elif p_ges <= 800:
      trafo = 800
  elif p_ges <= 1000:
      trafo = 1000
  elif p_ges <= 1250:
      trafo = 1250
  elif p_ges <= 1600:
      trafo = 1600
  elif p_ges <= 2000:
      trafo = 2000
  else:
      trafo = 2500

  st.info(f"🔌 Empfohlene Trafostation: {trafo} kVA")
  col1, spacer, col2 = st.columns([1, 3, 1])
  with col1:
      if st.button("Zurück", key="zurueck_step6"):
          st.session_state.step = 5
          st.rerun()
  with col2:
      if st.button("Neu Starten", key="restart_app_btn"):
          st.session_state.clear()
          st.rerun()
steps = {
    1: step1,
    2: step2,
    3: step3,
    4: step4,
    5: step5,
    6: step6,
   
}
st.divider()
steps[st.session_state.step]()
st.divider()
