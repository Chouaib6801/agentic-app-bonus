"""
Research Agent - LLM-powered agent with Wikipedia tools.

Implements an agentic pattern with:
- Multimodal input support (text + image)
- Wikipedia search and summary tools
- High context handling via chunking and summarization
"""

import os
import json
from typing import Optional

# Load .env file automatically (override=True to prioritize .env over system env vars)
from dotenv import load_dotenv
load_dotenv(override=True)

from openai import OpenAI

from app.tools_wikipedia import wikipedia_search, wikipedia_summary


class ResearchAgent:
    """
    LLM-powered research agent that uses Wikipedia for information gathering.
    """
    
    # Chunk size for large context handling
    CHUNK_SIZE = 12000
    MAX_CONTEXT_DIRECT = 15000
    
    def __init__(self):
        """Initialize the agent with OpenAI client."""
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.sources = []
    
    def _chunk_text(self, text: str) -> list[str]:
        """Split large text into chunks for processing."""
        chunks = []
        words = text.split()
        current_chunk = []
        current_length = 0
        
        for word in words:
            word_len = len(word) + 1  # +1 for space
            if current_length + word_len > self.CHUNK_SIZE:
                chunks.append(" ".join(current_chunk))
                current_chunk = [word]
                current_length = word_len
            else:
                current_chunk.append(word)
                current_length += word_len
        
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        
        return chunks
    
    def _summarize_chunk(self, chunk: str, chunk_index: int, total_chunks: int) -> str:
        """Summarize a single chunk of text."""
        print(f"  Summarizing chunk {chunk_index + 1}/{total_chunks}...")
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that creates concise summaries. Extract the key points and main ideas from the provided text."
                },
                {
                    "role": "user",
                    "content": f"Please summarize the following text, preserving the most important information:\n\n{chunk}"
                }
            ],
            max_tokens=1000
        )
        
        return response.choices[0].message.content
    
    def _handle_large_context(self, context_text: str) -> str:
        """
        Handle large context via chunking and summarization.
        
        If context is larger than MAX_CONTEXT_DIRECT, split into chunks,
        summarize each, and merge the summaries.
        """
        if len(context_text) <= self.MAX_CONTEXT_DIRECT:
            print(f"  Context size ({len(context_text)} chars) within limit, using directly")
            return context_text
        
        print(f"  Context size ({len(context_text)} chars) exceeds limit, chunking and summarizing...")
        
        # Chunk the text
        chunks = self._chunk_text(context_text)
        print(f"  Split into {len(chunks)} chunks")
        
        # Summarize each chunk
        summaries = []
        for i, chunk in enumerate(chunks):
            summary = self._summarize_chunk(chunk, i, len(chunks))
            summaries.append(summary)
        
        # Merge summaries
        merged = "\n\n---\n\n".join([
            f"**Section {i+1} Summary:**\n{s}" 
            for i, s in enumerate(summaries)
        ])
        
        print(f"  Merged summaries: {len(merged)} chars")
        return merged
    
    def _gather_wikipedia_info(self, prompt: str) -> dict:
        """
        Use Wikipedia tools to gather information relevant to the prompt.
        
        Implements an agentic pattern:
        1. Search Wikipedia for the topic
        2. Get summaries of top results
        3. Return gathered information
        """
        print("  Gathering Wikipedia information...")
        gathered = {
            "searches": [],
            "summaries": []
        }
        
        # Extract key topic from prompt using LLM
        topic_response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "Extract the main topic or subject for a Wikipedia search from the user's question. Respond with just the search query, nothing else."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=50
        )
        search_query = topic_response.choices[0].message.content.strip()
        print(f"  Extracted search query: {search_query}")
        
        # Search Wikipedia
        search_results = wikipedia_search(search_query, limit=5)
        gathered["searches"].append({
            "query": search_query,
            "results": search_results
        })
        self.sources.append({
            "tool": "wikipedia_search",
            "input": {"query": search_query, "limit": 5},
            "output": search_results
        })
        
        # Get summaries for top results (up to 3)
        titles_to_summarize = search_results[:3] if search_results else []
        
        for title in titles_to_summarize:
            print(f"  Getting summary for: {title}")
            summary = wikipedia_summary(title)
            if summary:
                gathered["summaries"].append({
                    "title": title,
                    "summary": summary
                })
                self.sources.append({
                    "tool": "wikipedia_summary",
                    "input": {"title": title},
                    "output": summary[:500] + "..." if len(summary) > 500 else summary
                })
        
        return gathered
    
    def _build_messages(
        self,
        prompt: str,
        image_data: Optional[str],
        processed_context: Optional[str],
        wiki_info: dict
    ) -> list:
        """Build the message list for the final LLM call."""
        
        # System message
        system_content = """You are a research assistant that creates comprehensive, well-structured reports.

Your reports should:
- Be written in Markdown format
- Have a clear title and structure with headers
- Synthesize information from Wikipedia sources
- Include relevant citations and references
- Be informative and well-organized

Always cite your sources using the Wikipedia article titles provided."""

        messages = [{"role": "system", "content": system_content}]
        
        # Build user message content
        user_content = []
        
        # Add image if provided (multimodal support)
        if image_data:
            user_content.append({
                "type": "image_url",
                "image_url": {"url": image_data}
            })
        
        # Build text content
        text_parts = [f"## Research Request\n{prompt}"]
        
        # Add processed context if available
        if processed_context:
            text_parts.append(f"\n## Provided Context\n{processed_context}")
        
        # Add Wikipedia information
        if wiki_info["summaries"]:
            text_parts.append("\n## Wikipedia Sources")
            for item in wiki_info["summaries"]:
                text_parts.append(f"\n### {item['title']}\n{item['summary']}")
        
        text_parts.append("\n## Instructions\nPlease create a comprehensive research report based on the above information. Include a title, introduction, main content with sections, and a references section listing the Wikipedia articles used.")
        
        user_content.append({
            "type": "text",
            "text": "\n".join(text_parts)
        })
        
        messages.append({"role": "user", "content": user_content})
        
        return messages
    
    def research(
        self,
        prompt: str,
        image_data: Optional[str] = None,
        context_text: Optional[str] = None
    ) -> dict:
        """
        Execute the research workflow.
        
        Args:
            prompt: The research question or topic
            image_data: Optional base64 data URL of an image
            context_text: Optional large text context
        
        Returns:
            Dictionary with 'report' and 'sources'
        """
        print("Starting research workflow...")
        self.sources = []
        
        # Step 1: Handle large context if provided
        processed_context = None
        if context_text:
            print("Step 1: Processing context text...")
            processed_context = self._handle_large_context(context_text)
        else:
            print("Step 1: No context text provided, skipping...")
        
        # Step 2: Gather Wikipedia information
        print("Step 2: Gathering external data from Wikipedia...")
        wiki_info = self._gather_wikipedia_info(prompt)
        
        # Step 3: Generate the report
        print("Step 3: Generating research report...")
        messages = self._build_messages(prompt, image_data, processed_context, wiki_info)
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=4000
        )
        
        report = response.choices[0].message.content
        print("Research workflow completed!")
        
        return {
            "report": report,
            "sources": self.sources
        }

