"""
Tests for Multi-Modal Content Processing System
"""

import pytest
import asyncio
import tempfile
import os
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

from features.multimodal_processing import (
    MultiModalProcessor, TextAnalyzer, ImageAnalyzer, PDFAnalyzer,
    TableAnalyzer, VideoAnalyzer, AudioAnalyzer, ContentAnalyzer
)
from utils.exceptions import ProcessingError


class TestContentAnalyzer:
    """Test base ContentAnalyzer class"""
    
    def test_initialization(self):
        """Test analyzer initialization"""
        analyzer = ContentAnalyzer()
        assert analyzer.local_llm is None
        
        mock_llm = Mock()
        analyzer_with_llm = ContentAnalyzer(mock_llm)
        assert analyzer_with_llm.local_llm == mock_llm
    
    async def test_analyze_with_llm_no_llm(self):
        """Test LLM analysis when no LLM available"""
        analyzer = ContentAnalyzer()
        result = await analyzer.analyze_with_llm("test content", "text")
        assert result["analysis"] == "LLM not available"
    
    async def test_analyze_with_llm_success(self):
        """Test successful LLM analysis"""
        mock_llm = AsyncMock()
        mock_llm.process_content.return_value = "Analysis result"
        
        analyzer = ContentAnalyzer(mock_llm)
        result = await analyzer.analyze_with_llm("test content", "text")
        
        assert result["analysis"] == "Analysis result"
        assert "analyzed_at" in result
        mock_llm.process_content.assert_called_once()


class TestTextAnalyzer:
    """Test TextAnalyzer class"""
    
    @pytest.fixture
    def text_analyzer(self):
        return TextAnalyzer()
    
    @patch('aiohttp.ClientSession.get')
    async def test_process_success(self, mock_get, text_analyzer):
        """Test successful text processing"""
        # Mock HTTP response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text.return_value = "This is test content with email@example.com"
        mock_response.charset = "utf-8"
        mock_get.return_value.__aenter__.return_value = mock_response
        
        result = await text_analyzer.process("http://example.com/text.txt")
        
        assert result["raw_text"] == "This is test content with email@example.com"
        assert result["character_count"] == 44
        assert result["word_count"] == 7
        assert result["language"] == "en"
        assert "structured_data" in result
        assert "email@example.com" in result["structured_data"]["emails"]
    
    @patch('aiohttp.ClientSession.get')
    async def test_process_http_error(self, mock_get, text_analyzer):
        """Test text processing with HTTP error"""
        mock_response = AsyncMock()
        mock_response.status = 404
        mock_get.return_value.__aenter__.return_value = mock_response
        
        with pytest.raises(ProcessingError):
            await text_analyzer.process("http://example.com/notfound.txt")
    
    async def test_detect_language(self, text_analyzer):
        """Test language detection"""
        english_text = "The quick brown fox jumps over the lazy dog"
        result = await text_analyzer._detect_language(english_text)
        assert result == "en"
        
        unknown_text = "xyz abc def"
        result = await text_analyzer._detect_language(unknown_text)
        assert result == "unknown"
    
    async def test_extract_structured_data(self, text_analyzer):
        """Test structured data extraction"""
        text = """
        Contact us at info@example.com or call 555-123-4567.
        Visit our website at https://example.com
        Meeting on 12/25/2023 at 2:30 PM.
        Price: $99.99
        """
        
        result = await text_analyzer._extract_structured_data(text)
        structured = result["structured_data"]
        
        assert "info@example.com" in structured["emails"]
        assert "https://example.com" in structured["urls"]
        assert "555-123-4567" in structured["phone_numbers"]
        assert "12/25/2023" in structured["dates"]


class TestImageAnalyzer:
    """Test ImageAnalyzer class"""
    
    @pytest.fixture
    def image_analyzer(self):
        return ImageAnalyzer()
    
    @patch('features.multimodal_processing.Image.open')
    @patch('aiohttp.ClientSession.get')
    async def test_process_success(self, mock_get, mock_image_open, image_analyzer):
        """Test successful image processing"""
        # Mock HTTP response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.content.iter_chunked.return_value = [b'fake_image_data']
        mock_get.return_value.__aenter__.return_value = mock_response
        
        # Mock PIL Image
        mock_img = Mock()
        mock_img.format = "JPEG"
        mock_img.mode = "RGB"
        mock_img.size = (800, 600)
        mock_img.width = 800
        mock_img.height = 600
        mock_image_open.return_value.__enter__.return_value = mock_img
        
        with patch('os.path.getsize', return_value=1024):
            with patch('os.path.exists', return_value=True):
                with patch('os.unlink'):
                    result = await image_analyzer.process("http://example.com/image.jpg")
        
        assert result["format"] == "JPEG"
        assert result["width"] == 800
        assert result["height"] == 600
    
    async def test_download_image_success(self, image_analyzer):
        """Test successful image download"""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.content.iter_chunked.return_value = [b'fake_image_data']
            mock_get.return_value.__aenter__.return_value = mock_response
            
            with patch('tempfile.NamedTemporaryFile') as mock_temp:
                mock_file = Mock()
                mock_file.name = "/tmp/test_image.jpg"
                mock_temp.return_value = mock_file
                
                result = await image_analyzer._download_image("http://example.com/image.jpg")
                assert result == "/tmp/test_image.jpg"
    
    async def test_download_image_failure(self, image_analyzer):
        """Test image download failure"""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 404
            mock_get.return_value.__aenter__.return_value = mock_response
            
            with pytest.raises(ProcessingError):
                await image_analyzer._download_image("http://example.com/notfound.jpg")


