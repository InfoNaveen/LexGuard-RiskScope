import fitz  # PyMuPDF

def parse_pdf(file_path: str) -> list[dict]:
    """
    Extracts text from a PDF file block by block.
    Returns a list of dicts: {"text": str, "page_num": int, "paragraph_index": int}
    """
    doc = fitz.open(file_path)
    extracted = []
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        # fitz uses 0-based indexing for pages, we use 1-based for humans
        # get_text("blocks") returns a list of blocks, where block[4] is the text
        blocks = page.get_text("blocks")
        for i, b in enumerate(blocks):
            # A block tuple format: (x0, y0, x1, y1, "text", block_no, block_type)
            # We only care about text blocks (type 0)
            if len(b) >= 7 and b[6] == 0:
                text = b[4].strip()
                if text:
                    extracted.append({
                        "text": text,
                        "page_num": page_num + 1,
                        "paragraph_index": i
                    })
            
    doc.close()
    return extracted
