from pypdf import PdfReader


def extract_text_from_pdf(uploaded_file) -> str:
  """Extracts and cleans text from an uploaded Streamlit PDF file."""
  reader = PdfReader(uploaded_file)
  pages_text = []

  for page_num, page in enumerate(reader.pages, start=1):
    text = page.extract_text()
    if text:
      cleaned = " ".join(text.split())
      pages_text.append(f"--- Page {page_num} ---\n{cleaned}")

  return "\n\n".join(pages_text)