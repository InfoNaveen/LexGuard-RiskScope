import docx

def parse_docx(file_path: str) -> list[dict]:
    """
    Extracts text from a DOCX file paragraph by paragraph.
    Returns a list of dicts: {"text": str, "page_num": int, "paragraph_index": int}
    """
    doc = docx.Document(file_path)
    extracted = []
    
    for i, para in enumerate(doc.paragraphs):
        text = para.text.strip()
        if text:
            extracted.append({
                "text": text,
                "page_num": 1,  # DOCX doesn't have reliable page numbers natively via python-docx
                "paragraph_index": i
            })
            
    return extracted
