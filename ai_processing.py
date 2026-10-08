"""Optional AI extraction; synthetic data only before IT approval."""
import base64
import json
import os
from core import local_notes_draft

def extract_call(notes, image_bytes=None, image_mime="image/jpeg", use_ai=False):
    if not use_ai:
        if image_bytes:
            raise ValueError("Handwriting images require AI mode")
        return local_notes_draft(notes)
    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY is not set")
    if not notes.strip() and not image_bytes:
        raise ValueError("Provide notes or an image")
    from openai import OpenAI
    content = [{"type":"text","text":"Return JSON fields subject, notes, next_steps from these sales notes. Do not invent details. " + (notes or "See image")}]
    if image_bytes:
        if image_mime not in ("image/jpeg","image/png","image/webp"):
            raise ValueError("Unsupported image format")
        b64=base64.b64encode(image_bytes).decode("ascii")
        content.append({"type":"image_url","image_url":{"url":f"data:{image_mime};base64,{b64}"}})
    response=OpenAI().chat.completions.create(model=os.getenv("OPENAI_MODEL","gpt-4o-mini"),
        response_format={"type":"json_object"},
        messages=[{"role":"system","content":"Return only JSON string fields subject, notes, next_steps. Do not invent details."},
                  {"role":"user","content":content}])
    obj=json.loads(response.choices[0].message.content or "{}")
    return {k:str(obj.get(k) or "").strip() for k in ("subject","notes","next_steps")}
