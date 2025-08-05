"""
Multi-Modal Content Processing System
Handles text, images, PDFs, tables, videos, and audio with intelligent analysis
"""

import asyncio
import aiohttp
import aiofiles
import logging
import mimetypes
import tempfile
import os
import re
from typing import Dict, List, Optional, Any, Union, Tuple
from urllib.parse import urlparse, urljoin
from datetime import datetime
import json
import base64

# OCR and Image Processing
try:
    import pytesseract
    from PIL import Image
    import easyocr
    TESSERACT_AVAILABLE = True
    EASYOCR_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    EASYOCR_AVAILABLE = False

# PDF Processing
try:
    import PyPDF2
    import pdfplumber
    PDF_PROCESSING_AVAILABLE = True
except ImportError:
    PDF_PROCESSING_AVAILABLE = False

# Table Processing
try:
    import pandas as pd
    from bs4 import BeautifulSoup
    import tabula
    TABLE_PROCESSING_AVAILABLE = True
except ImportError:
    TABLE_PROCESSING_AVAILABLE = False

# Video Processing
try:
    import cv2
    import moviepy.editor as mp
    VIDEO_PROCESSING_AVAILABLE = True
except ImportError:
    VIDEO_PROCESSING_AVAILABLE = False

# Audio Processing
try:
    import librosa
    import speech_recognition as sr
    AUDIO_PROCESSING_AVAILABLE = True
except ImportError:
    AUDIO_PROCESSING_AVAILABLE = False

from services.jina_ai_client import JinaAIClient
from utils.logging import LoggingMixin
from utils.exceptions import ProcessingError


class ContentAnalyzer(LoggingMixin):
    """Base class for content analyzers"""

    def __init__(self, local_llm=None):
        super().__init__()
        self.local_llm = local_llm

    async def process(self, content_url: str) -> Dict[str, Any]:
        """Process content from URL"""
        raise NotImplementedError

    async def analyze_with_llm(self, content: str, content_type: str) -> Dict[str, Any]:
        """Analyze content using local LLM"""
        if not self.local_llm:
            return {"analysis": "LLM not available"}

        try:
            prompt = f"""
            Analyze this {content_type} content and provide insights:

            Content: {content[:2000]}...

            Please provide:
            1. Summary of the content
            2. Key topics and themes
            3. Important entities (people, places, organizations)
            4. Sentiment analysis
            5. Any structured data found

            Format your response as JSON.
            """

            analysis = await self.local_llm.process_content(
                prompt,
                "content_analysis"
            )

            return {"analysis": analysis, "analyzed_at": datetime.now().isoformat()}

        except Exception as e:
            self.logger.error(f"LLM analysis failed: {e}")
            return {"analysis": f"Analysis failed: {e}", "error": True}


