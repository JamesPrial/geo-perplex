"""
Comprehensive tests for source extraction in the GEO-Perplex project.

This test file covers:
1. Multi-tier fallback source extraction
2. Source metadata extraction (domain, citation numbers, title)
3. Source deduplication and validation
4. Configuration-based behavior
5. Edge cases and error handling
6. Backward compatibility with old and new formats

Tests are designed to work with both the current basic implementation
and guide future enhancements for advanced source extraction features.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import List, Dict, Any
from src.search.extractor import extract_search_results, ExtractionResult, _validate_extraction
from src.config import SELECTORS


class MockElement:
    """Mock nodriver Element with attrs and text_all properties."""

    def __init__(self, href: str = '', text: str = '', attrs: Dict[str, str] = None):
        """
        Initialize mock element.

        Args:
            href: URL for the element
            text: Text content for the element
            attrs: Attributes dictionary (if None, will create with href)
        """
        self.attrs = attrs if attrs is not None else {'href': href}
        self.text_all = text
        self._text = text  # For compatibility with .text property

    @property
    def text(self):
        """Direct text property (without descendants)."""
        return self._text


class MockPage:
    """
    Simple mock of nodriver Page for basic testing.

    LIMITATIONS:
    - Does not simulate ElementWaiter behavior
    - Does not simulate dynamic content loading
    - Does not simulate CDP interactions

    Tests using this mock should focus on validation logic and helper
    functions. Full extraction flow requires integration tests with real browser.
    """

    def __init__(self, url: str = '', main_text: str = ''):
        """
        Initialize mock page.

        Args:
            url: Page URL
            main_text: Text content for main element
        """
        self.url = url
        self._main_text = main_text
        self._source_elements = []
        self._screenshot_saved = False
        self._screenshot_path = None

    async def select(self, selector: str, timeout: int = None):
        """Mock select method for single element selection."""
        if selector == 'main':
            main_elem = MockElement(text=self._main_text)
            return main_elem
        return None

    async def select_all(self, selector: str):
        """Mock select_all method for multiple elements."""
        if 'source' in selector or 'footer' in selector:
            return self._source_elements
        return []

    def set_source_elements(self, elements: List[MockElement]):
        """Set mock source elements for testing."""
        self._source_elements = elements

    async def save_screenshot(self, path: str, full_page: bool = True):
        """Mock screenshot saving."""
        self._screenshot_saved = True
        self._screenshot_path = path


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_page():
    """Provides a mock page for testing."""
    page = MockPage(url='https://www.perplexity.ai/search/test-query')
    return page


@pytest.fixture
def basic_sources():
    """Provides basic source elements without advanced metadata."""
    return [
        MockElement('https://example.com/article1', 'Example Article 1'),
        MockElement('https://example.com/article2', 'Example Article 2'),
        MockElement('https://test.org/page', 'Test Organization Page'),
    ]


@pytest.fixture
def sources_with_duplicates():
    """Provides source elements with duplicate URLs."""
    return [
        MockElement('https://example.com/page', 'First occurrence'),
        MockElement('https://different.com/page', 'Different site'),
        MockElement('https://example.com/page', 'Duplicate occurrence'),
        MockElement('https://another.com/page', 'Another site'),
    ]


@pytest.fixture
def sources_with_invalid():
    """Provides source elements with invalid/filtered URLs."""
    return [
        MockElement('https://example.com/valid', 'Valid Source'),
        MockElement('https://www.perplexity.ai/internal', 'Perplexity Internal'),
        MockElement('https://example.com/login', 'Login Page'),
        MockElement('https://test.com/upgrade', 'Upgrade Page'),
        MockElement('https://good.com/article', 'Good Article'),
    ]


@pytest.fixture
def sources_without_text():
    """Provides source elements without sufficient text."""
    return [
        MockElement('https://example.com/1', 'Good text here'),
        MockElement('https://example.com/2', 'AB'),  # Too short (< 3 chars)
        MockElement('https://example.com/3', ''),     # Empty
        MockElement('https://example.com/4', 'Valid source text'),
    ]


@pytest.fixture
def sources_without_href():
    """Provides source elements without href attribute."""
    return [
        MockElement('https://example.com/1', 'Has URL'),
        MockElement('', 'No URL', attrs={}),
        MockElement('https://example.com/2', 'Another good one'),
    ]


# ============================================================================
# BASIC EXTRACTION TESTS
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.unit
class TestBasicSourceExtraction:
    """Tests for basic source extraction functionality."""

    @pytest.mark.integration
    @pytest.mark.skip(reason="Requires real browser - MockPage doesn't simulate ElementWaiter")
    async def test_extract_sources_basic_success(self, mock_page, basic_sources):
        """Test basic source extraction with valid elements."""
        mock_page.set_source_elements(basic_sources)
        # Set valid answer text
        mock_page._main_text = 'This is a valid answer with sufficient content for extraction.'

        result = await extract_search_results(mock_page, screenshot_path=None)

        assert result.success is True
        assert len(result.sources) == 3
        assert result.sources[0]['url'] == 'https://example.com/article1'
        assert result.sources[0]['text'] == 'Example Article 1'

    @pytest.mark.integration
    @pytest.mark.skip(reason="Requires real browser - MockPage doesn't simulate ElementWaiter")
    async def test_extract_sources_no_sources_found(self, mock_page):
        """Test extraction when no source elements are found."""
        mock_page.set_source_elements([])
        mock_page._main_text = 'This is a valid answer with sufficient content but no sources available.'

        result = await extract_search_results(mock_page, screenshot_path=None)

        # Should succeed even without sources (sources are optional)
        assert result.success is True
        assert result.sources == []

    @pytest.mark.integration
    @pytest.mark.skip(reason="Requires real browser - MockPage doesn't simulate ElementWaiter")
    async def test_extract_sources_with_screenshot(self, mock_page, basic_sources):
        """Test extraction with screenshot enabled."""
        mock_page.set_source_elements(basic_sources)
        mock_page._main_text = 'Valid answer text for testing with screenshot functionality enabled.'
        screenshot_path = '/tmp/test_screenshot.png'

        result = await extract_search_results(mock_page, screenshot_path=screenshot_path)

        assert result.success is True
        assert mock_page._screenshot_saved is True
        assert mock_page._screenshot_path == screenshot_path


# ============================================================================
# VALIDATION TESTS
# ============================================================================

@pytest.mark.unit
class TestSourceValidation:
    """Tests for source validation logic."""

    def test_validate_extraction_valid_with_sources(self):
        """Test validation with valid answer and sources."""
        answer = "This is a valid answer with sufficient content."
        sources = [
            {'url': 'https://example.com', 'text': 'Example'},
            {'url': 'https://test.com', 'text': 'Test'},
        ]

        is_valid, error = _validate_extraction(answer, sources)

        assert is_valid is True
        assert error is None

    def test_validate_extraction_valid_without_sources(self):
        """Test validation with valid answer but no sources (acceptable)."""
        answer = "This is a valid answer without sources but sufficient content."
        sources = None

        is_valid, error = _validate_extraction(answer, sources)

        assert is_valid is True
        assert error is None

    def test_validate_extraction_valid_empty_sources(self):
        """Test validation with empty sources list (acceptable)."""
        answer = "Valid answer with empty sources list but good content length."
        sources = []

        is_valid, error = _validate_extraction(answer, sources)

        assert is_valid is True
        assert error is None

    def test_validate_extraction_answer_too_short(self):
        """Test validation fails when answer is too short."""
        answer = "Short"  # Less than 20 characters
        sources = [{'url': 'https://example.com', 'text': 'Test'}]

        is_valid, error = _validate_extraction(answer, sources)

        assert is_valid is False
        assert 'too short' in error.lower()

    def test_validate_extraction_error_message_detected(self):
        """Test validation fails when error messages are detected."""
        answer = "Sorry, I couldn't find any results for your query."
        sources = []

        is_valid, error = _validate_extraction(answer, sources)

        assert is_valid is False
        assert 'error message detected' in error.lower()

    def test_validate_extraction_no_valid_source_urls(self):
        """Test validation with sources that have invalid URLs."""
        answer = "This is a valid answer with sufficient content."
        sources = [
            {'url': 'not-a-url', 'text': 'Invalid URL'},
            {'url': 'ftp://old-protocol.com', 'text': 'Wrong protocol'},
        ]

        is_valid, error = _validate_extraction(answer, sources)

        # Validation should fail because no valid HTTP(S) URLs found
        assert is_valid is False
        assert 'no valid source urls' in error.lower()


# ============================================================================
# EDGE CASE TESTS
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.unit
class TestSourceExtractionEdgeCases:
    """Tests for edge cases in source extraction.

    Note: All tests in this class patch TIMEOUTS to use 1-second values
    to avoid hanging on ElementWaiter polls (default is 30s).
    """

    @pytest.mark.integration
    @pytest.mark.skip(reason="MockPage cannot simulate full extraction flow - requires real browser")
    async def test_sources_without_href(self, mock_page, sources_without_href):
        """Test that elements without href attribute are skipped.

        This test requires integration with a real browser as MockPage cannot properly
        simulate the ElementWaiter behavior and multi-strategy text extraction."""
        mock_page.set_source_elements(sources_without_href)
        mock_page._main_text = '1 step completed\n\nValid answer content for testing source extraction edge cases.\n\nask a follow-up'

        with patch('src.search.extractor.TIMEOUTS', {
            'content_stability': 1, 'page_load': 1, 'element_selection': 1,
            'search_initiation': 1, 'auth_verification': 1, 'new_chat_navigation': 1,
        }):
            result = await extract_search_results(mock_page, screenshot_path=None)

        assert result.success is True
        assert len(result.sources) == 2
        assert all('url' in source for source in result.sources)
        assert all(source['url'].startswith('http') for source in result.sources)

    async def test_empty_answer_text(self, mock_page, basic_sources):
        """Test handling when no answer text is extracted.

        Uses patched TIMEOUTS with short values (1s) to avoid hanging
        on ElementWaiter polls. Original TIMEOUTS['content_stability'] = 30s.
        """
        mock_page.set_source_elements(basic_sources)
        mock_page._main_text = ''  # Empty answer

        # Patch TIMEOUTS to use shorter values and avoid long waits
        with patch('src.search.extractor.TIMEOUTS', {
            'content_stability': 1,
            'page_load': 1,
            'element_selection': 1,
            'search_initiation': 1,
            'auth_verification': 1,
            'new_chat_navigation': 1,
        }):
            result = await extract_search_results(mock_page, screenshot_path=None)

        assert result.success is False
        assert result.error is not None

    async def test_extraction_with_exception(self, mock_page):
        """Test graceful handling when extraction raises exception."""
        # Mock select_all to raise exception
        async def raise_error(selector):
            raise RuntimeError("Simulated extraction error")

        mock_page.select_all = raise_error
        mock_page._main_text = 'Valid answer text for exception testing scenario.'

        # Patch TIMEOUTS to avoid long waits
        with patch('src.search.extractor.TIMEOUTS', {
            'content_stability': 1, 'page_load': 1, 'element_selection': 1,
            'search_initiation': 1, 'auth_verification': 1, 'new_chat_navigation': 1,
        }):
            result = await extract_search_results(mock_page, screenshot_path=None)

        # Should handle exception gracefully
        assert result.success is False or len(result.sources) == 0


# ============================================================================
# ENHANCED FEATURES TESTS (Future Implementation)
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.unit
class TestEnhancedSourceExtraction:
    """
    Tests for enhanced source extraction features.

    These tests document the desired behavior for future implementation:
    - Multi-tier source selector fallback
    - Domain extraction from URLs
    - Citation number assignment
    - Source deduplication
    - Enhanced filtering (internal links, login pages, etc.)
    """

    @pytest.mark.skip(reason="Enhanced features not yet implemented")
    async def test_tier1_primary_selector_success(self, mock_page):
        """Test tier1 source selector finds sources successfully."""
        sources = [
            MockElement('https://example.com/1', 'Source 1'),
            MockElement('https://example.com/2', 'Source 2'),
        ]
        mock_page.set_source_elements(sources)
        mock_page._main_text = 'Valid answer for tier1 selector testing.'

        result = await extract_search_results(mock_page, screenshot_path=None)

        assert result.success is True
        assert len(result.sources) == 2
        # Enhanced format includes domain and citation_number
        assert result.sources[0].get('domain') == 'example.com'
        assert result.sources[0].get('citation_number') == 1

    @pytest.mark.skip(reason="Enhanced features not yet implemented")
    async def test_domain_extraction(self, mock_page, basic_sources):
        """Test that domain is correctly extracted from URL."""
        mock_page.set_source_elements(basic_sources)
        mock_page._main_text = 'Valid answer for domain extraction testing.'

        result = await extract_search_results(mock_page, screenshot_path=None)

        assert result.success is True
        assert result.sources[0]['domain'] == 'example.com'
        assert result.sources[2]['domain'] == 'test.org'

    @pytest.mark.skip(reason="Enhanced features not yet implemented")
    async def test_citation_number_assignment(self, mock_page, basic_sources):
        """Test that sources are numbered sequentially starting from 1."""
        mock_page.set_source_elements(basic_sources)
        mock_page._main_text = 'Valid answer for citation numbering test.'

        result = await extract_search_results(mock_page, screenshot_path=None)

        assert result.success is True
        assert result.sources[0]['citation_number'] == 1
        assert result.sources[1]['citation_number'] == 2
        assert result.sources[2]['citation_number'] == 3

    @pytest.mark.skip(reason="Enhanced features not yet implemented")
    async def test_text_cleaning(self, mock_page):
        """Test that source text is cleaned (whitespace, newlines)."""
        sources = [
            MockElement('https://example.com/1', '  Text with   spaces  '),
            MockElement('https://example.com/2', 'Text\nwith\nnewlines'),
        ]
        mock_page.set_source_elements(sources)
        mock_page._main_text = 'Valid answer for text cleaning test.'

        result = await extract_search_results(mock_page, screenshot_path=None)

        assert result.success is True
        assert result.sources[0]['text'] == 'Text with spaces'
        assert result.sources[1]['text'] == 'Text with newlines'

    @pytest.mark.skip(reason="Enhanced features not yet implemented")
    async def test_title_extraction(self, mock_page):
        """Test that title field is populated in source metadata."""
        sources = [
            MockElement('https://example.com/article', 'Article Title - Description'),
        ]
        mock_page.set_source_elements(sources)
        mock_page._main_text = 'Valid answer for title extraction test.'

        result = await extract_search_results(mock_page, screenshot_path=None)

        assert result.success is True
        # Title should be extracted (implementation may vary)
        assert 'title' in result.sources[0]

    @pytest.mark.skip(reason="Enhanced features not yet implemented")
    async def test_duplicate_urls_removed(self, mock_page, sources_with_duplicates):
        """Test that duplicate URLs are removed, keeping first occurrence."""
        mock_page.set_source_elements(sources_with_duplicates)
        mock_page._main_text = 'Valid answer for deduplication testing.'

        result = await extract_search_results(mock_page, screenshot_path=None)

        assert result.success is True
        # Should only have 3 unique URLs (4 sources, 1 duplicate)
        assert len(result.sources) == 3
        urls = [s['url'] for s in result.sources]
        assert len(urls) == len(set(urls))  # All unique

    @pytest.mark.skip(reason="Enhanced features not yet implemented")
    async def test_deduplication_keeps_first_occurrence(self, mock_page, sources_with_duplicates):
        """Test that deduplication preserves first occurrence with its text."""
        mock_page.set_source_elements(sources_with_duplicates)
        mock_page._main_text = 'Valid answer for deduplication order testing.'

        result = await extract_search_results(mock_page, screenshot_path=None)

        assert result.success is True
        # Find the example.com entry
        example_source = next(s for s in result.sources if 'example.com' in s['url'])
        # Should keep first occurrence's text
        assert example_source['text'] == 'First occurrence'

    @pytest.mark.skip(reason="Enhanced features not yet implemented")
    async def test_deduplication_preserves_citation_numbers(self, mock_page, sources_with_duplicates):
        """Test that citation numbers remain sequential after deduplication."""
        mock_page.set_source_elements(sources_with_duplicates)
        mock_page._main_text = 'Valid answer for citation numbering after dedup.'

        result = await extract_search_results(mock_page, screenshot_path=None)

        assert result.success is True
        citation_numbers = [s['citation_number'] for s in result.sources]
        # Should be sequential: [1, 2, 3, ...]
        assert citation_numbers == list(range(1, len(result.sources) + 1))

    @pytest.mark.skip(reason="Enhanced features not yet implemented")
    async def test_external_urls_only(self, mock_page, sources_with_invalid):
        """Test that perplexity.ai internal links are filtered out."""
        mock_page.set_source_elements(sources_with_invalid)
        mock_page._main_text = 'Valid answer for external URL filtering test.'

        result = await extract_search_results(mock_page, screenshot_path=None)

        assert result.success is True
        # Should not include perplexity.ai URLs
        for source in result.sources:
            assert 'perplexity.ai' not in source['url']

    @pytest.mark.skip(reason="Enhanced features not yet implemented")
    async def test_exclude_patterns_applied(self, mock_page, sources_with_invalid):
        """Test that URLs matching exclude patterns are filtered out."""
        mock_page.set_source_elements(sources_with_invalid)
        mock_page._main_text = 'Valid answer for exclude pattern testing.'

        result = await extract_search_results(mock_page, screenshot_path=None)

        assert result.success is True
        # Should not include /login or /upgrade URLs
        for source in result.sources:
            assert '/login' not in source['url']
            assert '/upgrade' not in source['url']

    @pytest.mark.skip(reason="Enhanced features not yet implemented")
    async def test_min_text_length_enforced(self, mock_page, sources_without_text):
        """Test that sources with text < min_text_length are skipped."""
        mock_page.set_source_elements(sources_without_text)
        mock_page._main_text = 'Valid answer for minimum text length enforcement.'

        result = await extract_search_results(mock_page, screenshot_path=None)

        assert result.success is True
        # All sources should have text >= 3 chars (current minimum)
        for source in result.sources:
            assert len(source['text']) >= 3

    @pytest.mark.skip(reason="Enhanced features not yet implemented")
    async def test_invalid_urls_filtered(self, mock_page):
        """Test that malformed URLs are filtered out."""
        invalid_sources = [
            MockElement('not-a-url', 'Invalid URL'),
            MockElement('javascript:void(0)', 'JavaScript URL'),
            MockElement('https://valid.com/page', 'Valid URL'),
        ]
        mock_page.set_source_elements(invalid_sources)
        mock_page._main_text = 'Valid answer for invalid URL filtering test.'

        result = await extract_search_results(mock_page, screenshot_path=None)

        assert result.success is True
        # Should only include valid HTTP(S) URLs
        for source in result.sources:
            assert source['url'].startswith('http')

    @pytest.mark.skip(reason="Enhanced features not yet implemented")
    async def test_configurable_max_sources(self, mock_page):
        """Test that SOURCES_CONFIG['max_sources'] is respected."""
        # Create sources exceeding any reasonable limit
        many_sources = [
            MockElement(f'https://example.com/page{i}', f'Source {i}')
            for i in range(50)
        ]
        mock_page.set_source_elements(many_sources)
        mock_page._main_text = 'Valid answer for max sources configuration test.'

        with patch('src.config.SOURCES_CONFIG', {'max_sources': 5}):
            result = await extract_search_results(mock_page, screenshot_path=None)

        assert result.success is True
        # Should respect configured limit
        assert len(result.sources) <= 5

    @pytest.mark.skip(reason="Enhanced features not yet implemented")
    async def test_configurable_min_text_length(self, mock_page):
        """Test that SOURCES_CONFIG['min_text_length'] is respected."""
        sources = [
            MockElement('https://example.com/1', 'AB'),      # 2 chars
            MockElement('https://example.com/2', 'ABCDE'),   # 5 chars
            MockElement('https://example.com/3', 'ABCDEFGH'), # 8 chars
        ]
        mock_page.set_source_elements(sources)
        mock_page._main_text = 'Valid answer for min text length configuration test.'

        with patch('src.config.SOURCES_CONFIG', {'min_text_length': 5}):
            result = await extract_search_results(mock_page, screenshot_path=None)

        assert result.success is True
        # Should only include sources with text >= 5 chars
        for source in result.sources:
            assert len(source['text']) >= 5


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.skip(reason="Integration tests require real browser - MockPage cannot simulate full extraction flow")
class TestSourceExtractionIntegration:
    """Integration tests for complete source extraction flow."""

    async def test_complete_extraction_flow(self, mock_page, basic_sources):
        """Test complete extraction flow from page to result."""
        mock_page.set_source_elements(basic_sources)
        mock_page._main_text = 'This is a complete answer with sufficient content for full extraction testing.'
        screenshot_path = '/tmp/integration_test.png'

        result = await extract_search_results(mock_page, screenshot_path=screenshot_path)

        # Verify complete result structure
        assert isinstance(result, ExtractionResult)
        assert result.success is True
        assert len(result.answer_text) > 0
        assert isinstance(result.sources, list)
        assert len(result.sources) == 3
        assert result.strategy_used is not None
        assert result.extraction_time > 0
        assert result.error is None

    async def test_extraction_result_dataclass_fields(self, mock_page, basic_sources):
        """Test that ExtractionResult has all expected fields."""
        mock_page.set_source_elements(basic_sources)
        mock_page._main_text = 'Valid answer for dataclass field verification test.'

        result = await extract_search_results(mock_page, screenshot_path=None)

        # Verify all dataclass fields exist
        assert hasattr(result, 'success')
        assert hasattr(result, 'answer_text')
        assert hasattr(result, 'sources')
        assert hasattr(result, 'strategy_used')
        assert hasattr(result, 'extraction_time')
        assert hasattr(result, 'error')

    async def test_source_extraction_with_all_strategies(self, mock_page, basic_sources):
        """Test that sources are extracted regardless of answer extraction strategy."""
        mock_page.set_source_elements(basic_sources)
        # Set answer text that will be found by one of the strategies
        mock_page._main_text = '1 step completed Valid answer content ask a follow-up'

        result = await extract_search_results(mock_page, screenshot_path=None)

        assert result.success is True
        # Sources should be extracted independently of answer strategy
        assert len(result.sources) > 0


# ============================================================================
# PERFORMANCE AND STRESS TESTS
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.unit
@pytest.mark.skip(reason="Performance tests require real browser - MockPage cannot simulate full extraction flow")
class TestSourceExtractionPerformance:
    """Tests for performance and stress scenarios."""

    async def test_large_number_of_sources(self, mock_page):
        """Test extraction with a large number of source elements."""
        # Create 100 source elements
        large_sources = [
            MockElement(f'https://example{i}.com/page', f'Source {i} text content')
            for i in range(100)
        ]
        mock_page.set_source_elements(large_sources)
        mock_page._main_text = 'Valid answer for large source count performance test.'

        result = await extract_search_results(mock_page, screenshot_path=None)

        assert result.success is True
        # Should limit to reasonable number (10 by default)
        assert len(result.sources) <= 10
        # Extraction should complete reasonably fast
        assert result.extraction_time < 5.0

    async def test_very_long_source_text(self, mock_page):
        """Test extraction with very long source text."""
        long_text = 'A' * 10000  # 10KB of text
        sources = [
            MockElement('https://example.com/long', long_text),
        ]
        mock_page.set_source_elements(sources)
        mock_page._main_text = 'Valid answer for long source text handling test.'

        result = await extract_search_results(mock_page, screenshot_path=None)

        assert result.success is True
        # Should handle long text without errors
        assert len(result.sources) == 1
        assert len(result.sources[0]['text']) == 10000

    async def test_extraction_with_unicode_content(self, mock_page):
        """Test extraction with Unicode characters in source text."""
        unicode_sources = [
            MockElement('https://example.cn/article', '中文内容示例'),
            MockElement('https://example.jp/page', '日本語のコンテンツ'),
            MockElement('https://example.ru/doc', 'Русский текст'),
        ]
        mock_page.set_source_elements(unicode_sources)
        mock_page._main_text = 'Valid answer for Unicode content handling test.'

        result = await extract_search_results(mock_page, screenshot_path=None)

        assert result.success is True
        assert len(result.sources) == 3
        # Unicode should be preserved
        assert '中文' in result.sources[0]['text']
        assert '日本語' in result.sources[1]['text']
        assert 'Русский' in result.sources[2]['text']


# ============================================================================
# CONFIGURATION TESTS
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.unit
@pytest.mark.skip(reason="Configuration tests require real browser - MockPage cannot simulate full extraction flow")
class TestSourceExtractionConfiguration:
    """Tests for configuration-based source extraction behavior."""

    async def test_sources_selector_from_config(self, mock_page, basic_sources):
        """Test that source selector is read from SELECTORS config."""
        mock_page.set_source_elements(basic_sources)
        mock_page._main_text = 'Valid answer for selector configuration test.'

        # Verify SELECTORS['sources'] exists
        assert 'sources' in SELECTORS

        result = await extract_search_results(mock_page, screenshot_path=None)

        assert result.success is True
        # Sources should be extracted using configured selector
        assert len(result.sources) > 0

    async def test_extraction_with_modified_selector(self, mock_page):
        """Test extraction behavior when selector config is modified."""
        sources = [MockElement('https://example.com/1', 'Test Source')]
        mock_page.set_source_elements(sources)
        mock_page._main_text = 'Valid answer for modified selector test.'

        with patch('src.config.SELECTORS', {'sources': '[data-testid*="source"] a'}):
            result = await extract_search_results(mock_page, screenshot_path=None)

        # Should still work with patched selector
        assert isinstance(result, ExtractionResult)


# ============================================================================
# Helper Function Unit Tests (No Mock Required)
# ============================================================================

@pytest.mark.unit
class TestHelperFunctions:
    """Test helper functions in isolation without mocking."""

    def test_extract_domain_standard_url(self):
        """Test domain extraction from standard URL."""
        from src.search.extractor import _extract_domain
        domain = _extract_domain('https://www.example.com/path')
        assert domain == 'example.com'

    def test_extract_domain_no_www(self):
        """Test domain extraction without www."""
        from src.search.extractor import _extract_domain
        domain = _extract_domain('https://example.com/path')
        assert domain == 'example.com'

    def test_extract_domain_with_port(self):
        """Test domain extraction with port number."""
        from src.search.extractor import _extract_domain
        domain = _extract_domain('https://example.com:8080/path')
        assert domain == 'example.com:8080'

    def test_extract_domain_invalid_url(self):
        """Test domain extraction with invalid URL."""
        from src.search.extractor import _extract_domain
        domain = _extract_domain('not a url')
        assert domain == ''

    def test_is_excluded_url_matches_pattern(self):
        """Test URL exclusion with matching pattern."""
        from src.search.extractor import _is_excluded_url
        patterns = ['perplexity.ai', '/login']
        assert _is_excluded_url('https://perplexity.ai/search', patterns) is True
        assert _is_excluded_url('https://example.com/login', patterns) is True

    def test_is_excluded_url_no_match(self):
        """Test URL exclusion with no matching pattern."""
        from src.search.extractor import _is_excluded_url
        patterns = ['perplexity.ai', '/login']
        assert _is_excluded_url('https://example.com/article', patterns) is False

    def test_is_excluded_url_case_insensitive(self):
        """Test URL exclusion is case insensitive."""
        from src.search.extractor import _is_excluded_url
        patterns = ['perplexity.ai']
        assert _is_excluded_url('https://PERPLEXITY.AI/search', patterns) is True

    def test_is_excluded_url_empty_patterns(self):
        """Test URL exclusion with empty pattern list."""
        from src.search.extractor import _is_excluded_url
        patterns = []
        assert _is_excluded_url('https://example.com/anything', patterns) is False
