# -*- coding: utf-8 -*-
"""
∑ TRADUCTOR MATEMÁTICO MULTIIDIOMA (LaTeX-safe)
Traduce la PROSA de documentos matemáticos en 7 idiomas manteniendo
INTACTAS todas las fórmulas y ecuaciones LaTeX. PDF -> PDF.
Uso:  streamlit run app.py   |   python app.py entrada.pdf es salida.pdf
Dependencias: pip install streamlit pymupdf reportlab matplotlib deep-translator python-dotenv
"""
import os, re, io, sys, tempfile
from pathlib import Path

IDIOMAS = {"Español":"es","Inglés":"en","Francés":"fr","Alemán":"de",
           "Italiano":"it","Portugués":"pt","Ruso":"ru"}

# Términos de notación universal que NO se traducen
TERMINOS_PROTEGIDOS = ["QED","et al.","w.l.o.g.","s.t.","iff","LHS","RHS",
                       "det","tr","rank","dim","ker","Im","id","a.e.","i.i.d."]

# Entornos LaTeX que se preservan en bloque
ENTORNOS = ["equation","equation*","align","align*","gather","gather*","multline",
            "cases","array","matrix","pmatrix","bmatrix","split","aligned",
            "theorem","lemma","corollary","proof","definition"]

# Silabus: glosario matemático de post-edición por idioma destino
GLOSARIO = {
 "en":{"campo":"field","anillo":"ring","límite":"limit","derivada":"derivative",
       "prueba":"proof","teorema":"theorem","conjunto":"set","sucesión":"sequence"},
 "fr":{"campo":"corps","anillo":"anneau","límite":"limite","derivada":"dérivée",
       "prueba":"démonstration","teorema":"théorème","conjunto":"ensemble","sucesión":"suite"},
 "de":{"campo":"Körper","anillo":"Ring","límite":"Grenzwert","derivada":"Ableitung",
       "prueba":"Beweis","teorema":"Satz","conjunto":"Menge","sucesión":"Folge"},
 "it":{"campo":"campo","anillo":"anello","límite":"limite","derivada":"derivata",
       "prueba":"dimostrazione","teorema":"teorema","conjunto":"insieme","sucesión":"successione"},
 "pt":{"campo":"corpo","anillo":"anel","límite":"limite","derivada":"derivada",
       "prueba":"demonstração","teorema":"teorema","conjunto":"conjunto","sucesção":"sequência"},
 "ru":{"campo":"поле","anillo":"кольцо","límite":"предел","derivada":"производная",
       "prueba":"доказательство","teorema":"теорема","conjunto":"множество","sucesión":"последовательность"},
 "es":{"campo":"campo","anillo":"anillo","límite":"límite","derivada":"derivada",
       "prueba":"demostración","teorema":"teorema","conjunto":"conjunto","sucesión":"sucesión"},
}

# ---------------- SEGMENTADOR: protege fórmulas con placeholders ----------------
def _patrones_math():
    ent = "|".join(ENTORNOS)
    return [
        re.compile(r"\\begin\{(" + ent + r")\*?\}.*?\\end\{\1\*?\}", re.S),
        re.compile(r"\\\[.*?\\\]", re.S),
        re.compile(r"\$\$.*?\$\$", re.S),
        re.compile(r"\$[^$\n]+?\$"),
        re.compile(r"\\\(.*?\\\)", re.S),
    ]

def proteger(texto, ph):
    """Reemplaza cada fórmula por ⟦MATHn⟧ y guarda el original en `ph`."""
    for pat in _patrones_math():
        def _r(m):
            k = f"MATH{len(ph)}"
            ph[k] = m.group(0)
            return f"⟦{k}⟧"
        texto = pat.sub(_r, texto)
    for t in TERMINOS_PROTEGIDOS:
        texto = texto.replace(t, f"⟦KEEP:{t}⟧")
    return texto

def restaurar(texto, ph):
    for k, orig in ph.items():
        texto = re.sub(r"⟦\s*" + k + r"\s*⟧", lambda m, o=orig: o, texto)
    return re.sub(r"⟦\s*KEEP:\s*(.+?)\s*⟧", r"\1", texto)

# ---------------- MOTOR DE TRADUCCIÓN (DeepL -> Google) ----------------
class Traductor:
    def __init__(self, destino):
        self.destino = destino
        self.key = os.getenv("DEEPL_API_KEY")
        from deep_translator import GoogleTranslator
        self.google = GoogleTranslator(source="auto", target=destino)

    def _bloque(self, texto):
        if not texto.strip():
            return texto
        if self.key:
            try:
                import deepl
                return deepl.Translator(self.key).translate_text(
                    texto, target_lang=self.destino.upper()).text
            except Exception:
                pass
        try:
            return self.google.translate(texto[:4800])
        except Exception as e:
            print(f"[aviso] fallo de traducción ({e}); se conserva el original.")
            return texto

    def documento(self, texto):
        ph = {}
        protegido = proteger(texto, ph)
        glos = GLOSARIO.get(self.destino, {})
        # traduce solo los fragmentos de prosa (fuera de placeholders)
        partes = re.split(r"(⟦MATH\d+⟧)", protegido)
        salida = []
        for p in partes:
            if re.fullmatch(r"⟦MATH\d+⟧", p.strip()):
                salida.append(p.strip())
            else:
                t = self._bloque(p)
                for o, d in glos.items():
                    t = re.sub(rf"\b{re.escape(o)}\b", d, t)
                salida.append(t)
        return restaurar("".join(salida), ph)