class TextAnalyzer(ContentAnalyzer):
    """Analyze text content with intelligent processing"""

    async def process(self, content_url: str) -> Dict[str, Any]:
        """Process text content from URL"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(content_url) as response:
                    if response.status == 200:
                        content = await response.text()

                        # Basic text analysis
                        analysis = {
                            "raw_text": content,
                            "character_count": len(content),
                            "word_count": len(content.split()),
                            "line_count": len(content.splitlines()),
                            "language": await self._detect_language(content),
                            "encoding": response.charset or "utf-8"
                        }

                        # Extract structured data
                        analysis.update(await self._extract_structured_data(content))

                        # LLM analysis
                        if self.local_llm:
                            llm_analysis = await self.analyze_with_llm(content, "text")
                            analysis["llm_analysis"] = llm_analysis

                        return analysis
                    else:
                        raise ProcessingError(f"Failed to fetch content: HTTP {response.status}")

        except Exception as e:
            self.logger.error(f"Text processing failed: {e}")
            raise ProcessingError(f"Text processing failed: {e}")

    async def _detect_language(self, text: str) -> str:
        """Detect text language (simplified implementation)"""
        # This is a simplified language detection
        # In production, use a proper language detection library
        common_english_words = ['the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by']
        words = text.lower().split()
        english_count = sum(1 for word in words if word in common_english_words)

        if len(words) > 0 and english_count / len(words) > 0.1:
            return "en"
        return "unknown"

    async def _extract_structured_data(self, text: str) -> Dict[str, Any]:
        """Extract structured data from text"""
        structured_data = {
            "emails": re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text),
            "urls": re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', text),
            "phone_numbers": re.findall(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', text),
            "dates": re.findall(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b', text),
            "numbers": re.findall(r'\b\d+\.?\d*\b', text)
        }

        return {"structured_data": structured_data}


class ImageAnalyzer(ContentAnalyzer):
    """Analyze images with OCR and visual understanding"""

    def __init__(self, local_llm=None):
        super().__init__(local_llm)
        self.ocr_reader = None
        if EASYOCR_AVAILABLE:
            try:
                self.ocr_reader = easyocr.Reader(['en'])
            except Exception as e:
                self.logger.warning(f"Failed to initialize EasyOCR: {e}")

    async def process(self, content_url: str) -> Dict[str, Any]:
        """Process image content from URL"""
        try:
            # Download image
            image_path = await self._download_image(content_url)

            try:
                # Basic image analysis
                analysis = await self._analyze_image_properties(image_path)

                # OCR text extraction
                if TESSERACT_AVAILABLE or EASYOCR_AVAILABLE:
                    ocr_results = await self._perform_ocr(image_path)
                    analysis["ocr_results"] = ocr_results

                # Visual analysis with LLM
                if self.local_llm:
                    visual_analysis = await self._analyze_image_with_llm(image_path)
                    analysis["visual_analysis"] = visual_analysis

                return analysis

            finally:
                # Clean up temporary file
                if os.path.exists(image_path):
                    os.unlink(image_path)

        except Exception as e:
            self.logger.error(f"Image processing failed: {e}")
            raise ProcessingError(f"Image processing failed: {e}")

    async def _download_image(self, image_url: str) -> str:
        """Download image to temporary file"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url) as response:
                    if response.status == 200:
                        # Create temporary file
                        suffix = os.path.splitext(urlparse(image_url).path)[1] or '.jpg'
                        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)

                        # Write image data
                        async for chunk in response.content.iter_chunked(8192):
                            temp_file.write(chunk)

                        temp_file.close()
                        return temp_file.name
                    else:
                        raise ProcessingError(f"Failed to download image: HTTP {response.status}")

        except Exception as e:
            raise ProcessingError(f"Image download failed: {e}")

    async def _analyze_image_properties(self, image_path: str) -> Dict[str, Any]:
        """Analyze basic image properties"""
        try:
            with Image.open(image_path) as img:
                return {
                    "format": img.format,
                    "mode": img.mode,
                    "size": img.size,
                    "width": img.width,
                    "height": img.height,
                    "has_transparency": img.mode in ('RGBA', 'LA') or 'transparency' in img.info,
                    "file_size": os.path.getsize(image_path)
                }
        except Exception as e:
            self.logger.error(f"Image property analysis failed: {e}")
            return {"error": f"Property analysis failed: {e}"}

    async def _perform_ocr(self, image_path: str) -> Dict[str, Any]:
        """Perform OCR on image using available engines"""
        results = {"methods_used": [], "extracted_text": "", "confidence_scores": []}

        # Try EasyOCR first (generally more accurate)
        if self.ocr_reader:
            try:
                ocr_results = self.ocr_reader.readtext(image_path)
                extracted_text = " ".join([result[1] for result in ocr_results])
                confidence_scores = [result[2] for result in ocr_results]

                results["methods_used"].append("EasyOCR")
                results["extracted_text"] = extracted_text
                results["confidence_scores"] = confidence_scores
                results["easyocr_details"] = ocr_results

            except Exception as e:
                self.logger.warning(f"EasyOCR failed: {e}")

        # Fallback to Tesseract
        if TESSERACT_AVAILABLE and not results["extracted_text"]:
            try:
                with Image.open(image_path) as img:
                    text = pytesseract.image_to_string(img)
                    confidence = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)

                    results["methods_used"].append("Tesseract")
                    results["extracted_text"] = text.strip()
                    results["tesseract_confidence"] = confidence

            except Exception as e:
                self.logger.warning(f"Tesseract OCR failed: {e}")

        return results

    async def _analyze_image_with_llm(self, image_path: str) -> Dict[str, Any]:
        """Analyze image using local LLM (if vision capabilities available)"""
        try:
            # Convert image to base64 for LLM processing
            with open(image_path, 'rb') as img_file:
                img_data = base64.b64encode(img_file.read()).decode('utf-8')

            # Note: This assumes the LLM has vision capabilities
            # In practice, you might need to use a specific vision model
            prompt = """
            Analyze this image and provide:
            1. Description of what you see
            2. Objects and people identified
            3. Text visible in the image
            4. Scene context and setting
            5. Any notable features or anomalies

            Format your response as JSON.
            """

            analysis = await self.local_llm.process_content(
                f"{prompt}\n\nImage data: data:image/jpeg;base64,{img_data[:1000]}...",
                "image_analysis"
            )

            return {"llm_analysis": analysis, "analyzed_at": datetime.now().isoformat()}

        except Exception as e:
            self.logger.error(f"LLM image analysis failed: {e}")
            return {"error": f"LLM analysis failed: {e}"}


