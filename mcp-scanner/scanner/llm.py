import os
import json
import logging
from typing import Dict, Any, Optional, List
from openai import OpenAI
import google.generativeai as genai
from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()

logger = logging.getLogger(__name__)

# Pydantic models for structured output
class ThreatItem(BaseModel):
    """Individual security threat."""
    threat_type: str = Field(description="Category of the threat")
    description: str = Field(description="Detailed explanation of the threat")
    severity: str = Field(description="Severity level: low, medium, high, or critical")
    snippet: str = Field(description="Optional code snippet showing the issue")

class SecurityChecklist(BaseModel):
    """14-point security criteria checklist."""
    prompt_injection: bool = Field(description="True if prompt injection vulnerability exists")
    data_exfiltration: bool = Field(description="True if data exfiltration risk exists")
    tool_poisoning: bool = Field(description="True if tool poisoning/shadowing detected")
    unauthorized_code_execution: bool = Field(description="True if unauthorized code execution possible")
    system_manipulation: bool = Field(description="True if system manipulation risk exists")
    safety_harms: bool = Field(description="True if safety harms detected (harassment, hate speech, etc.)")
    docstring_mismatch: bool = Field(description="True if docstring doesn't match actual behavior")
    cross_file_dataflow: bool = Field(description="True if suspicious cross-file dataflow detected")
    hidden_behavior: bool = Field(description="True if hidden undocumented behavior exists")
    yara_patterns: bool = Field(description="True if YARA malicious patterns detected")
    ai_defense_violations: bool = Field(description="True if AI defense policy violations found")
    initialize_instructions: bool = Field(description="True if InitializeResult instruction issues found")
    input_schema_issues: bool = Field(description="True if input schema vulnerabilities exist")
    mime_type_issues: bool = Field(description="True if MIME type issues detected")

class SecurityAnalysis(BaseModel):
    """Complete security analysis response."""
    risk_score: int = Field(description="Risk score from 0 (safe) to 10 (critical)")
    risk_level: str = Field(description="Risk level: SAFE, LOW, MEDIUM, HIGH, or CRITICAL")
    security_checklist: SecurityChecklist = Field(description="14-point security criteria checklist")
    breakdown: List[ThreatItem] = Field(description="List of detected threats")


