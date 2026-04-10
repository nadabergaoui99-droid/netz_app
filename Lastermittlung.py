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


gebietstyp = st.selectbox(
    "Gebietstyp auswählen:",
    list(gebietsdaten.keys())
)

st.subheader("Eigenschaften des Gebietstyps")
st.write(f"**Beschreibung:** {gebietsdaten[gebietstyp]['Beschreibung']}")
st.write(f"**Typische Verbraucher:** {gebietsdaten[gebietstyp]['Typische Verbraucher']}")
st.write(f"**Charakteristik:** {gebietsdaten[gebietstyp]['Charakteristik']}")

st.divider()

st.subheader("Gleichzeitigkeitsfaktorberechnung für Netzteilnehmer")

gebäudecluster = st.selectbox(
    "Gebäudeclustering auswählen:",
    gebäudeclustering_typen
)

# Header row
col1, col2, col3 = st.columns([2, 2, 2], gap="large" )
with col1:
    st.markdown("**Netzteilnehmertyp**")
with col2:
    st.markdown("**Anzahl n**")
with col3:
    st.markdown("**g(n)**")

n_values = {}
ergebnisse = []

for i, typ in enumerate(typen):
    col1, col2, col3 = st.columns([2, 2, 2], gap="large")
    

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
    n_values[typ] = int(n)
    
    # Wärmepumpen automatisch setzen
   
if gebäudecluster == "Neubau ohne Gas/Wärme":
    haushalte = n_values.get("Haushalt", 0)
    n_values["Wärmepumpe"] = int(0.5 * haushalte)
    st.info("Für 'Neubau ohne Gas/Wärme' wurde die Anzahl der Wärmepumpen automatisch auf 50% der Haushalte gesetzt.")
    # Tabelle mit Ergebnissen anzeigen
for typ in typen:
    g = gleichzeitigkeitsfaktor(typ, n_values.get(typ, 0))
    ergebnisse.append((typ, n_values.get(typ, 0), g))

    col1, col2, col3 = st.columns([2, 2, 2], gap="large")
    with col1:
        st.write(typ)
    with col2:
        st.write(n_values.get(typ, 0))
    with col3:
        st.write(f"{g:.4f}")

 # Add empty editable row
st.markdown("**Neuen Netzteilnehmer hinzufügen:**")

col1, col2, col3 = st.columns([2, 2, 2], gap="small")

with col1:
    custom_typ = st.text_input(
        "Netzteilnehmertyp",
        key="custom_typ",
        label_visibility="collapsed",
        placeholder="Netzteilnehmertyp hinzufügen"
    )

with col2:
    custom_n = st.number_input(
        "Anzahl n",
        min_value=0,
        step=1,
        key="custom_n",
        label_visibility="collapsed"
    )

with col3:
    custom_g = st.number_input(
        "g(n)",
        min_value=0.0,
        max_value=1.0,
        step=0.0001,
        key="custom_g",
        label_visibility="collapsed"
    )
if gebäudecluster == "Neubau ohne Gas/Wärme":
    Haushalte = n_values.get("Haushalt", 0)
    n_values["Wärmepumpe"] = int(0.5 * Haushalte)
    st.info("Für 'Neubau ohne Gas/Wärme' wurde die Anzahl der Wärmepumpen automatisch auf 50% der Haushalte gesetzt.")



st.divider()




