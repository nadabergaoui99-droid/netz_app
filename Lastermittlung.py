import streamlit as st
import math 
import base64
import pandas as pd

# 1. PAGE CONFIG
st.set_page_config(page_title="Lastberechnung", page_icon="⚡", layout="wide")

# 2. BRANDING & GLASS-MORPHISM DESIGN (CSS)
try:
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
            background-attachment: fixed;
        }}
    </style>
    """, unsafe_allow_html=True)
except FileNotFoundError:
    pass

# Styling für die Inhaltsbox, Expander und Tabellen
st.markdown("""
<style>
    /* Hauptcontainer elegant vom Hintergrund abheben */
    .block-container {
        background-color: rgba(255, 255, 255, 0.94);
        padding: 30px 50px !important;
        border-radius: 16px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
        margin-top: 30px;
        margin-bottom: 30px;
    }
    /* Expander modernisieren */
    div[data-testid="stExpander"] summary {
        background-color: #e8f0ff;
        border-radius: 8px;
        padding: 8px;
        font-weight: 600;
        color: #004B93;
    }
    div[data-testid="stExpander"] > div {
        background-color: #f8fafc;
        border-radius: 8px;
        padding: 15px;
    }
</style>
""", unsafe_allow_html=True)


# 3. 
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
    elif typ in ["Nachtspeicherheizung", "Gewerbe", "Straßenbeleuchtung"]:
        g_inf = 0.7
        a = -0.5
        g = g_inf + (1 - g_inf) * (n ** a)
    else:
        g = 1.0
    return min(g, 1.0) # Gleichzeitigkeit kann theoretisch mathematisch > 1 steigen bei WP und n=1, hier gedeckelt.
  
trafo_leistung = [160, 250, 400, 630, 800, 1000, 1250, 1600, 2000, 2500]

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

typen = ["Haushalt", "Wärmepumpe", "E-Mobilität", "Gewerbe"]
Einspeiser = ["Photovoltaik"]
gebäudeclustering_typen = [
    "Neubau ohne Gas/Wärme",
    "Neubau mit Gas/Wärme",
    "Gebäude älter 10 Jahren"
]

leistungen = {
    "Haushalt": 10,
    "Wärmepumpe": 4, 
    "E-Mobilität": 11,
    "Gewerbe": 25,
}


# 4. INITIALISIERUNG SESSION STATE
if "step" not in st.session_state:
    st.session_state.step = 1
if "gebietstyp" not in st.session_state:
    st.session_state.gebietstyp = list(gebietsdaten.keys())[0]
if "gebäudeclustering" not in st.session_state:
    st.session_state.gebäudeclustering = []
if "cluster_percentages" not in st.session_state:
    st.session_state.cluster_percentages = {}
if "selected_bezug" not in st.session_state:
    st.session_state.selected_bezug = []
if "selected_einspeisung" not in st.session_state:
    st.session_state.selected_einspeisung = []
if "n_haushalte" not in st.session_state:
    st.session_state.n_haushalte = 0
if "n_gewerbe" not in st.session_state:
    st.session_state.n_gewerbe = 0
if "n_ev" not in st.session_state:
    st.session_state.n_ev = 0


# 5. VISUELLER SCHRITT-ANZEIGER (WIZARD STEPPER)

def render_progress_bar(current_step):
    steps_titles = [
        "1. Gebiet & Cluster", 
        "2. Infrastruktur", 
        "3. Einheiten", 
        "4. E-Mobilität", 
        "5. Gleichzeitigkeit", 
        "6. Ergebnis"
    ]
    progress_val = current_step / len(steps_titles)
    st.progress(progress_val)
    
    # Textuelle Anzeige der Schritte nebeneinander
    cols = st.columns(len(steps_titles))
    for idx, title in enumerate(steps_titles):
        with cols[idx]:
            if idx + 1 == current_step:
                st.markdown(f"**🔵 {title}**")
            elif idx + 1 < current_step:
                st.markdown(f"🟢 <span style='color:gray;'>{title}</span>", unsafe_allow_html=True)
            else:
                st.markdown(f"<span style='color:lightgray;'>{title}</span>", unsafe_allow_html=True)
    st.write("---")


# 6. DIE EINZELNEN SCHRITTE (WIZARD FUNKTIONEN)

def step1():
    st.info("💡 **Willkommen beim Netzplanungstool:** Dieses Tool ermöglicht eine standardisierte Lastabschätzung für Neubaugebiete anhand mathematischer Gleichzeitigkeitsfaktoren.")
    
    col_left, col_right = st.columns([1, 1], gap="large")
    
    with col_left:
        st.subheader("📍 Gebietstyp")
        gebietstyp = st.selectbox(
            "Wähle den primären Gebietstyp:",
            list(gebietsdaten.keys()),
            index=list(gebietsdaten.keys()).index(st.session_state.gebietstyp),
        )
        st.session_state.gebietstyp = gebietstyp
        
        # Zeige Details zum Gebietstyp an
        st.caption(f"**Beschreibung:** {gebietsdaten[gebietstyp]['Beschreibung']}")
        st.caption(f"**Typische Verbraucher:** {gebietsdaten[gebietstyp]['Typische Verbraucher']}")

        
    with col_right:
        st.subheader("🏢 Gebäudeclustering")
        clustering = st.multiselect(
            "Gebäudetypen im Gebiet bestimmen:",
            gebäudeclustering_typen,
            default=st.session_state.gebäudeclustering,
        )

        cluster_percentages = {}
        total_pct = 0
        validation_passed = True # Initialisiert für die Validierung
        
        
        if clustering:
            st.markdown("**Prozentuale Aufteilung:**")
            cols_pct = st.columns(len(clustering))
            for idx, cluster in enumerate(clustering):
                with cols_pct[idx]:
                    percentage = st.number_input(
                        f"{cluster} (%)",
                        min_value=0,
                        max_value=100,
                        value=st.session_state.cluster_percentages.get(cluster, 0),
                        step=5,
                        key=f"pct_{cluster}",
                    )
                    cluster_percentages[cluster] = percentage
                    total_pct += percentage
            
            if total_pct > 100:
                st.error(f"❌ Die Summe der Anteile beträgt **{total_pct}%**. Ein Wert über 100% ist unzulässig. Bitte korrigiere die Eingaben.")
                validation_passed = False
            elif total_pct != 100:
                st.warning(f"⚠️ Die aktuelle Summe beträgt **{total_pct}%**. Für exakte Berechnungen wird eine Summe von genau 100% empfohlen.")
            
            if validation_passed:
                st.session_state.gebäudeclustering = clustering
                st.session_state.cluster_percentages = cluster_percentages
        else:
            st.error("❌ Bitte wähle mindestens ein **Gebäudeclustering** aus, um fortzufahren.")
            validation_passed = False
        
    col_back, spacer, col_next = st.columns([1, 4, 1])
    with col_next:
        # Button reagiert nun auf den Validierungs-Status
        if st.button("Weiter →", key="start_btn", type="primary", use_container_width=True):
            if not validation_passed:
                st.sidebar.error("🛑 Blockiert: Bitte korrigiere die Eingaben (z.B. Summe der Prozentwerte max. 100%).")
            else:
                st.session_state.step = 2
                st.rerun()


def step2():   
    st.subheader("🔌 Infrastruktur")
    st.write("Wähle aus, welche Einspeisungen und Verbraucher für die Dimensionierung der Trafostation berücksichtigt werden müssen.")
    
    col1, col2 = st.columns(2, gap="large")
    with col1:
        st.markdown("### Bezug")
        selected_bezug = st.pills(
            "Verfügbare Bezugsarten:",
            options=typen,
            selection_mode="multi",
            default=st.session_state.selected_bezug,
        )
    with col2:
        st.markdown("### Einspeisung")
        selected_einspeisung = st.pills(
            "Verfügbare Einspeisearten:",
            options=Einspeiser,
            selection_mode="multi",
            default=st.session_state.selected_einspeisung,
        )

    st.write("")
    col_back, spacer, col_next = st.columns([1, 4, 1])
    with col_back:
        if st.button("← Zurück", key="zurueck_step2", use_container_width=True):
            st.session_state.step = 1
            st.rerun()
    with col_next:
        if st.button("Weiter →", key="weiter_step2", type="primary", use_container_width=True):
            if not selected_bezug and not selected_einspeisung:
                st.error("⚠️ Bitte wähle mindestens einen Netzteilnehmer aus.")
            else:
                st.session_state.selected_bezug = selected_bezug
                st.session_state.selected_einspeisung = selected_einspeisung
                st.session_state.step = 3
                st.rerun()


def step3():
    st.subheader("🔢 Netzteilnehmer")
    selected_bezug = st.session_state.selected_bezug
    
    col1, col2 = st.columns(2, gap="large")
    
    with col1:
        if "Haushalt" in selected_bezug:
            st.markdown("### 🏠 Wohneinheiten")
            n_h = st.number_input(
                "Anzahl aller geplanten Wohneinheiten (WE):",
                min_value=0,
                value=st.session_state.n_haushalte,
                step=1,
                key="input_n_h"
            )
    
            st.session_state.n_haushalte = n_h
        else:
            st.info("ℹ️ Haushalte wurden im vorherigen Schritt nicht ausgewählt.")
            st.session_state.n_haushalte = 0
            
    with col2:
        if "Gewerbe" in selected_bezug:
            st.markdown("### 🏢 Gewerbeeinheiten")
            if st.session_state.gebietstyp in ["Mischgebiete", "Gewerbegebiete"]:
                n_g = st.number_input(
                    "Anzahl der Gewerbeeinheiten:",
                    min_value=0,
                    value=st.session_state.n_gewerbe,
                    step=1,
                    key="input_n_g"
                )
                st.session_state.n_gewerbe = n_g
            else:
                st.warning(
                    f"⚠️ Gewerbe-Inputs sind laut Ihren Einstellungen nur für 'Mischgebiete' und 'Gewerbegebiet' aktiv. "
                    f"Aktueller Typ: **{st.session_state.gebietstyp}**."
                )
                st.session_state.n_gewerbe = 0
        else:
            st.info("ℹ️ Gewerbe wurden im vorherigen Schritt nicht ausgewählt.")
            st.session_state.n_gewerbe = 0

    st.write("")
    col_back, spacer, col_next = st.columns([1, 4, 1])
    with col_back:
        if st.button("← Zurück", key="zurueck_step3", use_container_width=True):
            st.session_state.step = 2
            st.rerun()
    with col_next:
        if st.button("Weiter →", key="weiter_step3", type="primary", use_container_width=True):
            if "E-Mobilität" in selected_bezug:
                st.session_state.step = 4
            else:
                st.session_state.step = 5
            st.rerun()
def update_ev_value():
    """Berechnet den Standardwert für Ladepunkte basierend auf Struktur live neu."""
    if "input_siedlungstyp" not in st.session_state or "n_haushalte" not in st.session_state:
        return
        
    siedlung = st.session_state.input_siedlungstyp
    n_haushalte = st.session_state.n_haushalte
    
    if siedlung == "Innenstadt":
        pkw_pro_we = 0.5
        ev_anteil = 0.4
    else:
        pkw_pro_we = 1.4
        ev_anteil = 0.5
        
    st.session_state.input_n_ev = int(n_haushalte * pkw_pro_we * ev_anteil) 
def step4():
    st.subheader("🚗 E-Mobilitätsdurchdringung")
    
    col_left, col_right = st.columns(2, gap="large")
    
    with col_left:
        # Wir fügen 'key' und 'on_change' hinzu. 
        # Sobald der User hier tippt/wählt, feuert die Funktion oben ab.
        siedlungstyp = st.selectbox(
            "Siedlungsstruktur wählen (berechnet Richtwerte):",
            ["Innenstadt", "Randbereich (Speckgürtel)", "Viele Einfamilienhäuser", "Pendlergegend"],
            key="input_siedlungstyp",
            on_change=update_ev_value
        )
    
    # Sicherstellen, dass beim ersten Laden der Seite überhaupt ein berechneter Wert da ist
    if "input_n_ev" not in st.session_state or st.session_state.input_n_ev == 0:
        update_ev_value()
    
    with col_right:
        # Der 'value'-Parameter wird hier weggelassen, weil Streamlit den Wert 
        # nun exklusiv über die Verknüpfung mit dem 'key' aus dem Session State zieht.
        n_ev = st.number_input(
            "Festgelegte Anzahl E-Fahrzeuge / Ladepunkte:",
            min_value=0,
            step=1,
            key="input_n_ev",
            help="Der Standardwert basiert auf dem gewählten Siedlungstyp, kann aber manuell überschrieben werden."
        )
   
    st.session_state.n_ev = n_ev
 
    st.write("")
    col_back, spacer, col_next = st.columns([1, 4, 1])
    with col_back:
        if st.button("← Zurück", key="zurueck_step4", use_container_width=True):
            st.session_state.step = 3
            st.rerun()
    with col_next:
        if st.button("Weiter →", key="weiter_step4", type="primary", use_container_width=True): 
            st.session_state.step = 5
            st.rerun()


def step5():
    st.subheader("📊 Berechnete Gleichzeitigkeitsfaktoren g(n)")
    
    n_h = st.session_state.n_haushalte if "Haushalt" in st.session_state.selected_bezug else 0
    n_g = st.session_state.n_gewerbe if "Gewerbe" in st.session_state.selected_bezug else 0
    n_ev = st.session_state.n_ev if "E-Mobilität" in st.session_state.selected_bezug else 0
   
    selected_bezug = st.session_state.selected_bezug
    cluster_percentages = st.session_state.cluster_percentages
    
    # Wärmepumpen-Clustering auswerten
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

    n_wp = int(n_wp)
    st.session_state.n_wp = n_wp

    display_data = []
    if "Haushalt" in selected_bezug and n_h > 0:
        display_data.append(("Haushalt", n_h, gleichzeitigkeitsfaktor("Haushalt", n_h)))
    if "Wärmepumpe" in selected_bezug and n_wp > 0:
        display_data.append(("Wärmepumpe", n_wp, gleichzeitigkeitsfaktor("Wärmepumpe", n_wp)))
    if "Gewerbe" in selected_bezug and st.session_state.gebietstyp in ("Mischgebiete", "Gewerbegebiete") and n_g > 0:
        display_data.append(("Gewerbe", n_g, gleichzeitigkeitsfaktor("Gewerbe", n_g)))
    if "E-Mobilität" in selected_bezug and n_ev > 0:
        display_data.append(("E-Mobilität", n_ev, gleichzeitigkeitsfaktor("E-Mobilität", n_ev)))

    if display_data:
        # Repräsentative Tabelle für Faktoren erstellen
        df_factors = pd.DataFrame(display_data, columns=["Netzteilnehmertyp", "Anzahl (n)", "Gleichzeitigkeitsfaktor g(n)"])
        df_factors["Gleichzeitigkeitsfaktor g(n)"] = df_factors["Gleichzeitigkeitsfaktor g(n)"].map(lambda x: f"{x:.4f}")
        st.dataframe(df_factors, use_container_width=True, hide_index=True)
    else:
        st.warning("⚠️ Keine aktiven Verbraucher mit einer Anzahl größer als 0 für die Faktoren-Berechnung vorhanden.")

    st.write("")
    col_back, spacer, col_next = st.columns([1, 4, 1])
    with col_back:
        if st.button("← Zurück", key="zurueck_step5", use_container_width=True):
            if "E-Mobilität" in selected_bezug:
                st.session_state.step = 4
            else:
                st.session_state.step = 3
            st.rerun()
    with col_next:
        if st.button("Ergebnis berechnen 🎉", key="weiter_step5", type="primary", use_container_width=True):
            st.session_state.step = 6
            st.rerun()


def step6():
    st.subheader("🏁 Ergebnis der Lastabschätzung")
    p_ges = 0
    
    n_h = st.session_state.n_haushalte
    n_g = st.session_state.n_gewerbe
    n_ev = st.session_state.n_ev
    n_wp = st.session_state.get("n_wp", 0)
    selected_bezug = st.session_state.selected_bezug

    werte = {
        "Haushalt": n_h,
        "Wärmepumpe": n_wp,
        "E-Mobilität": n_ev,
        "Gewerbe": n_g if st.session_state.gebietstyp in ("Mischgebiete", "Gewerbegebiete") else 0,
    }

    detailed_results = []
    for typ in selected_bezug:
        n = werte.get(typ, 0)
        if n <= 0:
            continue
        p = leistungen.get(typ, 0)
        g = gleichzeitigkeitsfaktor(typ, n)
        p_typ = n * p * g
        p_ges += p_typ
        detailed_results.append({
            "Typ": typ, 
            "Anzahl (n)": n, 
            "Einzel-Leistung (kW)": p, 
            "Gleichzeitigkeit g(n)": round(g, 4), 
            "Summenleistung (kW)": round(p_typ, 2)
        })
    
    # Ab hier lag der Fehler – diese Zeilen müssen eingerückt bleiben!
    if detailed_results:
        st.dataframe(pd.DataFrame(detailed_results), use_container_width=True, hide_index=True)

    # Option 1: Einzelner Trafo
    trafo_single = 2500
    for t in trafo_leistung:
        if p_ges <= t:
            trafo_single = t
            break

    # Option 2: Zwei Trafos (Last geteilt durch 2)
    p_halbe = p_ges / 2
    trafo_half_size = 2500
    for t in trafo_leistung:
        if p_halbe <= t:
            trafo_half_size = t
            break

    st.write("")
    st.metric(label="Errechnete Gesamtleistung P_ges", value=f"{p_ges:.2f} kW")
    
    st.markdown("### 🛠️ Empfehlung zur Trafostation-Auslegung")
    
    col_opt1, col_opt2 = st.columns(2, gap="large")
    
    with col_opt1:
        st.markdown("#### Option A")
        st.info(f"**1x {trafo_single} kVA** Trafostation")
        
        
    with col_opt2:
        st.markdown("#### Option B")
        st.success(f"**2x {trafo_half_size} kVA** Trafostationen")
        

    st.write("")
    col_back, spacer, col_next = st.columns([1, 4, 1])
    with col_back:
        if st.button("← Zurück", key="zurueck_step6", use_container_width=True):
            st.session_state.step = 5
            st.rerun()
    with col_next:
        if st.button("🔄 System Neustarten", key="restart_app_btn", type="primary", use_container_width=True):
            st.session_state.clear()
            st.rerun()



steps = {
    1: step1, 
    2: step2, 
    3: step3, 
    4: step4, 
    5: step5, 
    6: step6
}

# Rendert die visuelle Statuszeile oben über der App
render_progress_bar(st.session_state.step)

# Führt das aktuelle Skript-Segment aus
steps[st.session_state.step]()
st.divider()