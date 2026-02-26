"""PDF processing utilities."""
import io
import re
import logging
import PyPDF2
import uuid
from datetime import datetime, timezone
from pathlib import Path

from db import db, UPLOAD_DIR


def extract_text_from_pdf(pdf_content: bytes) -> str:
    try:
        pdf_file = io.BytesIO(pdf_content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text.strip()
    except Exception as e:
        logging.error(f"PDF extraction error: {str(e)}")
        return ""


def split_into_chunks(text: str, chunk_size: int = 1000) -> list:
    """Split text into chunks at sentence boundaries."""
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks = []
    current_chunk = ""
    for sentence in sentences:
        if len(current_chunk) + len(sentence) > chunk_size and current_chunk:
            chunks.append(current_chunk.strip())
            current_chunk = sentence
        else:
            current_chunk += " " + sentence if current_chunk else sentence
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    return chunks


async def rebuild_subtopic_text_cache(subtopic_id: str):
    """Rebuild the extracted_text cache and knowledge_chunks for a subtopic."""
    subtopic = await db.subtopics.find_one({"id": subtopic_id}, {"_id": 0})
    if not subtopic:
        return

    all_text = ""
    for pdf_file in subtopic.get("knowledge_base_files", []):
        fp = UPLOAD_DIR / pdf_file
        if fp.exists():
            with open(fp, "rb") as f:
                extracted = extract_text_from_pdf(f.read())
                if extracted:
                    all_text += extracted + "\n\n"

    await db.subtopics.update_one(
        {"id": subtopic_id},
        {"$set": {
            "extracted_text": all_text.strip(),
            "text_updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )

    await db.knowledge_chunks.delete_many({"subtopic_id": subtopic_id})
    subtopic_name = subtopic.get("name", "")
    if all_text.strip():
        chunks = split_into_chunks(all_text.strip())
        chunk_docs = []
        for i, chunk_content in enumerate(chunks):
            chunk_docs.append({
                "id": str(uuid.uuid4()),
                "subtopic_id": subtopic_id,
                "subtopic_name": subtopic_name,
                "source_file": "combined",
                "content": chunk_content,
                "chunk_index": i,
                "created_at": datetime.now(timezone.utc).isoformat()
            })
        if chunk_docs:
            await db.knowledge_chunks.insert_many(chunk_docs)