class TestPDFAnalyzer:
    """Test PDFAnalyzer class"""
    
    @pytest.fixture
    def pdf_analyzer(self):
        return PDFAnalyzer()
    
    @patch('aiohttp.ClientSession.get')
    async def test_process_success(self, mock_get, pdf_analyzer):
        """Test successful PDF processing"""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.content.iter_chunked.return_value = [b'fake_pdf_data']
        mock_get.return_value.__aenter__.return_value = mock_response
        
        with patch('tempfile.NamedTemporaryFile') as mock_temp:
            mock_file = Mock()
            mock_file.name = "/tmp/test.pdf"
            mock_temp.return_value = mock_file
            
            with patch.object(pdf_analyzer, '_analyze_pdf_properties') as mock_props:
                mock_props.return_value = {"pages": 5, "file_size": 1024}
                
                with patch('os.path.exists', return_value=True):
                    with patch('os.unlink'):
                        result = await pdf_analyzer.process("http://example.com/doc.pdf")
        
        assert result["content_type"] == "pdf"
        assert "properties" in result
        assert "processed_at" in result
    
    async def test_analyze_pdf_properties(self, pdf_analyzer):
        """Test PDF properties analysis"""
        with patch('os.path.getsize', return_value=2048):
            with patch('features.multimodal_processing.PDF_PROCESSING_AVAILABLE', True):
                with patch('PyPDF2.PdfReader') as mock_reader:
                    mock_pdf = Mock()
                    mock_pdf.pages = [Mock(), Mock(), Mock()]  # 3 pages
                    mock_pdf.metadata = {
                        '/Title': 'Test Document',
                        '/Author': 'Test Author'
                    }
                    mock_reader.return_value = mock_pdf
                    
                    with patch('builtins.open', mock_open()):
                        result = await pdf_analyzer._analyze_pdf_properties("/fake/path.pdf")
                    
                    assert result["pages"] == 3
                    assert result["file_size"] == 2048
                    assert result["metadata"]["title"] == "Test Document"