class PDFAnalyzer(ContentAnalyzer):
    """Analyze PDF documents with text extraction and structure analysis"""

    def __init__(self, jina_config=None, jina_ai_client: Optional[JinaAIClient] = None):
        super().__init__()
        self.jina_config = jina_config or {}
        # PRIORITY: Use Jina AI Reader for PDF processing
        self.jina_ai_client = jina_ai_client

    async def process(self, content_url: str) -> Dict[str, Any]:
        """Process PDF content from URL - PRIORITIZE Jina AI Reader"""
        try:
            # PRIORITY 1: Use Jina AI Reader for PDF processing
            if self.jina_ai_client:
                self.logger.info(f"🚀 Processing PDF via Jina AI Reader: {content_url}")
                try:
                    jina_result = await self.jina_ai_client.read_url(
                        content_url,
                        options={"format": "markdown", "summary": True}
                    )

                    if jina_result.get("success"):
                        return {
                            "content_type": "pdf",
                            "source_url": content_url,
                            "processed_at": datetime.now().isoformat(),
                            "text_content": jina_result.get("content", ""),
                            "processing_method": "jina_ai_reader",
                            "source": "jina_ai_reader",
                            "success": True
                        }
                except Exception as e:
                    self.logger.warning(f"⚠️ Jina AI Reader failed for PDF, falling back: {e}")

            # FALLBACK: Local PDF processing
            self.logger.info("⚠️ Using fallback local PDF processing")

            # Download PDF
            pdf_path = await self._download_pdf(content_url)

            try:
                analysis = {
                    "content_type": "pdf",
                    "source_url": content_url,
                    "processed_at": datetime.now().isoformat(),
                    "processing_method": "local_fallback"
                }

                # Basic PDF properties
                properties = await self._analyze_pdf_properties(pdf_path)
                analysis["properties"] = properties

                # Extract text content
                if PDF_PROCESSING_AVAILABLE:
                    text_content = await self._extract_pdf_text(pdf_path)
                    analysis["text_content"] = text_content

                    # Extract tables if available
                    tables = await self._extract_pdf_tables(pdf_path)
                    if tables:
                        analysis["tables"] = tables
                if self.jina_config.get("api_key"):
                    jina_analysis = await self._analyze_with_jina(content_url)
                    analysis["jina_analysis"] = jina_analysis

                return analysis

            finally:
                # Clean up temporary file
                if os.path.exists(pdf_path):
                    os.unlink(pdf_path)

        except Exception as e:
            self.logger.error(f"PDF processing failed: {e}")
            raise ProcessingError(f"PDF processing failed: {e}")

    async def _download_pdf(self, pdf_url: str) -> str:
        """Download PDF to temporary file"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(pdf_url) as response:
                    if response.status == 200:
                        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')

                        async for chunk in response.content.iter_chunked(8192):
                            temp_file.write(chunk)

                        temp_file.close()
                        return temp_file.name
                    else:
                        raise ProcessingError(f"Failed to download PDF: HTTP {response.status}")

        except Exception as e:
            raise ProcessingError(f"PDF download failed: {e}")

    async def _analyze_pdf_properties(self, pdf_path: str) -> Dict[str, Any]:
        """Analyze basic PDF properties"""
        try:
            properties = {
                "file_size": os.path.getsize(pdf_path),
                "pages": 0,
                "metadata": {}
            }

            if PDF_PROCESSING_AVAILABLE:
                with open(pdf_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    properties["pages"] = len(pdf_reader.pages)

                    if pdf_reader.metadata:
                        properties["metadata"] = {
                            "title": pdf_reader.metadata.get('/Title', ''),
                            "author": pdf_reader.metadata.get('/Author', ''),
                            "subject": pdf_reader.metadata.get('/Subject', ''),
                            "creator": pdf_reader.metadata.get('/Creator', ''),
                            "producer": pdf_reader.metadata.get('/Producer', ''),
                            "creation_date": str(pdf_reader.metadata.get('/CreationDate', '')),
                            "modification_date": str(pdf_reader.metadata.get('/ModDate', ''))
                        }

            return properties

        except Exception as e:
            self.logger.error(f"PDF property analysis failed: {e}")
            return {"error": f"Property analysis failed: {e}"}

    async def _extract_pdf_text(self, pdf_path: str) -> Dict[str, Any]:
        """Extract text from PDF using multiple methods"""
        text_results = {
            "methods_used": [],
            "full_text": "",
            "pages": [],
            "total_characters": 0,
            "total_words": 0
        }

        # Try pdfplumber first (better for complex layouts)
        if PDF_PROCESSING_AVAILABLE:
            try:
                import pdfplumber
                with pdfplumber.open(pdf_path) as pdf:
                    pages_text = []
                    for i, page in enumerate(pdf.pages):
                        page_text = page.extract_text() or ""
                        pages_text.append({
                            "page_number": i + 1,
                            "text": page_text,
                            "character_count": len(page_text),
                            "word_count": len(page_text.split())
                        })

                    text_results["methods_used"].append("pdfplumber")
                    text_results["pages"] = pages_text
                    text_results["full_text"] = "\n\n".join([p["text"] for p in pages_text])

            except ImportError:
                pass
            except Exception as e:
                self.logger.warning(f"pdfplumber extraction failed: {e}")

        # Fallback to PyPDF2
        if not text_results["full_text"] and PDF_PROCESSING_AVAILABLE:
            try:
                with open(pdf_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    pages_text = []

                    for i, page in enumerate(pdf_reader.pages):
                        page_text = page.extract_text()
                        pages_text.append({
                            "page_number": i + 1,
                            "text": page_text,
                            "character_count": len(page_text),
                            "word_count": len(page_text.split())
                        })

                    text_results["methods_used"].append("PyPDF2")
                    text_results["pages"] = pages_text
                    text_results["full_text"] = "\n\n".join([p["text"] for p in pages_text])

            except Exception as e:
                self.logger.warning(f"PyPDF2 extraction failed: {e}")

        # Calculate totals
        text_results["total_characters"] = len(text_results["full_text"])
        text_results["total_words"] = len(text_results["full_text"].split())

        return text_results

    async def _extract_pdf_tables(self, pdf_path: str) -> List[Dict[str, Any]]:
        """Extract tables from PDF"""
        tables = []

        if TABLE_PROCESSING_AVAILABLE:
            try:
                import tabula
                # Extract tables using tabula-py
                dfs = tabula.read_pdf(pdf_path, pages='all', multiple_tables=True)

                for i, df in enumerate(dfs):
                    if not df.empty:
                        table_data = {
                            "table_number": i + 1,
                            "rows": len(df),
                            "columns": len(df.columns),
                            "headers": df.columns.tolist(),
                            "data": df.to_dict('records'),
                            "csv_data": df.to_csv(index=False)
                        }
                        tables.append(table_data)

            except ImportError:
                pass
            except Exception as e:
                self.logger.warning(f"Table extraction failed: {e}")

        return tables

    async def _analyze_with_jina(self, pdf_url: str) -> Dict[str, Any]:
        """Analyze PDF using Jina Reader API"""
        try:
            jina_endpoint = self.jina_config.get("endpoint", "https://r.jina.ai/")
            api_key = self.jina_config.get("api_key")

            headers = {}
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{jina_endpoint}{pdf_url}",
                    headers=headers
                ) as response:
                    if response.status == 200:
                        content = await response.text()
                        return {
                            "jina_content": content,
                            "processed_at": datetime.now().isoformat(),
                            "method": "jina_reader"
                        }
                    else:
                        return {"error": f"Jina API error: HTTP {response.status}"}

        except Exception as e:
            self.logger.error(f"Jina analysis failed: {e}")
            return {"error": f"Jina analysis failed: {e}"}


class TableAnalyzer(ContentAnalyzer):
    """Analyze HTML tables and structured data"""

    async def process(self, content_url: str) -> Dict[str, Any]:
        """Process table content from URL"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(content_url) as response:
                    if response.status == 200:
                        content = await response.text()

                        analysis = {
                            "content_type": "table",
                            "source_url": content_url,
                            "processed_at": datetime.now().isoformat()
                        }

                        # Parse HTML tables
                        if TABLE_PROCESSING_AVAILABLE:
                            tables = await self._extract_html_tables(content)
                            analysis["tables"] = tables

                        # LLM analysis
                        if self.local_llm:
                            llm_analysis = await self.analyze_with_llm(content[:2000], "table")
                            analysis["llm_analysis"] = llm_analysis

                        return analysis
                    else:
                        raise ProcessingError(f"Failed to fetch content: HTTP {response.status}")

        except Exception as e:
            self.logger.error(f"Table processing failed: {e}")
            raise ProcessingError(f"Table processing failed: {e}")

    async def _extract_html_tables(self, html_content: str) -> List[Dict[str, Any]]:
        """Extract tables from HTML content"""
        tables = []

        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            html_tables = soup.find_all('table')

            for i, table in enumerate(html_tables):
                # Extract headers
                headers = []
                header_row = table.find('tr')
                if header_row:
                    headers = [th.get_text(strip=True) for th in header_row.find_all(['th', 'td'])]

                # Extract rows
                rows = []
                for row in table.find_all('tr')[1:]:  # Skip header row
                    row_data = [td.get_text(strip=True) for td in row.find_all(['td', 'th'])]
                    if row_data:
                        rows.append(row_data)

                # Convert to DataFrame if pandas available
                table_data = {
                    "table_number": i + 1,
                    "headers": headers,
                    "rows": rows,
                    "row_count": len(rows),
                    "column_count": len(headers) if headers else (len(rows[0]) if rows else 0)
                }

                if TABLE_PROCESSING_AVAILABLE and headers and rows:
                    try:
                        df = pd.DataFrame(rows, columns=headers)
                        table_data["dataframe_info"] = {
                            "shape": df.shape,
                            "dtypes": df.dtypes.to_dict(),
                            "summary": df.describe().to_dict() if df.select_dtypes(include=[float, int]).shape[1] > 0 else None
                        }
                        table_data["csv_data"] = df.to_csv(index=False)
                    except Exception as e:
                        self.logger.warning(f"DataFrame conversion failed: {e}")

                tables.append(table_data)

        except Exception as e:
            self.logger.error(f"HTML table extraction failed: {e}")

        return tables


