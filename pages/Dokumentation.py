import os
import streamlit as st
import numpy as np

st.set_page_config(page_title="Documentation")

st.title("📚 Documentation")

st.markdown("### 📊 Gleichzeitigkeitsfaktoren nach Bezugsart")

# 1. Define the tab titles
tab_titles = ["🏠 Haushalt", "🔥 Wärmepumpe", "🚗 Ladesäule privat", "⚡ Nachtspeicherheizung"]

# 2. Create the tabs
tab1, tab2, tab3, tab4 = st.tabs(tab_titles)

# 3. Fill each tab with its respective content
with tab1:
    st.latex(r"g(n) = g_{\infty} + (1 - g_{\infty}) \cdot n^{-0.75}")
    st.latex(r"g_{\infty} = 0.07")

with tab2:
    st.latex(r"g(n) = 1.05 \cdot n^{-0.03}")

with tab3:
    st.latex(r"g(n) = g_{\infty} + (1 - g_{\infty}) \cdot a \cdot (n - 1)^{b}")
    st.latex(r"a = 1.4343,\quad b = -0.5203,\quad g_{\infty} = 0.1081")

with tab4:
    st.latex(r"g(n) = g_{\infty} + (1 - g_{\infty}) \cdot n^{a}")
    st.latex(r"a = -0.5,\quad g_{\infty} = 0.7")

st.divider()

st.divider()
st.subheader("📥 Präsentation herunterladen")

file_path = "powerpoint/Lastabschätzung_neubaugebiet.pptx"

if os.path.exists(file_path):
    with open(file_path, "rb") as file:
        btn = st.download_button(
            label="📊 PowerPoint herunterladen (PPTX)",
            data=file,
            file_name="Lastabschätzung_neubaugebiet.pptx",
            mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            type="primary"
        )
else:
    # Falls der Pfad falsch ist, wird diese Warnung anstelle eines leeren Raums angezeigt
    st.warning(f"⚠️ Die Datei konnte unter '{file_path}' nicht gefunden werden. Bitte überprüfe die Ordnerstruktur.")


st.subheader("Quellen")
st.markdown("- [Envelio Gruppen-Gleichzeitigkeitsfaktoren](https://bnnetze.envelio.de/docs/de/01-documentation/01-general/01-calculation-principles/01-analysis/04-group-coincidence-factors/)")
st.markdown("- [Baugesetzbuch](https://www.gesetze-im-internet.de/baunvo/__5a.html)")