class TestMultiModalProcessor:
    """Test main MultiModalProcessor class"""
    
    @pytest.fixture
    def processor(self):
        return MultiModalProcessor()
    
    def test_initialization(self, processor):
        """Test processor initialization"""
        assert len(processor.content_analyzers) == 6
        assert "text" in processor.content_analyzers
        assert "image" in processor.content_analyzers
        assert "pdf" in processor.content_analyzers
        assert "table" in processor.content_analyzers
        assert "video" in processor.content_analyzers
        assert "audio" in processor.content_analyzers
    
    async def test_detect_content_type_from_extension(self, processor):
        """Test content type detection from file extension"""
        assert await processor.detect_content_type("http://example.com/image.jpg") == "image"
        assert await processor.detect_content_type("http://example.com/doc.pdf") == "pdf"
        assert await processor.detect_content_type("http://example.com/video.mp4") == "video"
        assert await processor.detect_content_type("http://example.com/audio.mp3") == "audio"
        assert await processor.detect_content_type("http://example.com/text.txt") == "text"
    
    @patch('aiohttp.ClientSession.head')
    async def test_detect_content_type_from_headers(self, mock_head, processor):
        """Test content type detection from HTTP headers"""
        mock_response = AsyncMock()
        mock_response.headers = {'content-type': 'image/jpeg'}
        mock_head.return_value.__aenter__.return_value = mock_response
        
        result = await processor.detect_content_type("http://example.com/unknown")
        assert result == "image"
    
    async def test_detect_content_type_fallback(self, processor):
        """Test content type detection fallback to text"""
        with patch('aiohttp.ClientSession.head', side_effect=Exception("Network error")):
            result = await processor.detect_content_type("http://example.com/unknown")
            assert result == "text"
    
    @patch.object(MultiModalProcessor, 'detect_content_type')
    async def test_process_content_success(self, mock_detect, processor):
        """Test successful content processing"""
        mock_detect.return_value = "text"
        
        # Mock the text analyzer
        mock_analyzer = AsyncMock()
        mock_analyzer.process.return_value = {"raw_text": "test content"}
        processor.content_analyzers["text"] = mock_analyzer
        
        with patch.object(processor, 'extract_metadata') as mock_metadata:
            mock_metadata.return_value = {"url": "http://example.com"}
            
            result = await processor.process_content("http://example.com/test.txt")
        
        assert result["url"] == "http://example.com/test.txt"
        assert result["detected_content_type"] == "text"
        assert "processing_time_seconds" in result
        assert "content_analysis" in result
        mock_analyzer.process.assert_called_once()
    
    async def test_extract_metadata(self, processor):
        """Test metadata extraction"""
        with patch('aiohttp.ClientSession.head') as mock_head:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.headers = {
                'content-length': '1024',
                'content-type': 'text/html',
                'server': 'nginx'
            }
            mock_head.return_value.__aenter__.return_value = mock_response
            
            result = await processor.extract_metadata("http://example.com/test.html", "text")
        
        assert result["url"] == "http://example.com/test.html"
        assert result["content_type"] == "text"
        assert result["http_status"] == 200
        assert result["domain"] == "example.com"
        assert result["filename"] == "test.html"
    
    async def test_batch_process(self, processor):
        """Test batch processing of multiple URLs"""
        urls = [
            "http://example.com/1.txt",
            "http://example.com/2.txt",
            "http://example.com/3.txt"
        ]
        
        with patch.object(processor, 'process_content') as mock_process:
            mock_process.side_effect = [
                {"url": urls[0], "result": "success"},
                {"url": urls[1], "result": "success"},
                Exception("Processing failed")
            ]
            
            results = await processor.batch_process(urls, max_concurrent=2)
        
        assert len(results) == 3
        assert results[0]["result"] == "success"
        assert results[1]["result"] == "success"
        assert "error" in results[2]
    
    def test_get_supported_content_types(self, processor):
        """Test getting supported content types information"""
        info = processor.get_supported_content_types()
        
        assert "supported_types" in info
        assert "file_extensions" in info
        assert "capabilities" in info
        assert "cross_modal_features" in info
        
        assert len(info["supported_types"]) == 6
        assert "text" in info["capabilities"]
        assert "image" in info["capabilities"]


@pytest.mark.asyncio
class TestMultiModalIntegration:
    """Integration tests for multi-modal processing"""
    
    async def test_end_to_end_text_processing(self):
        """Test complete text processing workflow"""
        processor = MultiModalProcessor()
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.text.return_value = "Test content"
            mock_response.charset = "utf-8"
            mock_get.return_value.__aenter__.return_value = mock_response
            
            with patch('aiohttp.ClientSession.head') as mock_head:
                mock_head_response = AsyncMock()
                mock_head_response.status = 200
                mock_head_response.headers = {'content-type': 'text/plain'}
                mock_head.return_value.__aenter__.return_value = mock_head_response
                
                result = await processor.process_content("http://example.com/test.txt")
        
        assert result["detected_content_type"] == "text"
        assert result["content_analysis"]["raw_text"] == "Test content"
        assert "metadata" in result
    
    async def test_cross_modal_analysis(self):
        """Test cross-modal content analysis"""
        processor = MultiModalProcessor()
        
        # Mock processing result with embedded images
        processing_result = {
            "detected_content_type": "text",
            "content_analysis": {
                "raw_text": '<img src="http://example.com/image1.jpg"> <img src="http://example.com/image2.png">',
                "structured_data": {
                    "urls": ["http://example.com/video.mp4", "http://example.com/doc.pdf"]
                }
            }
        }
        
        with patch.object(processor, 'detect_content_type') as mock_detect:
            mock_detect.side_effect = ["video", "pdf"]
            
            result = await processor._perform_cross_modal_analysis(processing_result)
        
        assert "embedded_images" in result
        assert "linked_content" in result
        assert len(result["embedded_images"]) == 2
        assert "videos" in result["linked_content"]
        assert "pdfs" in result["linked_content"]


def mock_open(mock=None, read_data=''):
    """Helper function to create mock file objects"""
    if mock is None:
        mock = MagicMock(spec=open)
    
    handle = MagicMock(spec=open)
    handle.read.return_value = read_data
    handle.__enter__.return_value = handle
    mock.return_value = handle
    return mock
