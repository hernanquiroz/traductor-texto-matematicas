# ∑ Traductor Matemático Multiidioma (LaTeX-safe)

Traduce la **prosa** de documentos matemáticos entre 7 idiomas
(español, inglés, francés, alemán, italiano, portugués, ruso)
manteniendo **intactas** todas las fórmulas y ecuaciones LaTeX.

Entrada: PDF → Salida: PDF traducido.

## 🚀 Demo online

La app está desplegada en Streamlit Cloud: (pegar aquí tu URL tras el deploy)

## ⚙️ Instalación local

    pip install -r requirements.txt
    streamlit run app.py

## 🖥️ Uso por línea de comandos

    python app.py entrada.pdf es salida.pdf

## 🔐 API key de DeepL (opcional, mejor calidad)

Crea un archivo `.env` en la raíz:
    DEEPL_API_KEY=tu_clave_aqui

Sin clave, la app usa Google Translator; sin conexión, Argos Translate (offline).

## 🧠 Cómo preserva las fórmulas

1. Extrae el texto del PDF con PyMuPDF.
2. Detecta bloques LaTeX (`$...$`, `$$...$$`, `\[...\]`, entornos
   `equation`, `align`, `theorem`, ...) y los reemplaza por placeholders.
3. Traduce **solo la prosa** y aplica un glosario matemático de post-edición.
4. Restaura los placeholders con las fórmulas originales sin alterar.
5. Renderiza cada fórmula como imagen (matplotlib) y compone el PDF final
   con ReportLab.

## ☁️ Despliegue en Streamlit Cloud

1. Sube este repo a GitHub (público o privado).
2. Entra a https://share.streamlit.io y conecta tu cuenta de GitHub.
3. "New app" → selecciona el repo y `app.py` como archivo principal.
4. Si usas DeepL: Settings → Secrets → añade `DEEPL_API_KEY = "tu_clave"`.
5. Deploy. Cada `git push` actualiza la app automáticamente.

## 📝 Limitaciones

- PDFs escaneados requieren OCR (no incluido por defecto).
- El render de LaTeX usa mathtext de matplotlib; entornos muy complejos
  pueden mostrarse como texto crudo.
- Los 7 idiomas requieren que el motor de traducción los soporte
  (Argos offline necesita paquetes instalados: `argostranslate install`).