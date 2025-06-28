import json

DEBUG = False


def classify_chunk(txt: str, client, MODEL, SYSTEM) -> str | None:
    """Return heading text or None."""
    user = f"Text chunk:\n'''{txt}'''"
    r = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "system", "content": SYSTEM},
                  {"role": "user", "content": user}],
        temperature=0
    )
    payload = json.loads(r.choices[0].message.content)
    if DEBUG:
        if payload["section"] != "None":
            print('PAYLOAD: ', payload)

    return payload["section"]

def find_n_section(chunks: list[str], n: int, client, MODEL, SYSTEM) -> int | None:
    """Return index where the n *distinct* section (after Abstract & Introduction) starts."""
    seen = set()

    for idx, chunk in enumerate(chunks):
        heading = classify_chunk(chunk, client, MODEL, SYSTEM)
        if not heading:
            continue        # no heading in this chunk

        h = heading.lower().strip(": ").split()[-1]   # normalize quick-n-dirty

        if len(seen) < n:
            if h not in seen:
                seen.add(h)
        else:
            return idx   # n distinct section found → stop

    return None  # never saw n sections

def pdf_to_script(pdf_paths: list, openai_api_key):
    
    # --- 1. Import libraries ---
    import pandas as pd
    from unstructured.partition.pdf import partition_pdf
    from openai import OpenAI
    import json

    client = OpenAI(api_key=openai_api_key)
    MODEL = "gpt-4o-mini"        # cheap & plenty for heading detection

    # ---------- system prompt ----------
    SYSTEM = """
    You are a heading detector.  
    Given a text chunk, check if it is a section heading. If it is, respond with JSON: {"section": "<name>"} else respond with JSON: {"section": "None"}.
    We are interested in headings: abstract, introduction, background, methods, results, discussion, conclusion, references, acknowledgments, appendices OR any other section headings that are not in the list.
    Return **only** the JSON.
    """
    
    ABSTRACT_SYSTEM_PROMPT = """
    You are a strict extractor. The user will give you a list of text chunks that come
    from the front pages of a research paper. They contain an Abstract section plus
    extra headings, author info, and other noise.

    Return ONLY the full, clean Abstract text (no heading line, no metadata, no extra
    characters) in plain text. If you cannot find an Abstract, return: "ABSTRACT NOT FOUND".
    Do not wrap the output in JSON or Markdown—just the abstract itself, nothing more.
    """.strip()

    INTRODUCTION_SYSTEM_PROMPT = """
    You are a strict extractor. The user will give you a list of text chunks that come
    from the front pages of a research paper. They contain an Introduction section plus
    extra headings, author info, and other noise.

    Return ONLY the full, clean Introduction text (no heading line, no metadata, no extra
    characters) in plain text. If you cannot find an Introduction, return: "INTRODUCTION NOT FOUND".
    Do not wrap the output in JSON or Markdown—just the introduction itself, nothing more.
    """.strip()

    SCRIPT_SYSTEM_PROMPT = """
        You are a scriptwriter for an educational persona-based AV system.
        Your job: distill an academic paper’s ABSTRACT and INTRODUCTION into a concise,
        engaging voice-over script using the six numbered sections below.

        Formatting rules (MUST FOLLOW):
        1. Output plain text, no markdown.
        2. Do not add extra headings or commentary.
        3. Keep each section ≤ 2 sentences.
        4. When talking about the paper, talk in third person - use the word "the paper" or "the authors" instead of "we" or "the authors".
        5. Just use text and no other formatting like \n or anything else.

        Purpose of each section — keep these goals in mind while writing:
        0. Hook – Grab attention with a vivid scenario, question, or startling fact - that is relevant to the paper.
        1. Domain & Sub-domain – Orient the audience: name the broad research field
        and the specific niche within it.
        2. Problem Statement – State the concrete gap, limitation, or pain-point that
        motivates the study; make the stakes clear.
        3. Proposed Solution / Novelties – Summarize the core idea, algorithm, or
        experimental approach that is new or unique.
        4. Key Evidence – Cite one or two standout metrics (accuracy, F1, runtime…) and
        mention the dataset or benchmark that proves the method works.
        5. Overall Impact & Outlook – Explain why this matters in the grander scheme,
        and hint at future directions or real-world applications.

        Return the script in exactly that six-section order. Try keeping the script as short and interesting as possible.
        """.strip()
    
    scripts = []

    for pdf_path in pdf_paths:
        
        # --- 1. run Unstructured with layout, images, and metadata ---
        elements = partition_pdf(
            filename=pdf_path,
            strategy="fast",
            extract_images=True,           # save images if embedded
            infer_table_structure=True,    # keep <table> tags intact
            include_metadata=True,         # page numbers, bboxes, etc.
            chunking_strategy="by_title",  # groups narrative by headings
            strategy_kwargs={"multipage_sections": True},
        )

        # --- 2. walk the element stream ---
        info = []

        for el in elements:
            info_dict = {}
            try:
                info_dict['text'] = el.text
            except:
                info_dict['text'] = "NANA"
            try:
                info_dict['category'] = el.category
            except:
                info_dict['category'] = "NANA"
            try:
                info_dict['coordinates'] = el.metadata.coordinates
            except:
                info_dict['coordinates'] = "NANA"
            try:
                info_dict['page_number'] = el.metadata.page_number
            except:
                info_dict['page_number'] = "NANA"
            try:
                info_dict['text_in_metadata'] = el.metadata.text
            except:
                info_dict['text_in_metadata'] = "NANA"
            try:
                info_dict['text_as_html'] = el.metadata.text_as_html
            except:
                info_dict['text_as_html'] = "NANA"
            
            info.append(info_dict)
            
        # --- 3 Parse sections
        chunks = [x['text'] for x in info]
        n = 4

        limit_idx = find_n_section(chunks, n, client, MODEL, SYSTEM)
        if DEBUG:
            if limit_idx is not None:
                print(f"The {n} distinct section begins at chunk #{limit_idx}")
            else:
                print(f"Less than {n} sections detected.")

        # -- 4 Extract sections

        def extract_section(chunks: list[str], section_prompt: str) -> str:
            """
            Pass the list of chunks to the LLM once and get back the abstract text.
            """
            # Combine chunks with line breaks to preserve layout cues
            doc = "\n".join(chunks)

            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": section_prompt},
                    {"role": "user",
                    "content": f"Here are the text chunks:\n\n{doc}\n\n--- END ---"}
                ],
                temperature=0
            )

            return response.choices[0].message.content.strip()

        chunks = chunks[:limit_idx+1]

        abstract_text = extract_section(chunks, ABSTRACT_SYSTEM_PROMPT)
        introduction_text = extract_section(chunks, INTRODUCTION_SYSTEM_PROMPT)

        if DEBUG:
            print("\nEXTRACTED ABSTRACT:\n")
            print(abstract_text)

            print("\nEXTRACTED INTRODUCTION:\n")
            print(introduction_text)

        # -- 5 Generate script
        def generate_script(abstract_text: str, introduction_text: str) -> str:
            """Generate the six-part AV script from abstract and intro."""
            user_content = (
                "ABSTRACT:\n" + abstract_text.strip() +
                "\n\nINTRODUCTION:\n" + introduction_text.strip()
            )

            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": SCRIPT_SYSTEM_PROMPT},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.3,
                max_tokens=450,
            )
            return response.choices[0].message.content.strip()

        script = generate_script(abstract_text, introduction_text)
        if DEBUG:
            print("\n=== Generated Script ===\n")
            print(script)

        # replace \n with a space
        script = script.replace("\n", " ")
        
        scripts.append(script)

    return scripts

if __name__ == "__main__":
    
    pdf_paths = ["/home/dipayan/Desktop/Content_Curator/test_pdf_extraction/Towards_Context_aware_EEG-based_Emotion_Recognition_Models_Personality_and_Emotional_Intelligence_as_Context.pdf"]
    openai_api_key = ''

    scripts = pdf_to_script(pdf_paths, openai_api_key)
    
    print(scripts)
