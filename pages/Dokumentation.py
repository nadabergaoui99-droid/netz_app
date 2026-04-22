import streamlit as st
import numpy as np

st.set_page_config(page_title="Documentation")

st.title("📚 Documentation")


st.subheader("Haushalt")
st.latex(r"g(n) = g_{\infty} + (1 - g_{\infty}) \cdot n^{-0.75}")
st.latex(r"g_{\infty} = 0.07")

st.subheader("Wärmepumpe")
st.latex(r"g(n) = 1.05 \cdot n^{-0.03}")

st.subheader("Ladesäule privat")
st.latex(r"g(n) = g_{\infty} + (1 - g_{\infty}) \cdot a \cdot (n - 1)^{b}")
st.latex(r"a = 1.4343,\quad b = -0.5203,\quad g_{\infty} = 0.1081")

st.subheader("Nachtspeicherheizung")
st.latex(r"g(n) = g_{\infty} + (1 - g_{\infty}) \cdot n^{a}")
st.latex(r"a = -0.5,\quad g_{\infty} = 0.7")

st.divider()

st.subheader("Quellen")
st.markdown("- [Envelio Gruppen-Gleichzeitigkeitsfaktoren](https://bnnetze.envelio.de/docs/de/01-documentation/01-general/01-calculation-principles/01-analysis/04-group-coincidence-factors/)")
st.markdown("- [Baugesetzbuch](https://www.gesetze-im-internet.de/baunvo/__5a.html)")