class VideoAnalyzer(ContentAnalyzer):
    """Analyze video content with metadata extraction"""

    async def process(self, content_url: str) -> Dict[str, Any]:
        """Process video content from URL"""
        try:
            analysis = {
                "content_type": "video",
                "source_url": content_url,
                "processed_at": datetime.now().isoformat()
            }

            if VIDEO_PROCESSING_AVAILABLE:
                # Download video for analysis
                video_path = await self._download_video(content_url)

                try:
                    # Extract video properties
                    properties = await self._analyze_video_properties(video_path)
                    analysis["properties"] = properties

                    # Extract frames for analysis
                    frames = await self._extract_key_frames(video_path)
                    analysis["key_frames"] = frames

                    # Extract audio if available
                    audio_analysis = await self._extract_audio_from_video(video_path)
                    if audio_analysis:
                        analysis["audio_analysis"] = audio_analysis

                finally:
                    # Clean up
                    if os.path.exists(video_path):
                        os.unlink(video_path)
            else:
                analysis["error"] = "Video processing libraries not available"

            return analysis

        except Exception as e:
            self.logger.error(f"Video processing failed: {e}")
            raise ProcessingError(f"Video processing failed: {e}")

    async def _download_video(self, video_url: str) -> str:
        """Download video to temporary file"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(video_url) as response:
                    if response.status == 200:
                        suffix = os.path.splitext(urlparse(video_url).path)[1] or '.mp4'
                        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)

                        async for chunk in response.content.iter_chunked(8192):
                            temp_file.write(chunk)

                        temp_file.close()
                        return temp_file.name
                    else:
                        raise ProcessingError(f"Failed to download video: HTTP {response.status}")

        except Exception as e:
            raise ProcessingError(f"Video download failed: {e}")

    async def _analyze_video_properties(self, video_path: str) -> Dict[str, Any]:
        """Analyze video properties using OpenCV"""
        try:
            cap = cv2.VideoCapture(video_path)

            properties = {
                "frame_count": int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
                "fps": cap.get(cv2.CAP_PROP_FPS),
                "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                "duration": int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) / cap.get(cv2.CAP_PROP_FPS),
                "file_size": os.path.getsize(video_path)
            }

            cap.release()
            return properties

        except Exception as e:
            self.logger.error(f"Video property analysis failed: {e}")
            return {"error": f"Property analysis failed: {e}"}

    async def _extract_key_frames(self, video_path: str, max_frames: int = 5) -> List[Dict[str, Any]]:
        """Extract key frames from video"""
        frames = []

        try:
            cap = cv2.VideoCapture(video_path)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

            # Extract frames at regular intervals
            interval = max(1, frame_count // max_frames)

            for i in range(0, frame_count, interval):
                cap.set(cv2.CAP_PROP_POS_FRAMES, i)
                ret, frame = cap.read()

                if ret:
                    # Save frame as temporary image
                    frame_path = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
                    cv2.imwrite(frame_path.name, frame)

                    # Encode frame as base64
                    with open(frame_path.name, 'rb') as f:
                        frame_data = base64.b64encode(f.read()).decode('utf-8')

                    frames.append({
                        "frame_number": i,
                        "timestamp": i / cap.get(cv2.CAP_PROP_FPS),
                        "base64_data": frame_data[:1000] + "...",  # Truncated for storage
                        "width": frame.shape[1],
                        "height": frame.shape[0]
                    })

                    # Clean up frame file
                    os.unlink(frame_path.name)

                    if len(frames) >= max_frames:
                        break

            cap.release()

        except Exception as e:
            self.logger.error(f"Frame extraction failed: {e}")

        return frames

    async def _extract_audio_from_video(self, video_path: str) -> Optional[Dict[str, Any]]:
        """Extract audio track from video"""
        try:
            video = mp.VideoFileClip(video_path)

            if video.audio:
                audio_path = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
                video.audio.write_audiofile(audio_path.name, verbose=False, logger=None)

                # Analyze audio properties
                audio_analysis = {
                    "duration": video.audio.duration,
                    "fps": video.audio.fps,
                    "has_audio": True,
                    "file_size": os.path.getsize(audio_path.name)
                }

                # Clean up
                os.unlink(audio_path.name)
                video.close()

                return audio_analysis
            else:
                return {"has_audio": False}

        except Exception as e:
            self.logger.error(f"Audio extraction failed: {e}")
            return {"error": f"Audio extraction failed: {e}"}


class AudioAnalyzer(ContentAnalyzer):
    """Analyze audio content with speech recognition and analysis"""

    async def process(self, content_url: str) -> Dict[str, Any]:
        """Process audio content from URL"""
        try:
            analysis = {
                "content_type": "audio",
                "source_url": content_url,
                "processed_at": datetime.now().isoformat()
            }

            if AUDIO_PROCESSING_AVAILABLE:
                # Download audio for analysis
                audio_path = await self._download_audio(content_url)

                try:
                    # Analyze audio properties
                    properties = await self._analyze_audio_properties(audio_path)
                    analysis["properties"] = properties

                    # Speech recognition
                    transcription = await self._transcribe_audio(audio_path)
                    if transcription:
                        analysis["transcription"] = transcription

                    # Audio feature analysis
                    features = await self._extract_audio_features(audio_path)
                    analysis["features"] = features

                finally:
                    # Clean up
                    if os.path.exists(audio_path):
                        os.unlink(audio_path)
            else:
                analysis["error"] = "Audio processing libraries not available"

            return analysis

        except Exception as e:
            self.logger.error(f"Audio processing failed: {e}")
            raise ProcessingError(f"Audio processing failed: {e}")

    async def _download_audio(self, audio_url: str) -> str:
        """Download audio to temporary file"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(audio_url) as response:
                    if response.status == 200:
                        suffix = os.path.splitext(urlparse(audio_url).path)[1] or '.wav'
                        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)

                        async for chunk in response.content.iter_chunked(8192):
                            temp_file.write(chunk)

                        temp_file.close()
                        return temp_file.name
                    else:
                        raise ProcessingError(f"Failed to download audio: HTTP {response.status}")

        except Exception as e:
            raise ProcessingError(f"Audio download failed: {e}")

    async def _analyze_audio_properties(self, audio_path: str) -> Dict[str, Any]:
        """Analyze audio properties using librosa"""
        try:
            y, sr = librosa.load(audio_path)

            properties = {
                "duration": len(y) / sr,
                "sample_rate": sr,
                "channels": 1 if y.ndim == 1 else y.shape[0],
                "samples": len(y),
                "file_size": os.path.getsize(audio_path),
                "rms_energy": float(librosa.feature.rms(y=y).mean()),
                "zero_crossing_rate": float(librosa.feature.zero_crossing_rate(y).mean())
            }

            return properties

        except Exception as e:
            self.logger.error(f"Audio property analysis failed: {e}")
            return {"error": f"Property analysis failed: {e}"}

    async def _transcribe_audio(self, audio_path: str) -> Optional[Dict[str, Any]]:
        """Transcribe audio using speech recognition"""
        try:
            r = sr.Recognizer()

            # Convert to WAV if needed
            wav_path = audio_path
            if not audio_path.endswith('.wav'):
                wav_path = tempfile.NamedTemporaryFile(delete=False, suffix='.wav').name
                # Convert using librosa
                y, sr_rate = librosa.load(audio_path)
                librosa.output.write_wav(wav_path, y, sr_rate)

            with sr.AudioFile(wav_path) as source:
                audio_data = r.record(source)

            # Try multiple recognition engines
            transcription_results = {}

            # Google Speech Recognition (free)
            try:
                text = r.recognize_google(audio_data)
                transcription_results["google"] = {
                    "text": text,
                    "confidence": "unknown",
                    "engine": "google"
                }
            except Exception as e:
                self.logger.debug(f"Google speech recognition failed: {e}")

            # Sphinx (offline)
            try:
                text = r.recognize_sphinx(audio_data)
                transcription_results["sphinx"] = {
                    "text": text,
                    "confidence": "unknown",
                    "engine": "sphinx"
                }
            except Exception as e:
                self.logger.debug(f"Sphinx speech recognition failed: {e}")

            # Clean up temporary WAV file
            if wav_path != audio_path and os.path.exists(wav_path):
                os.unlink(wav_path)

            if transcription_results:
                return {
                    "results": transcription_results,
                    "best_result": list(transcription_results.values())[0],
                    "transcribed_at": datetime.now().isoformat()
                }

            return None

        except Exception as e:
            self.logger.error(f"Audio transcription failed: {e}")
            return {"error": f"Transcription failed: {e}"}

    async def _extract_audio_features(self, audio_path: str) -> Dict[str, Any]:
        """Extract audio features using librosa"""
        try:
            y, sr = librosa.load(audio_path)

            features = {
                "tempo": float(librosa.beat.tempo(y=y, sr=sr)[0]),
                "spectral_centroid": float(librosa.feature.spectral_centroid(y=y, sr=sr).mean()),
                "spectral_rolloff": float(librosa.feature.spectral_rolloff(y=y, sr=sr).mean()),
                "mfcc": librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13).mean(axis=1).tolist(),
                "chroma": librosa.feature.chroma_stft(y=y, sr=sr).mean(axis=1).tolist(),
                "tonnetz": librosa.feature.tonnetz(y=y, sr=sr).mean(axis=1).tolist()
            }

            return features

        except Exception as e:
            self.logger.error(f"Audio feature extraction failed: {e}")
            return {"error": f"Feature extraction failed: {e}"}


