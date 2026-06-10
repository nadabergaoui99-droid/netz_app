import streamlit as st
import math 
import base64
import pandas as pd

# 1. PAGE CONFIG
st.set_page_config(page_title="Lastberechnung", page_icon="⚡", layout="wide")

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
    st.write("Wähle aus, welche Verbraucher berücksichtigt werden müssen.")
    
   
    st.markdown("### Bezug")
    selected_bezug = st.pills(
    "Verfügbare Bezugsarten:",
    options=typen,
    selection_mode="multi",
    default=st.session_state.selected_bezug,
        )
    

    st.write("")
    col_back, spacer, col_next = st.columns([1, 4, 1])
    with col_back:
        if st.button("← Zurück", key="zurueck_step2", use_container_width=True):
            st.session_state.step = 1
            st.rerun()
    with col_next:
        if st.button("Weiter →", key="weiter_step2", type="primary", use_container_width=True):
            if not selected_bezug and not selected_bezug:
                st.error("⚠️ Bitte wähle mindestens einen Netzteilnehmer aus.")
            else:
                st.session_state.selected_bezug = selected_bezug
                st.session_state.selected_bezug = selected_bezug
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
                    f"⚠️ Gewerbe-Inputs sind nur für 'Mischgebiete' und 'Gewerbegebiet' aktiv. "
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
            help="Die Anzahl der Fahrzeuge ist editierbar"
        )
   
    st.session_state.n_ev = n_ev
 
    with st.expander("📘 Berechnungsmethode", expanded=False):
        st.markdown("""
       
        
        | Siedlungsstruktur (Cluster) | Pkw pro Wohneinheit (WE) | E-Kfz-Anteil  | Mathematische Formel |
        | :--- | :---: | :---: | :---: |
        | **Innenstadt** | 0,5 | 40% | WE · 0,4 · 0,4 |
        | **Randbereich / EFH / Pendler** | 1,4 | 50% | WE · 1,4 · 0,5 |
        """)
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
    st.write(" die Gleichzeitigkeitsfaktoren kann bei Bedarf direkt in der Tabelle angepasst werden:")
    
    selected_bezug = st.session_state.selected_bezug
    n_h = st.session_state.n_haushalte if "Haushalt" in selected_bezug else 0
    n_g = st.session_state.n_gewerbe if "Gewerbe" in selected_bezug else 0
    n_ev = st.session_state.n_ev if "E-Mobilität" in selected_bezug else 0
    
    # WP-Anzahl berechnen falls ausgewählt
    n_wp = 0
    if "Wärmepumpe" in selected_bezug and n_h > 0:
        for cluster, percentage in st.session_state.cluster_percentages.items():
            anteil = percentage / 100
            faktor = 1.0 if "ohne Gas" in cluster else (0.5 if "mit Gas" in cluster else 0.1)
            n_wp += n_h * faktor * anteil
    st.session_state.n_wp = int(n_wp)

    # Basis-Daten generieren
    display_data = []
    if "Haushalt" in selected_bezug and n_h > 0:
        display_data.append({"Netzteilnehmertyp": "Haushalt", "Anzahl (n)": n_h, "Gleichzeitigkeitsfaktor g(n)": float(f"{gleichzeitigkeitsfaktor('Haushalt', n_h):.4f}")})
    if "Wärmepumpe" in selected_bezug and st.session_state.n_wp > 0:
        display_data.append({"Netzteilnehmertyp": "Wärmepumpe", "Anzahl (n)": st.session_state.n_wp, "Gleichzeitigkeitsfaktor g(n)": float(f"{gleichzeitigkeitsfaktor('Wärmepumpe', st.session_state.n_wp):.4f}")})
    if "Gewerbe" in selected_bezug and st.session_state.gebietstyp in ("Mischgebiete", "Gewerbegebiete") and n_g > 0:
        display_data.append({"Netzteilnehmertyp": "Gewerbe", "Anzahl (n)": n_g, "Gleichzeitigkeitsfaktor g(n)": float(f"{gleichzeitigkeitsfaktor('Gewerbe', n_g):.4f}")})
    if "E-Mobilität" in selected_bezug and n_ev > 0:
        display_data.append({"Netzteilnehmertyp": "E-Mobilität", "Anzahl (n)": n_ev, "Gleichzeitigkeitsfaktor g(n)": float(f"{gleichzeitigkeitsfaktor('E-Mobilität', n_ev):.4f}")})

    if display_data:
        df_base = pd.DataFrame(display_data)
        
        # NEU: st.data_editor statt st.dataframe erlaubt direkte Eingabe
        edited_df = st.data_editor(
            df_base,
            use_container_width=True,
            hide_index=True,
            disabled=["Netzteilnehmertyp", "Anzahl (n)"], # Nur der Faktor ist editierbar
            column_config={
                "Gleichzeitigkeitsfaktor g(n)": st.column_config.NumberColumn(
                    min_value=0.0,
                    max_value=1.0,
                    step=0.0001,
                    format="%.4f"
                )
            }
        )
        
        # Speicher die editierten Faktoren im Session State für Schritt 6 ab
        factors_dict = dict(zip(edited_df["Netzteilnehmertyp"], edited_df["Gleichzeitigkeitsfaktor g(n)"]))
        st.session_state.custom_factors = factors_dict
    else:
        st.warning("⚠️ Keine aktiven Verbraucher")
        st.session_state.custom_factors = {}

    col_back, spacer, col_next = st.columns([1, 4, 1])
    with col_back:
        if st.button("← Zurück", key="zurueck_step5", use_container_width=True):
            st.session_state.step = 4 if "E-Mobilität" in selected_bezug else 3
            st.rerun()
    with col_next:
        if st.button("Ergebnis berechnen 🎉", key="weiter_step5", type="primary", use_container_width=True):
            st.session_state.step = 6
            st.rerun()