class LLMAnalyzer:
    """
LLM-based security analysis for MCP servers.
Supports both OpenRouter and Google Gemini APIs.
"""

    def __init__(self):
        # Determine which API to use
        self.api_type = os.getenv("LLM_API_TYPE", "gemini")  # "openrouter" or "gemini"
        
        if self.api_type == "gemini":
            self.api_key = os.getenv("GEMINI_API_KEY")
            self.model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")
            
            if self.api_key:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel(self.model_name)
                logger.info(f"Initialized Gemini API with model: {self.model_name}")
            else:
                logger.warning("GEMINI_API_KEY not found. LLM analysis will be skipped.")
                self.model = None
                
        else:  # openrouter
            self.api_key = os.getenv("OPENROUTER_API_KEY")
            self.model_name = os.getenv("OPENROUTER_MODEL", "google/gemini-2.0-flash-exp:free")
            
            if self.api_key:
                self.client = OpenAI(
                    base_url="https://openrouter.ai/api/v1",
                    api_key=self.api_key,
                    timeout=30.0
                )
                logger.info(f"Initialized OpenRouter API with model: {self.model_name}")
            else:
                logger.warning("OPENROUTER_API_KEY not found. LLM analysis will be skipped.")
                self.client = None

    def analyze_code(self, code: str, file_path: str) -> Dict[str, Any]:
        """
        Analyze code for security threats using LLM.
        Returns a risk analysis dict.
        """
        if self.api_type == "gemini":
            return self._analyze_with_gemini(code, file_path)
        else:
            return self._analyze_with_openrouter(code, file_path)

    def _analyze_with_gemini(self, code: str, file_path: str) -> Dict[str, Any]:
        """Use Google Gemini API for analysis with structured JSON output."""
        if not self.model:
            return {
                "risk_score": 0,
                "risk_level": "UNKNOWN",
                "security_checklist": {
                    "prompt_injection": False,
                    "data_exfiltration": False,
                    "tool_poisoning": False,
                    "unauthorized_code_execution": False,
                    "system_manipulation": False,
                    "safety_harms": False,
                    "docstring_mismatch": False,
                    "cross_file_dataflow": False,
                    "hidden_behavior": False,
                    "yara_patterns": False,
                    "ai_defense_violations": False,
                    "initialize_instructions": False,
                    "input_schema_issues": False,
                    "mime_type_issues": False,
                },
                "breakdown": []
            }

            
        # Truncate very large code samples to avoid token limits
        max_code_length = 8000  # characters
        if len(code) > max_code_length:
            logger.warning(f"Code for {file_path} is {len(code)} chars, truncating to {max_code_length}")
            code = code[:max_code_length] + "\n\n... [Code truncated for analysis]"
        
        try:
            logger.info(f"Sending request to Gemini for {file_path}. Model: {self.model_name}")
            
            prompt = self._create_prompt(code, file_path)
            
            # Use Gemini's JSON schema mode for structured output
            response = self.model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    response_schema=SecurityAnalysis,
                    temperature=0.1,
                    max_output_tokens=2048,
                )
            )
            
            response_text = response.text
            logger.info(f"Received response for {file_path}")
            logger.debug(f"Raw Gemini response: {response_text[:500]}...")
            
            # Extract JSON from response with multiple strategies
            json_text = response_text.strip()
            
            # Strategy 1: Remove markdown code blocks if present
            if json_text.startswith("```"):
                lines = json_text.split('\n')
                # Remove first line (```json or ```)
                if lines[0].startswith('```'):
                    lines = lines[1:]
                # Remove last line if it's ```
                if lines and lines[-1].strip() == '```':
                    lines = lines[:-1]
                json_text = '\n'.join(lines).strip()
            
            # Strategy 2: Find JSON object boundaries
            start_idx = json_text.find('{')
            end_idx = json_text.rfind('}')
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                json_text = json_text[start_idx:end_idx+1]
            
            # Strategy 3: Try to fix common JSON issues
            # Replace escaped newlines in strings that might break parsing
            # This is a simple attempt - more sophisticated repair could be added
            
            # Parse JSON directly
            try:
                analysis = json.loads(json_text)
                logger.info(f"Successfully parsed analysis for {file_path}: Risk={analysis.get('risk_score', '?')}, Level={analysis.get('risk_level', '?')}")
                return analysis
            except json.JSONDecodeError as je:
                logger.error(f"JSON decode error for {file_path}: {je}")
                logger.error(f"Attempted to parse: {json_text[:500]}...")
                
                # Last resort: try to extract at least the risk info with regex
                try:
                    risk_score = 0
                    risk_level = "SAFE"
                    
                    # Try to extract risk_score
                    score_match = re.search(r'"risk_score"\s*:\s*(\d+)', json_text)
                    if score_match:
                        risk_score = int(score_match.group(1))
                    
                    # Try to extract risk_level
                    level_match = re.search(r'"risk_level"\s*:\s*"([^"]+)"', json_text)
                    if level_match:
                        risk_level = level_match.group(1)
                    
                    logger.warning(f"Extracted partial data via regex: score={risk_score}, level={risk_level}")
                    
                    return {
                        "risk_score": risk_score,
                        "risk_level": risk_level,
                        "security_checklist": {
                            "prompt_injection": False,
                            "data_exfiltration": False,
                            "tool_poisoning": False,
                            "unauthorized_code_execution": False,
                            "system_manipulation": False,
                            "safety_harms": False,
                            "docstring_mismatch": False,
                            "cross_file_dataflow": False,
                            "hidden_behavior": False,
                            "yara_patterns": False,
                            "ai_defense_violations": False,
                            "initialize_instructions": False,
                            "input_schema_issues": False,
                            "mime_type_issues": False,
                        },
                        "breakdown": [{
                            "threat_type": "Parsing Error",
                            "description": f"Failed to parse LLM response: {str(je)}",
                            "severity": "low",
                            "snippet": ""
                        }]
                    }
                except Exception as regex_err:
                    logger.error(f"Regex extraction also failed: {regex_err}")
                    # Return safe default if everything fails
                    return {
                        "risk_score": 0,
                        "risk_level": "ERROR",
                        "security_checklist": {
                            "prompt_injection": False,
                            "data_exfiltration": False,
                            "tool_poisoning": False,
                            "unauthorized_code_execution": False,
                            "system_manipulation": False,
                            "safety_harms": False,
                            "docstring_mismatch": False,
                            "cross_file_dataflow": False,
                            "hidden_behavior": False,
                            "yara_patterns": False,
                            "ai_defense_violations": False,
                            "initialize_instructions": False,
                            "input_schema_issues": False,
                            "mime_type_issues": False,
                        },
                        "breakdown": [{
                            "threat_type": "Parsing Error",
                            "description": f"Failed to parse LLM response: {str(je)}",
                            "severity": "low",
                            "snippet": ""
                        }]
                    }
            
            
        except Exception as e:
            logger.error(f"Error during Gemini analysis of {file_path}: {e}")
            return {
                "risk_score": 0,
                "risk_level": "ERROR",
                "security_checklist": {
                    "prompt_injection": False,
                    "data_exfiltration": False,
                    "tool_poisoning": False,
                    "unauthorized_code_execution": False,
                    "system_manipulation": False,
                    "safety_harms": False,
                    "docstring_mismatch": False,
                    "cross_file_dataflow": False,
                    "hidden_behavior": False,
                    "yara_patterns": False,
                    "ai_defense_violations": False,
                    "initialize_instructions": False,
                    "input_schema_issues": False,
                    "mime_type_issues": False,
                },
                "breakdown": [{
                    "threat_type": "Analysis Error",
                    "description": f"LLM Analysis failed: {str(e)}",
                    "severity": "low",
                    "snippet": ""
                }]
            }

    def _analyze_with_openrouter(self, code: str, file_path: str) -> Dict[str, Any]:
        """Use OpenRouter API for analysis."""
        if not self.client:
            return {
                "risk_score": 0,
                "risk_level": "UNKNOWN",
                "breakdown": []
            }

        try:
            logger.info(f"Sending request to OpenRouter for {file_path}. Model: {self.model_name}")
            
            prompt = self._create_prompt(code, file_path)
            
            completion = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are a security analyst specializing in MCP server code review."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=2048
            )
            
            response_text = completion.choices[0].message.content
            logger.info(f"Received response for {file_path}")
            logger.debug(f"Raw OpenRouter response: {response_text[:200]}...")
            
            analysis = self._parse_json_response(response_text)
            logger.info(f"Parsed analysis for {file_path}: {analysis}")
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error during OpenRouter analysis of {file_path}: {e}")
            return {
                "risk_score": 0,
                "risk_level": "ERROR",
                "breakdown": [{
                    "description": f"LLM Analysis failed: {str(e)}"
                }]
            }

    def _create_prompt(self, code: str, file_path: str) -> str:
        """Create analysis prompt for the LLM."""
        return f"""Analyze this MCP (Model Context Protocol) server code for security threats and vulnerabilities.

File: {file_path}

Code:
```
{code[:3000]}
```

Provide a comprehensive security analysis in JSON format with the following structure:

{{
  "risk_score": <integer 0-10, where 0=safe, 10=critical>,
  "risk_level": "<SAFE|LOW|MEDIUM|HIGH|CRITICAL>",
  "security_checklist": {{
    "prompt_injection": <true/false>,
    "data_exfiltration": <true/false>,
    "tool_poisoning": <true/false>,
    "unauthorized_code_execution": <true/false>,
    "system_manipulation": <true/false>,
    "safety_harms": <true/false>,
    "docstring_mismatch": <true/false>,
    "cross_file_dataflow": <true/false>,
    "hidden_behavior": <true/false>,
    "yara_patterns": <true/false>,
    "ai_defense_violations": <true/false>,
    "initialize_instructions": <true/false>,
    "input_schema_issues": <true/false>,
    "mime_type_issues": <true/false>
  }},
  "breakdown": [
    {{
      "threat_type": "<category>",
      "description": "<detailed explanation>",
      "severity": "<low|medium|high|critical>",
      "snippet": "<optional code snippet>"
    }}
  ]
}}

Security Criteria Definitions:
1. **Prompt Injection**: Attempts to override system instructions or bypass guardrails
2. **Data Exfiltration**: Unauthorized exposure of sensitive information or intellectual property
3. **Tool Poisoning/Shadowing**: Modifying tool behavior or substituting legitimate tools with malicious versions
4. **Unauthorized Code Execution**: Execution of malicious scripts or command sequences
5. **System Manipulation**: Unauthorized access to file systems, registries, or system resources
6. **Safety Harms**: Harassment, hate speech, profanity, and violence
7. **Docstring-to-Code Alignment**: Does the tool's description match what the code actually does?
8. **Cross-File Dataflow**: Parameters flowing across multiple files with hidden malicious logic
9. **Hidden Behavior**: Actions (network calls, file deletions) not mentioned in description
10. **YARA Analyzer**: Specific patterns matching known malicious behavior
11. **AI Defense API**: Violations of safety policies and complex security issues
12. **InitializeResult Instructions**: Issues in usage guidelines and security notes
13. **Input Schemas**: Parameter and input type injection vulnerabilities
14. **MIME Types**: Content type filtering and scanning issues

For each criterion, set to true if the issue EXISTS, false if it does NOT exist.
Provide detailed threat descriptions in the breakdown array for any issues found.

Respond ONLY with valid JSON, no other text."""

    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """Parse JSON from LLM response."""
        try:
            # Try to find JSON in the response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                analysis = json.loads(json_str)
                
                # Validate required fields
                if "risk_level" in analysis and "risk_score" in analysis:
                    return analysis
            
            # If parsing failed, return safe default
            logger.warning("Could not parse JSON from LLM response, returning SAFE")
            return {
                "risk_score": 0,
                "risk_level": "SAFE",
                "breakdown": []
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            return {
                "risk_score": 0,
                "risk_level": "SAFE",
                "breakdown": []
            }
