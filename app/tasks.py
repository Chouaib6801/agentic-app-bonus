"""
Background task definitions for research jobs.
"""

import json
import traceback
from pathlib import Path

from app.agent import ResearchAgent
from app.utils_files import generate_pdf_report


def run_research_job(params: dict) -> dict:
    """
    Execute a research job.
    
    This is the main task that:
    1. Processes the input (prompt, image, context)
    2. Runs the research agent with Wikipedia tools
    3. Generates output files (report.md, report.pdf, sources.json)
    
    Args:
        params: Dictionary with job_id, prompt, image_data, context_text, job_dir
    
    Returns:
        Dictionary with job results and file paths
    """
    job_id = params["job_id"]
    prompt = params["prompt"]
    image_data = params.get("image_data")
    context_text = params.get("context_text")
    job_dir = Path(params["job_dir"])
    
    print(f"[Job {job_id}] Starting research job")
    print(f"[Job {job_id}] Prompt: {prompt[:100]}...")
    
    try:
        # Initialize the research agent
        agent = ResearchAgent()
        
        # Run the research
        result = agent.research(
            prompt=prompt,
            image_data=image_data,
            context_text=context_text
        )
        
        # Save outputs
        report_content = result["report"]
        sources = result["sources"]
        
        # Save report.md
        report_md_path = job_dir / "report.md"
        with open(report_md_path, "w", encoding="utf-8") as f:
            f.write(report_content)
        print(f"[Job {job_id}] Saved report.md")
        
        # Save sources.json
        sources_path = job_dir / "sources.json"
        with open(sources_path, "w", encoding="utf-8") as f:
            json.dump(sources, f, indent=2, ensure_ascii=False)
        print(f"[Job {job_id}] Saved sources.json")
        
        # Generate PDF
        pdf_path = job_dir / "report.pdf"
        generate_pdf_report(report_content, str(pdf_path))
        print(f"[Job {job_id}] Saved report.pdf")
        
        print(f"[Job {job_id}] Job completed successfully")
        
        return {
            "status": "success",
            "files": ["report.md", "report.pdf", "sources.json"]
        }
        
    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
        print(f"[Job {job_id}] Job failed: {error_msg}")
        
        # Save error to file
        error_path = job_dir / "error.txt"
        with open(error_path, "w", encoding="utf-8") as f:
            f.write(error_msg)
        
        raise

