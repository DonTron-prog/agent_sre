import os
import glob
import json
import yaml
from typing import List, Tuple, Dict

class DocumentProcessor:
    def __init__(self, chunk_size: int, chunk_overlap: int):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def _chunk_text(self, text: str) -> List[str]:
        paragraphs = text.split("\n\n")
        chunks = []
        current_chunk = ""
        
        for i, paragraph_text in enumerate(paragraphs):
            paragraph = paragraph_text.strip() # Process stripped paragraphs
            if not paragraph:
                continue

            # Case 1: The paragraph itself is larger than the chunk size
            if len(paragraph) > self.chunk_size:
                # First, add any accumulated current_chunk before processing this large paragraph
                if current_chunk:
                    current_chunk_stripped = current_chunk.strip()
                    if current_chunk_stripped:
                        print(f"    Adding accumulated chunk of size: {len(current_chunk_stripped)} before large paragraph.")
                        chunks.append(current_chunk_stripped)
                    current_chunk = "" # Reset current_chunk

                # Now, split the large paragraph
                print(f"  Paragraph {i} (length {len(paragraph)}) is larger than chunk_size ({self.chunk_size}). Splitting it directly.")
                para_start = 0
                while para_start < len(paragraph):
                    para_end = para_start + self.chunk_size
                    sub_chunk_content = paragraph[para_start:para_end].strip()
                    
                    if sub_chunk_content:
                        print(f"    Adding direct split sub-chunk of size: {len(sub_chunk_content)}")
                        chunks.append(sub_chunk_content)
                    
                    # Determine overlap for the next sub-chunk from this large paragraph
                    # Overlap is character based here. self.chunk_overlap is in characters.
                    overlap_amount_chars = self.chunk_overlap
                    para_start = para_end - overlap_amount_chars
                    
                    # Ensure para_start is valid and we don't get stuck in an infinite loop if chunk_overlap >= chunk_size
                    if para_start < 0: para_start = 0
                    if para_end >= len(paragraph): break # Reached end of paragraph
                    if para_start >= para_end: # Avoid infinite loop if overlap is too large or chunk_size too small
                        print(f"    Warning: Overlap ({overlap_amount_chars}) is too large for chunk_size ({self.chunk_size}) or remaining paragraph. Advancing without overlap.")
                        para_start = para_end


                current_chunk = "" # Ensure current_chunk is reset after a large paragraph

            # Case 2: The paragraph is not larger than the chunk size
            else:
                # If adding this paragraph would make current_chunk too big
                if len(current_chunk) + (len("\n\n") if current_chunk else 0) + len(paragraph) > self.chunk_size and current_chunk:
                    current_chunk_stripped = current_chunk.strip()
                    if current_chunk_stripped:
                        print(f"    Adding chunk of size: {len(current_chunk_stripped)} (due to new paragraph making it too large).")
                        chunks.append(current_chunk_stripped)
                    
                    # Apply word-based overlap from the end of the just-added chunk
                    overlap_words_list = current_chunk_stripped.split()
                    overlap_word_count = min(self.chunk_overlap // 5, len(overlap_words_list)) if self.chunk_overlap > 0 else 0
                    
                    if overlap_word_count > 0:
                        overlap_text = " ".join(overlap_words_list[-overlap_word_count:])
                        current_chunk = overlap_text + "\n\n" + paragraph
                    else:
                        current_chunk = paragraph
                # Else, just append the paragraph to current_chunk
                else:
                    if current_chunk:
                        current_chunk += "\n\n" + paragraph
                    else:
                        current_chunk = paragraph
        
        # Add any remaining current_chunk
        if current_chunk:
            current_chunk_stripped = current_chunk.strip()
            if current_chunk_stripped:
                print(f"    Adding final accumulated chunk of size: {len(current_chunk_stripped)}")
                chunks.append(current_chunk_stripped)
        
        if not chunks and text.strip(): # Should only happen if text is very small
             print(f"  Warning: No chunks produced from non-empty text, adding entire text (size {len(text.strip())}) as one chunk.")
             chunks.append(text.strip())
             
        return chunks

    def _load_and_process_file(self, file_path: str) -> Tuple[List[str], List[Dict]]:
        content = ""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                if file_path.endswith(".json"):
                    content = json.dumps(json.load(f))
                elif file_path.endswith(".yml") or file_path.endswith(".yaml"):
                    content = yaml.dump(yaml.safe_load(f))
                else: # .md, .txt
                    content = f.read()
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return [], []

        if not content:
            print(f"  No content found for {file_path}")
            return [], []
        
        print(f"  Content length for {file_path}: {len(content)} characters")
        chunks = self._chunk_text(content)
        print(f"  Number of chunks produced for {file_path}: {len(chunks)}")
        metadatas = [{"source": file_path, "file_name": os.path.basename(file_path), "chunk_index": i} for i in range(len(chunks))]
        return chunks, metadatas

    def load_and_index_documents(self, docs_dir: str) -> Tuple[List[str], List[Dict]]:
        print(f"Loading documents from: {docs_dir}")
        all_chunks = []
        all_metadatas = []
        
        supported_extensions = ["*.json", "*.md", "*.yml", "*.yaml", "*.txt"]
        file_paths = []
        for ext in supported_extensions:
            file_paths.extend(glob.glob(os.path.join(docs_dir, "**", ext), recursive=True))

        if not file_paths:
            print(f"!!! DEBUG: No documents found in {docs_dir} with supported extensions.")
            return [], []

        print(f"!!! DEBUG: Found {len(file_paths)} documents to process.")
        for file_path in file_paths:
            print(f"!!! DEBUG: Processing {file_path}...")
            chunks, metadatas = self._load_and_process_file(file_path)
            print(f"!!! DEBUG: Generated {len(chunks)} chunks from {file_path}")
            
            # Check for duplicate chunks
            chunk_set = set(chunks)
            if len(chunk_set) < len(chunks):
                print(f"!!! DEBUG: WARNING - Found {len(chunks) - len(chunk_set)} duplicate chunks in {file_path}")
            
            all_chunks.extend(chunks)
            all_metadatas.extend(metadatas)
        
        print(f"!!! DEBUG: Total chunks generated: {len(all_chunks)}")
        print(f"!!! DEBUG: Number of unique chunks: {len(set(all_chunks))}")
        
        return all_chunks, all_metadatas