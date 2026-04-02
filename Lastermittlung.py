import streamlit as st
import math


st.set_page_config(
    page_title="Dokumentation",
)



def gleichzeitigkeitsfaktor(typ, n):
    if n <= 0:
        return 0.0
    if typ == "Haushalt":
        g_inf = 0.07
        g = g_inf + (1 - g_inf) * (n ** -0.75)

    elif typ == "Wärmepumpe":
        g = 1.05 * (n ** -0.03)

    elif typ == "E-Mobilität":
        # mapped to private charging station logic
        g_inf = 0.1081
        a = 1.4343
        b = -0.5203
        if n == 1:
            g = 1.0
        else:
            g = g_inf + (1 - g_inf) * a * ((n - 1) ** b)

    elif typ == "Photovoltaik":
        g = 1.0

    else:
        g = 1.0

  


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

typen = ["Haushalt", "Wärmepumpe", "E-Mobilität", "Photovoltaik"]


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

# Header row
col1, col2, col3 = st.columns([2, 2, 2])
with col1:
    st.markdown("**Netzteilnehmertyp**")
with col2:
    st.markdown("**Anzahl n**")
with col3:
    st.markdown("**g(n)**")

ergebnisse = []

for i, typ in enumerate(typen):
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

st.divider()




