import re
import uuid
import json
import google.generativeai as genai

# Configure Gemini (Assumes GEMINI_API_KEY is in environment)
genai.configure()

def split_with_gemini(text: str) -> list[str]:
    """
    Uses Gemini to semantically split a large text block into smaller distinct legal clauses.
    """
    prompt = f"""
You are a legal contract analyzer. Your task is to split the following text into distinct legal clauses.
Return ONLY a JSON array of strings, where each string is a complete clause from the text.
Do not add any conversational text or markdown formatting outside of the JSON array.

Text to split:
{text}
"""
    try:
        # Use flash for faster/cheaper text processing
        model = genai.GenerativeModel('models/gemini-1.5-flash') 
        response = model.generate_content(
            prompt, 
            generation_config={"response_mime_type": "application/json"}
        )
        
        clauses = json.loads(response.text)
        if isinstance(clauses, list):
            return clauses
    except Exception as e:
        print(f"Failed to parse Gemini response for splitting: {e}")
        
    # Fallback to returning the original text if Gemini fails
    return [text]

def segment_text(parsed_blocks: list[dict]) -> list[dict]:
    """
    Takes a list of blocks from parsers and segments them into clauses.
    Applies regex splitting, drops clauses < 30 words, and uses Gemini for clauses > 500 words.
    """
    full_text = ""
    block_mappings = []
    
    current_char = 0
    for block in parsed_blocks:
        # Add some padding to cleanly separate blocks
        text = block["text"] + "\n\n"
        full_text += text
        block_mappings.append({
            "start": current_char,
            "end": current_char + len(text),
            "page_num": block.get("page_num", 1),
            "paragraph_index": block.get("paragraph_index", 0)
        })
        current_char += len(text)
        
    # 1. Regex Pass: Split on double newlines, numbered sections, or capitalized headers
    # We'll rely primarily on \n\n which we inserted, and attempt to catch standard headers.
    raw_segments = re.split(r'\n\n+', full_text)
    
    refined_segments = []
    for seg in raw_segments:
        seg = seg.strip()
        if not seg:
            continue
            
        word_count = len(seg.split())
        
        # 2. Filter clauses under 30 words
        if word_count < 30:
            continue
            
        # 3. Use Gemini to re-split clauses over 500 words
        if word_count > 500:
            gemini_clauses = split_with_gemini(seg)
            for gc in gemini_clauses:
                # Re-verify word count on the new chunks
                if len(gc.split()) >= 30: 
                    refined_segments.append(gc)
        else:
            refined_segments.append(seg)
            
    # 4. Re-map to page_num and paragraph_index
    clauses = []
    search_start = 0
    for seg in refined_segments:
        # Find position of this segment in full_text (using a snippet to avoid whitespace mismatch)
        snippet = seg[:50]
        pos = full_text.find(snippet, search_start)
        if pos == -1:
            pos = search_start # Fallback if not found exactly
            
        # Find corresponding block
        page_num = 1
        paragraph_index = 0
        
        for mapping in block_mappings:
            if mapping["start"] <= pos < mapping["end"]:
                page_num = mapping["page_num"]
                paragraph_index = mapping["paragraph_index"]
                break
                
        clauses.append({
            "id": str(uuid.uuid4()),
            "text": seg,
            "type": "unknown",
            "page": page_num, # API contract expects "page"
            "paragraph_index": paragraph_index
        })
        
        search_start = pos + len(seg)
        
    return clauses