# ---------------- ENTRADA/SALIDA PDF ----------------
def leer_pdf(ruta):
    import fitz
    doc = fitz.open(ruta)
    texto = "\n".join(p.get_text("text") for p in doc)
    doc.close()
    return texto

def _latex_png(latex, fs=12):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig = plt.figure(figsize=(0.01, 0.01))
    fig.text(0, 0, f"${latex}$", fontsize=fs)
    buf = io.BytesIO()
    fig.savefig(buf, dpi=300, bbox_inches="tight", pad_inches=0.02, facecolor="white")
    plt.close(fig)
    buf.seek(0)
    return buf

def generar_pdf(texto, titulo, destino, ruta_out):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib.enums import TA_CENTER
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image

    doc = SimpleDocTemplate(ruta_out, pagesize=A4, leftMargin=2*cm,
                            rightMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
    st = getSampleStyleSheet()
    st.add(ParagraphStyle("Formula", alignment=TA_CENTER))
    story = [Paragraph(titulo, st["Title"]), Spacer(1, 12)]

    trozos = re.split(r"(\$\$.*?\$\$|\\\[.*?\\\]|\\begin\{(?:equation|align)\*?\}.*?\\end\{(?:equation|align)\*?\})", texto, flags=re.S)
    for t in trozos:
        t = t.strip()
        if not t:
            continue
        esc = t.replace("&", "&amp;").replace("<", "&lt;")
        if t.startswith("$$") or t.startswith("\\[") or t.startswith("\\begin"):
            latex = t.replace("$$","").replace("\\[","").replace("\\]","").strip()
            try:
                img = Image(_latex_png(latex), width=10*cm, height=2.5*cm, kind="proportional")
                story.append(img)
            except Exception:
                story.append(Paragraph(esc, st["Formula"]))
            story.append(Spacer(1, 8))
        else:
            for linea in t.split("\n"):
                if linea.strip():
                    story.append(Paragraph(linea.strip(), st["BodyText"]))
            story.append(Spacer(1, 6))
    doc.build(story)
    return ruta_out

# ---------------- PIPELINE COMPLETO ----------------
def traducir_pdf(entrada, destino, salida=None, titulo="Documento traducido"):
    texto = leer_pdf(entrada)
    traducido = Traductor(destino).documento(texto)
    if salida is None:
        salida = str(Path(entrada).with_name(Path(entrada).stem + f"_{destino}.pdf"))
    return generar_pdf(traducido, f"{titulo} ({destino})", destino, salida)

# ---------------- APP STREAMLIT ----------------
def app():
    import streamlit as st
    st.set_page_config(page_title="Traductor Matemático", page_icon="∑", layout="wide")
    st.title("∑ Traductor Matemático Multiidioma")
    st.caption("Traduce la prosa matemática en 7 idiomas conservando **intactas** "
               "todas las fórmulas y ecuaciones LaTeX. PDF → PDF.")

    with st.sidebar:
        destino = st.selectbox("Idioma de destino", list(IDIOMAS))
        titulo = st.text_input("Título", "Documento traducido")

    archivo = st.file_uploader("Sube el PDF de entrada", type=["pdf"])
    if archivo and st.button("Traducir", type="primary"):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(archivo.getvalue())
            ruta = tmp.name
        texto = leer_pdf(ruta)
        with st.spinner("Traduciendo…"):
            traducido = Traductor(IDIOMAS[destino]).documento(texto)
        c1, c2 = st.columns(2)
        c1.subheader("Original");  c1.text_area("", texto[:4000], height=300)
        c2.subheader(f"Traducido ({destino})");  c2.text_area("", traducido[:4000], height=300)
        with st.spinner("Generando PDF…"):
            out = generar_pdf(traducido, f"{titulo} ({destino})", destino,
                              ruta.replace(".pdf", f"_{IDIOMAS[destino]}.pdf"))
        with open(out, "rb") as f:
            st.download_button("⬇️ Descargar PDF traducido", f.read(),
                               file_name=Path(out).name, mime="application/pdf")
        st.success("✅ Listo. Fórmulas preservadas sin alteraciones.")

if __name__ == "__main__":
    if len(sys.argv) == 4:
        print(traducir_pdf(sys.argv[1], sys.argv[2], sys.argv[3]))
    else:
        app()  # streamlit run app.py
