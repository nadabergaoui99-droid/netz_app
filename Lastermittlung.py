import streamlit as st
import math 
import base64


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

st.subheader("Eigenschaften des Gebietstyps")
gebietstyp = st.selectbox(
    "Gebietstyp auswählen:",
    list(gebietsdaten.keys())
)


st.write(f"**Beschreibung:** {gebietsdaten[gebietstyp]['Beschreibung']}")
st.write(f"**Typische Verbraucher:** {gebietsdaten[gebietstyp]['Typische Verbraucher']}")
st.write(f"**Charakteristik:** {gebietsdaten[gebietstyp]['Charakteristik']}")

st.divider()
# Init state
if "step" not in st.session_state:
    st.session_state.step = 1
if "selected" not in st.session_state:
    st.session_state.selected = []


st.subheader("Lastabschätzung von Neubaugebieten ")
 
def step1():   
    # The multiselect
    selected = st.multiselect(
        label="Wähle oder tippe neue Arten:",
        options=typen,
        accept_new_options=True,
        placeholder="Tippen zum Hinzufügen..."
    )
    if st.button("Weiter"):
        st.session_state.selected = selected
        st.session_state.step = 2
        st.rerun()

def step2():
    st.text("Eingaben")

    selected = st.session_state.get("selected", [])

    if "Haushalt" in selected:
        st.markdown(" **Anzahl der Haushalte**")
        st.number_input(
            "Wie viele Haushalte sind vorhanden?",
            min_value=1,
            step=1,
            key="n_h",
            label_visibility="collapsed"
        )

    if "Gewerbe" in selected:
        st.write("")
        st.markdown(" **Anzahl der Gewerbeeinheiten**")
        st.number_input(
            "Wie viele Gewerbeeinheiten sind vorhanden?",
            min_value=1,
            step=1,
            key="n_g",
            label_visibility="collapsed"
        )

    if st.button("Zurück"):
        st.session_state.step = 1
        st.rerun()
    
       # 👉 EVERYTHING inside popover
    with st.expander("📊 Eingaben anzeigen"):
    # your full table here
        
        # Header row
        col1, col2, col3 = st.columns([2, 2, 2])
        with col1:
            st.markdown("**Netzteilnehmertyp**")
        with col2:
            st.markdown("**Anzahl n**")
        with col3:
            st.markdown("**g(n)**")

        ergebnisse = []

        for i, typ in enumerate(selected):
            col1, col2, col3 = st.columns([2, 2, 2])

            with col1:
                st.write(typ)

            with col2:
                n = st.number_input(
                    f"Anzahl für {typ}",
                    min_value=0,
                    step=1,
                    key=f"n_{i}",
                    label_visibility="collapsed"
                )

            g = gleichzeitigkeitsfaktor(typ, int(n))
            ergebnisse.append((typ, int(n), g))
            with col3:
                st.write(f"{g:.4f}")
    st.session_state.ergebnisse = ergebnisse

steps = {
    1: step1,
    2: step2,
   
}

steps[st.session_state.step] ()
st.divider()




