from tenacity import retry, wait_exponential, stop_after_attempt
from typing import Literal
import requests
import json
from typing import Dict, Any, List
from datetime import datetime

class MaturityAuditor:
    def __init__(self, gemini_client=None):
        self.gemini_client = gemini_client

    def audit_pypi_package(self, package_name: str) -> Dict[str, Any]:
        """
        Deeply inspects a PyPI package to extract its full capability set and maturity level.
        """
        url = f"https://pypi.org/pypi/{package_name}/json"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code != 200:
                return {"error": f"Package {package_name} not found on PyPI"}
            
            data = response.json()
            info = data.get("info", {})
            releases = data.get("releases", {})
            
            # Extract high-level wisdom
            maturity_data = {
                "name": package_name,
                "version": info.get("version"),
                "summary": info.get("summary"),
                "description": info.get("description", "")[:5000],  # Keep first 5k chars of README
                "author": info.get("author"),
                "project_urls": info.get("project_urls", {}),
                "release_count": len(releases),
                "last_release": list(releases.keys())[-1] if releases else "N/A",
                "source": "pypi"
            }
            
            # Use Gemini to synthesize "Maturity Wisdom" if available
            if self.gemini_client:
                maturity_data["wisdom"] = self._synthesize_maturity_wisdom(maturity_data)
            
            return maturity_data
        except Exception as e:
            return {"error": str(e)}

    def _synthesize_maturity_wisdom(self, data: Dict[str, Any]) -> str:
        """
        Synthesizes a CompetePulse-grade maturity assessment using Gemini.
        """
        prompt = f"""
        <system_instructions>
        You are a Principal AI Architect performing a Technical Maturity Audit on an SDK.
        Your goal is to provide "Field Wisdom" for CompetePulses.
        </system_instructions>
        
        <context>
        Package: {data['name']}
        Summary: {data['summary']}
        Version: {data['version']}
        Release Count: {data['release_count']}
        Description Snippet: {data['description'][:2000]}
        </context>
        
        <task>
        Summarize the 'Maturity & Capabilities' of this package in 3 sections:
        1. 💎 KEY CAPABILITIES: What does it actually allow architects to build?
        2. 📈 MATURITY SCORE: Is it production-ready? (Early Alpha, Stable, Enterprise Grade)
        3. 🎯 SALES PLAY: How should the field position this to customers?
        </task>
        
        <format>
        Return a clean, bulleted synthesis with emojis.
        </format>
        """
        try:
            resp = self.gemini_client.models.generate_content(model='gemini-3.1-flash-lite', contents=prompt)
            return resp.text.strip()
        except Exception:
            return "Unable to synthesize wisdom at this time."