def step6():
    st.subheader(" Ergebnis der Lastabschätzung")
    st.write("   **Einzel-Leistung (kW)** kann bei Bedarf nochmals manuell angepasst werden ")
    
    selected_bezug = st.session_state.selected_bezug
    werte = {
        "Haushalt": st.session_state.n_haushalte,
        "Wärmepumpe": st.session_state.n_wp,
        "E-Mobilität": st.session_state.n_ev,
        "Gewerbe": st.session_state.n_gewerbe if st.session_state.gebietstyp in ("Mischgebiete", "Gewerbegebiete") else 0,
    }
    
    # Holen der (evtl. editierten) Faktoren aus Schritt 5
    custom_factors = st.session_state.get("custom_factors", {})

    detailed_results = []
    for typ in selected_bezug:
        n = werte.get(typ, 0)
        if n <= 0:
            continue
        p = leistungen.get(typ, 0)
        g = custom_factors.get(typ, gleichzeitigkeitsfaktor(typ, n))
        
        detailed_results.append({
            "Typ": typ, 
            "Anzahl (n)": n, 
            "Einzel-Leistung (kW)": float(p), 
            "Gleichzeitigkeit g(n)": float(g)
        })
    
    # Standardwert für p_ges definieren, falls keine Daten vorhanden sind
    p_ges = 0.0
    
    if detailed_results:
        df_res_base = pd.DataFrame(detailed_results)
        
        edited_res_df = st.data_editor(
            df_res_base,
            use_container_width=True,
            hide_index=True,
            disabled=["Typ", "Anzahl (n)", "Gleichzeitigkeit g(n)"], 
            column_config={
                "Einzel-Leistung (kW)": st.column_config.NumberColumn(
                    min_value=0.0,
                    step=0.5,
                    format="%.1f"
                )
            },
            key="res_editor"
        )
        
        # Berechne die Summenleistung pro Zeile
        edited_res_df["Summenleistung (kW)"] = (
            edited_res_df["Anzahl (n)"] * edited_res_df["Einzel-Leistung (kW)"] * edited_res_df["Gleichzeitigkeit g(n)"]
        ).round(2)
        
        # FEHLERBEHEBUNG 1 & 2: Gesamtleistung aus der editierten Tabelle berechnen
        p_ges = float(edited_res_df["Summenleistung (kW)"].sum())
        
    # FEHLERBEHEBUNG 3: Trafoberechnung und Anzeige in die Einrückung mit einbeziehen
    # bzw. absichern, dass p_ges existiert:
    if p_ges > 0:
        trafo_single = next((t for t in trafo_leistung if p_ges <= t), 2500)
        trafo_half_size = next((t for t in trafo_leistung if (p_ges / 2) <= t), 2500)
        
        st.write(f"Für das gewählte Gebiet wird eine  Gesamtlast von **{p_ges:.2f} kW** erwartet.")
        
        with st.expander("📊 Dimensionierung & Trafostation-Empfehlung", expanded=True):
            col_metric, col_text = st.columns([1, 2], gap="large")
            with col_metric:
                st.metric(label="Errechnete Gesamtleistung P_ges", value=f"{p_ges:.2f} kW")
            with col_text:
                col_opt1, col_opt2 = st.columns(2, gap="large")
                with col_opt1:
                    st.markdown("#### Option A ")
                    st.info(f"**1x {trafo_single} kVA** Trafostation")
                    st.caption("Wirtschaftlich optimal bei kompakter Bebauung.")
                with col_opt2:
                    st.markdown("#### Option B ")
                    st.success(f"**2x {trafo_half_size} kVA** Trafostationen")
                    st.caption("Höhere Versorgungssicherheit und bessere Spannungshaltung.")
    else:
        st.warning("Keine aktiven Verbraucher oder Leistungen zur Berechnung vorhanden.")

    # Navigation Buttons (sauber eingerückt auf Funktionsebene)
    col_back, spacer, col_next = st.columns([1, 4, 1])
    with col_back:
        if st.button("← Zurück", key="zurueck_step6", use_container_width=True):
            st.session_state.step = 5
            st.rerun()
    with col_next:
        if st.button("🔄 System Neustarten", key="restart_app_btn", type="primary", use_container_width=True):
            st.session_state.clear()
            st.rerun()


render_progress_bar(st.session_state.step)

if st.session_state.step == 1:
    step1()
elif st.session_state.step == 2:
    step2()
elif st.session_state.step == 3:
    step3()
elif st.session_state.step == 4:
    step4()
elif st.session_state.step == 5:
    step5()
elif st.session_state.step == 6:
    step6()
