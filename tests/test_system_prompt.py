"""
tests/test_system_prompt.py

Test suite for system prompt validation and guardrails.
Ensures the AI assistant maintains professional tone, scope control, and proper responses.
"""
from pathlib import Path
import pytest
from app.services.nodes.generator import load_system_prompt


class TestSystemPromptLoading:
    """Test system prompt file loading."""

    def test_system_prompt_file_exists(self):
        """Verify SYSTEM-PROMPT.md file exists."""
        prompt_path = Path(__file__).parent.parent / "app" / "services" / "config" / "SYSTEM-PROMPT.md"
        assert prompt_path.exists(), f"System prompt file not found at {prompt_path}"

    def test_load_system_prompt(self):
        """Test that system prompt can be loaded successfully."""
        prompt = load_system_prompt()
        assert isinstance(prompt, str), "System prompt should be a string"
        assert len(prompt) > 0, "System prompt should not be empty"


class TestSystemPromptContent:
    """Test system prompt content for required guardrails."""

    @pytest.fixture
    def prompt(self):
        """Load system prompt for tests."""
        return load_system_prompt()

    def test_prompt_has_scope_section(self, prompt):
        """Verify prompt defines scope explicitly."""
        assert "SCOPE & DOMAINS" in prompt, "Prompt must define scope and domains"
        assert "Code of Business Conduct" in prompt, "Prompt should mention Code of Business Conduct"
        assert "Human Rights Policy" in prompt, "Prompt should mention Human Rights Policy"
        assert "Data Protection" in prompt, "Prompt should mention Data Protection"

    def test_prompt_forbids_jokes(self, prompt):
        """Verify prompt explicitly forbids jokes and humor."""
        assert "NEVER make jokes" in prompt, "Prompt must explicitly forbid jokes"
        assert "humor" in prompt.lower(), "Prompt should mention avoiding humor"

    def test_prompt_requires_professional_tone(self, prompt):
        """Verify prompt emphasizes professional tone."""
        assert "professional" in prompt.lower(), "Prompt must emphasize professional tone"
        assert "serious" in prompt.lower(), "Prompt must require serious tone"

    def test_prompt_has_out_of_scope_handling(self, prompt):
        """Verify prompt defines how to handle out-of-scope questions."""
        assert "out-of-scope" in prompt.lower(), "Prompt must define out-of-scope handling"
        assert "doesn't relate to these areas" in prompt, "Prompt should have specific rejection message"

    def test_prompt_handles_insufficient_info(self, prompt):
        """Verify prompt handles 'I don't know' scenarios."""
        assert "don't have sufficient information" in prompt, \
            "Prompt must define clear 'insufficient info' response"
        assert "Do NOT guess" in prompt or "do not guess" in prompt.lower(), \
            "Prompt must forbid guessing or making up information"

    def test_prompt_cites_sources(self, prompt):
        """Verify prompt requires source citation."""
        assert "cite" in prompt.lower(), "Prompt should mention citing sources"
        assert "policy section" in prompt.lower(), "Prompt should mention specific policy sections"

    def test_prompt_uses_format_placeholders(self, prompt):
        """Verify prompt has correct format placeholders."""
        assert "{info}" in prompt, "Prompt must have {info} placeholder for retrieved information"
        assert "{hist_str}" in prompt, "Prompt must have {hist_str} placeholder for history"
        assert "{question}" in prompt, "Prompt must have {question} placeholder for user question"

    def test_prompt_forbids_making_up_policies(self, prompt):
        """Verify prompt forbids fabricating policies."""
        forbid_phrases = ["make up", "make up policies", "Do NOT guess", "extrapolate"]
        assert any(phrase.lower() in prompt.lower() for phrase in forbid_phrases), \
            "Prompt must forbid making up or extrapolating policies"


class TestPromptFormatting:
    """Test system prompt formatting and template structure."""

    @pytest.fixture
    def prompt(self):
        """Load system prompt for tests."""
        return load_system_prompt()

    def test_prompt_is_well_structured(self, prompt):
        """Verify prompt has clear sections."""
        required_sections = [
            "SCOPE & DOMAINS",
            "TONE & BEHAVIOR",
            "RESPONSE GUIDELINES"
        ]
        for section in required_sections:
            assert section in prompt, f"Prompt must have '{section}' section"

    def test_prompt_template_format(self, prompt):
        """Verify prompt can be formatted with template variables."""
        try:
            formatted = prompt.format(
                info="test information",
                hist_str="test history",
                question="test question"
            )
            assert "test information" in formatted
            assert "test history" in formatted
            assert "test question" in formatted
        except KeyError as e:
            pytest.fail(f"Prompt format error: {e}")