class MultiModalProcessor(LoggingMixin):
    """
    Main multi-modal content processor that handles all content types
    """

    def __init__(self, local_llm=None, jina_config=None, jina_ai_client: Optional[JinaAIClient] = None):
        super().__init__()
        self.local_llm = local_llm
        self.jina_config = jina_config or {}
        # CRITICAL: Jina AI client for advanced processing
        self.jina_ai_client = jina_ai_client

        # Initialize content analyzers with Jina AI client
        self.content_analyzers = {
            "text": TextAnalyzer(local_llm),
            "image": ImageAnalyzer(local_llm),
            "pdf": PDFAnalyzer(jina_config, jina_ai_client=self.jina_ai_client),  # CRITICAL: Pass Jina AI client
            "table": TableAnalyzer(local_llm),
            "video": VideoAnalyzer(local_llm),
            "audio": AudioAnalyzer(local_llm)
        }

        # Content type detection patterns
        self.content_type_patterns = {
            "image": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg"],
            "pdf": [".pdf"],
            "video": [".mp4", ".avi", ".mov", ".wmv", ".flv", ".webm", ".mkv"],
            "audio": [".mp3", ".wav", ".flac", ".aac", ".ogg", ".wma"],
            "text": [".txt", ".md", ".html", ".htm", ".xml", ".json", ".csv"]
        }

        self.logger.info("MultiModalProcessor initialized")

    async def process_content(
        self,
        content_url: str,
        content_type: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process content from URL with automatic type detection

        Args:
            content_url: URL of content to process
            content_type: Optional content type override
            options: Processing options

        Returns:
            Processed content with analysis results
        """
        try:
            self.logger.info(f"Processing content: {content_url}")

            # Detect content type if not provided
            if not content_type:
                content_type = await self.detect_content_type(content_url)

            self.logger.debug(f"Detected content type: {content_type}")

            # Get appropriate analyzer
            analyzer = self.content_analyzers.get(content_type)
            if not analyzer:
                self.logger.warning(f"No analyzer for content type {content_type}, using text analyzer")
                analyzer = self.content_analyzers["text"]

            # Process content
            start_time = datetime.now()
            processed_content = await analyzer.process(content_url)
            processing_time = (datetime.now() - start_time).total_seconds()

            # Add metadata
            result = {
                "url": content_url,
                "detected_content_type": content_type,
                "processing_time_seconds": processing_time,
                "processed_at": datetime.now().isoformat(),
                "processor_version": "1.0.0",
                "content_analysis": processed_content
            }

            # Extract metadata
            metadata = await self.extract_metadata(content_url, content_type)
            result["metadata"] = metadata

            # Apply cross-modal analysis if multiple content types detected
            cross_modal_analysis = await self._perform_cross_modal_analysis(result)
            if cross_modal_analysis:
                result["cross_modal_analysis"] = cross_modal_analysis

            self.logger.info(f"Content processing completed in {processing_time:.2f}s")
            return result

        except Exception as e:
            self.logger.error(f"Content processing failed for {content_url}: {e}")
            raise ProcessingError(f"Content processing failed: {e}")

    async def detect_content_type(self, content_url: str) -> str:
        """
        Detect content type from URL and headers

        Args:
            content_url: URL to analyze

        Returns:
            Detected content type
        """
        try:
            # First, try to detect from URL extension
            parsed_url = urlparse(content_url)
            path = parsed_url.path.lower()

            for content_type, extensions in self.content_type_patterns.items():
                if any(path.endswith(ext) for ext in extensions):
                    return content_type

            # If no extension match, check MIME type from headers
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.head(content_url) as response:
                        content_type_header = response.headers.get('content-type', '').lower()

                        if 'image/' in content_type_header:
                            return "image"
                        elif 'application/pdf' in content_type_header:
                            return "pdf"
                        elif 'video/' in content_type_header:
                            return "video"
                        elif 'audio/' in content_type_header:
                            return "audio"
                        elif any(t in content_type_header for t in ['text/', 'application/json', 'application/xml']):
                            return "text"
                        elif 'text/html' in content_type_header:
                            # Check if it's primarily a table-based page
                            return await self._detect_html_content_type(content_url)

            except Exception as e:
                self.logger.debug(f"Header-based detection failed: {e}")

            # Default to text if unable to determine
            return "text"

        except Exception as e:
            self.logger.error(f"Content type detection failed: {e}")
            return "text"

    async def _detect_html_content_type(self, content_url: str) -> str:
        """Detect if HTML content is primarily table-based"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(content_url) as response:
                    if response.status == 200:
                        content = await response.text()

                        # Simple heuristic: if there are many tables relative to content
                        table_count = content.lower().count('<table')
                        total_content_length = len(content)

                        if table_count > 0 and (table_count * 1000) > total_content_length:
                            return "table"

            return "text"

        except Exception:
            return "text"

    async def extract_metadata(self, content_url: str, content_type: str) -> Dict[str, Any]:
        """
        Extract metadata from content URL

        Args:
            content_url: URL of content
            content_type: Type of content

        Returns:
            Metadata dictionary
        """
        metadata = {
            "url": content_url,
            "content_type": content_type,
            "extracted_at": datetime.now().isoformat()
        }

        try:
            # Get HTTP headers
            async with aiohttp.ClientSession() as session:
                async with session.head(content_url) as response:
                    metadata["http_status"] = response.status
                    metadata["content_length"] = response.headers.get('content-length')
                    metadata["last_modified"] = response.headers.get('last-modified')
                    metadata["etag"] = response.headers.get('etag')
                    metadata["server"] = response.headers.get('server')
                    metadata["mime_type"] = response.headers.get('content-type')

            # Parse URL components
            parsed = urlparse(content_url)
            metadata["domain"] = parsed.netloc
            metadata["path"] = parsed.path
            metadata["filename"] = os.path.basename(parsed.path)
            metadata["extension"] = os.path.splitext(parsed.path)[1]

        except Exception as e:
            self.logger.error(f"Metadata extraction failed: {e}")
            metadata["extraction_error"] = str(e)

        return metadata

    async def _perform_cross_modal_analysis(self, processing_result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Perform cross-modal analysis when multiple content types are detected
        """
        try:
            content_analysis = processing_result.get("content_analysis", {})

            # Look for embedded content of different types
            cross_modal_findings = {}

            # Check for images in text/HTML content
            if processing_result["detected_content_type"] == "text":
                text_content = content_analysis.get("raw_text", "")
                image_urls = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', text_content)
                if image_urls:
                    cross_modal_findings["embedded_images"] = image_urls[:5]  # Limit to 5

            # Check for links to other content types
            if "structured_data" in content_analysis:
                urls = content_analysis["structured_data"].get("urls", [])
                categorized_urls = {"images": [], "videos": [], "pdfs": [], "audio": []}

                for url in urls:
                    detected_type = await self.detect_content_type(url)
                    if detected_type in categorized_urls:
                        categorized_urls[detected_type].append(url)

                # Only include categories with content
                cross_modal_findings["linked_content"] = {
                    k: v for k, v in categorized_urls.items() if v
                }

            return cross_modal_findings if cross_modal_findings else None

        except Exception as e:
            self.logger.error(f"Cross-modal analysis failed: {e}")
            return None

    async def batch_process(
        self,
        content_urls: List[str],
        max_concurrent: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Process multiple content URLs concurrently

        Args:
            content_urls: List of URLs to process
            max_concurrent: Maximum concurrent processing tasks

        Returns:
            List of processing results
        """
        self.logger.info(f"Starting batch processing of {len(content_urls)} URLs")

        semaphore = asyncio.Semaphore(max_concurrent)

        async def process_single(url: str) -> Dict[str, Any]:
            async with semaphore:
                try:
                    return await self.process_content(url)
                except Exception as e:
                    self.logger.error(f"Batch processing failed for {url}: {e}")
                    return {
                        "url": url,
                        "error": str(e),
                        "processed_at": datetime.now().isoformat()
                    }

        tasks = [process_single(url) for url in content_urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle any exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "url": content_urls[i],
                    "error": str(result),
                    "processed_at": datetime.now().isoformat()
                })
            else:
                processed_results.append(result)

        self.logger.info(f"Batch processing completed: {len(processed_results)} results")
        return processed_results

    def get_supported_content_types(self) -> Dict[str, Any]:
        """Get information about supported content types"""
        return {
            "supported_types": list(self.content_analyzers.keys()),
            "file_extensions": self.content_type_patterns,
            "capabilities": {
                "text": {
                    "features": ["language_detection", "structured_data_extraction", "llm_analysis"],
                    "formats": ["txt", "html", "xml", "json", "csv", "md"]
                },
                "image": {
                    "features": ["ocr", "visual_analysis", "property_extraction"],
                    "formats": ["jpg", "png", "gif", "bmp", "webp", "svg"],
                    "ocr_available": TESSERACT_AVAILABLE or EASYOCR_AVAILABLE
                },
                "pdf": {
                    "features": ["text_extraction", "table_extraction", "metadata_extraction"],
                    "formats": ["pdf"],
                    "processing_available": PDF_PROCESSING_AVAILABLE
                },
                "table": {
                    "features": ["html_table_extraction", "dataframe_conversion", "statistical_analysis"],
                    "formats": ["html"],
                    "processing_available": TABLE_PROCESSING_AVAILABLE
                },
                "video": {
                    "features": ["metadata_extraction", "frame_extraction", "audio_extraction"],
                    "formats": ["mp4", "avi", "mov", "wmv", "flv", "webm"],
                    "processing_available": VIDEO_PROCESSING_AVAILABLE
                },
                "audio": {
                    "features": ["speech_recognition", "feature_extraction", "property_analysis"],
                    "formats": ["mp3", "wav", "flac", "aac", "ogg"],
                    "processing_available": AUDIO_PROCESSING_AVAILABLE
                }
            },
            "cross_modal_features": ["embedded_content_detection", "linked_content_analysis"]
        }