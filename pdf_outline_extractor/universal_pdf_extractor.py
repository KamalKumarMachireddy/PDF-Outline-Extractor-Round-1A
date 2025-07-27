"""
Universal PDF Outline Extractor - Fixed Version
A robust PDF outline extraction tool that works across different document types and formats.
"""

import json
import re
from typing import List, Dict, Tuple, Optional, Set
import fitz  # PyMuPDF
from collections import defaultdict, Counter
import statistics
from dataclasses import dataclass
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class TextBlock:
    """Represents a text block with formatting information"""
    text: str
    page: int
    font: str
    size: float
    flags: int
    bbox: Tuple[float, float, float, float]
    color: int = 0

    @property
    def is_bold(self) -> bool:
        return bool(self.flags & 2 ** 4)

    @property
    def is_italic(self) -> bool:
        return bool(self.flags & 2 ** 1)


class UniversalPDFOutlineExtractor:
    """Universal PDF outline extractor with multiple detection strategies"""

    def __init__(self, debug: bool = False):
        self.debug = debug

        # Comprehensive heading patterns for different document types
        self.heading_patterns = [
            # Numbered sections
            r'^\d+\.\s+[A-Za-z]',  # 1. Introduction
            r'^\d+\.\d+\s+[A-Za-z]',  # 1.1 Overview
            r'^\d+\.\d+\.\d+\s+[A-Za-z]',  # 1.1.1 Details
            r'^\d+\s+[A-Z][A-Za-z\s]+',  # 1 INTRODUCTION

            # Chapter patterns
            r'^Chapter\s+\d+',  # Chapter 1
            r'^CHAPTER\s+\d+',  # CHAPTER 1
            r'^Ch\.\s*\d+',  # Ch. 1

            # Roman numerals
            r'^[IVX]+\.\s+[A-Za-z]',  # I. Introduction
            r'^[IVX]+\s+[A-Z][A-Za-z\s]+',  # I INTRODUCTION

            # Letter patterns
            r'^[A-Z]\.\s+[A-Za-z]',  # A. Introduction
            r'^[A-Z]\)\s+[A-Za-z]',  # A) Introduction

            # Academic patterns
            r'^Abstract\s*$',  # Abstract
            r'^Introduction\s*$',  # Introduction
            r'^Conclusion\s*$',  # Conclusion
            r'^References\s*$',  # References
            r'^Bibliography\s*$',  # Bibliography
            r'^Methodology\s*$',  # Methodology
            r'^Results\s*$',  # Results
            r'^Discussion\s*$',  # Discussion
            r'^Summary\s*$',  # Summary
            r'^Background\s*$',  # Background
            r'^Literature Review\s*$',  # Literature Review

            # Business document patterns
            r'^Executive Summary\s*$',  # Executive Summary
            r'^Overview\s*$',  # Overview
            r'^Objectives\s*$',  # Objectives
            r'^Goals\s*$',  # Goals
            r'^Strategy\s*$',  # Strategy
            r'^Implementation\s*$',  # Implementation

            # Technical document patterns
            r'^Requirements\s*$',  # Requirements
            r'^Specifications\s*$',  # Specifications
            r'^Architecture\s*$',  # Architecture
            r'^Design\s*$',  # Design
            r'^Testing\s*$',  # Testing
            r'^Deployment\s*$',  # Deployment

            # General patterns
            r'^[A-Z][A-Z\s]{4,20}$',  # ALL CAPS titles
            r'^[A-Z][a-z]+(\s+[A-Z][a-z]+)*:?\s*$',  # Title Case
        ]

        # Words that typically indicate body text, not headings
        self.body_text_indicators = {
            'the', 'this', 'that', 'these', 'those', 'within', 'embedded',
            'useful', 'designed', 'can', 'will', 'should', 'would', 'could',
            'may', 'might', 'must', 'shall', 'during', 'through', 'between',
            'among', 'including', 'such', 'example', 'however', 'therefore',
            'furthermore', 'moreover', 'additionally', 'consequently'
        }

        # Common false positive patterns
        self.false_positives = {
            'page', 'figure', 'table', 'note', 'see', 'www', 'http', 'https',
            'copyright', 'rights reserved', 'inc', 'ltd', 'corp', 'pdf',
            'document', 'file', 'email', '@', '.com', '.org', '.edu'
        }

    def extract_outline(self, pdf_path: str) -> Dict:
        """Main method to extract outline from PDF"""
        try:
            if self.debug:
                logger.info(f"Processing PDF: {pdf_path}")

            doc = fitz.open(pdf_path)

            # Strategy 1: Try existing outline/bookmarks first
            existing_outline = self._extract_existing_outline(doc)
            if existing_outline and len(existing_outline) > 2:
                title = self._extract_title(doc)
                doc.close()
                if self.debug:
                    logger.info("Used existing PDF outline")
                return {
                    "title": title,
                    "outline": existing_outline,
                    "method": "existing_outline"
                }

            # Strategy 2: Analyze document structure
            text_blocks = self._extract_text_blocks(doc)
            title = self._extract_title_from_blocks(text_blocks)

            # Try multiple detection strategies
            outline = self._multi_strategy_detection(text_blocks)

            doc.close()

            return {
                "title": title,
                "outline": outline,
                "method": "structure_analysis"
            }

        except Exception as e:
            logger.error(f"Error extracting outline: {str(e)}")
            return {
                "title": "Error extracting title",
                "outline": [],
                "error": str(e)
            }

    def _extract_existing_outline(self, doc) -> List[Dict]:
        """Extract existing PDF outline/bookmarks"""
        outline = []
        try:
            toc = doc.get_toc()

            if not toc:
                return []

            for item in toc:
                level, title, page = item
                # Convert level to H1, H2, H3 format (cap at H3)
                heading_level = f"H{min(level, 3)}"
                outline.append({
                    "level": heading_level,
                    "text": title.strip(),
                    "page": page
                })

            return outline
        except Exception as e:
            if self.debug:
                logger.warning(f"Could not extract existing outline: {e}")
            return []

    def _extract_text_blocks(self, doc) -> List[TextBlock]:
        """Extract text blocks with comprehensive formatting information"""
        blocks = []

        for page_num in range(min(len(doc), 50)):  # Limit to 50 pages for performance
            page = doc[page_num]
            try:
                text_dict = page.get_text("dict")

                for block in text_dict.get("blocks", []):
                    if "lines" in block:
                        for line in block["lines"]:
                            for span in line["spans"]:
                                text = span["text"].strip()
                                if text and len(text) > 1:
                                    blocks.append(TextBlock(
                                        text=text,
                                        page=page_num + 1,
                                        font=span.get("font", ""),
                                        size=span.get("size", 0),
                                        flags=span.get("flags", 0),
                                        bbox=span.get("bbox", (0, 0, 0, 0)),
                                        color=span.get("color", 0)
                                    ))
            except Exception as e:
                if self.debug:
                    logger.warning(f"Error processing page {page_num + 1}: {e}")
                continue

        return blocks

    def _extract_title(self, doc) -> str:
        """Extract document title from first page"""
        if len(doc) == 0:
            return "Untitled Document"

        try:
            page = doc[0]
            text_dict = page.get_text("dict")

            # Look for largest text on first page
            largest_size = 0
            title_candidates = []

            for block in text_dict.get("blocks", []):
                if "lines" in block:
                    for line in block["lines"]:
                        for span in line["spans"]:
                            text = span["text"].strip()
                            size = span.get("size", 0)

                            if text and 5 <= len(text) <= 100 and size > largest_size:
                                largest_size = size
                                title_candidates = [text]
                            elif text and 5 <= len(text) <= 100 and size == largest_size:
                                title_candidates.append(text)

            if title_candidates:
                # Filter out common non-title patterns
                filtered_candidates = []
                for candidate in title_candidates:
                    if not any(fp in candidate.lower() for fp in self.false_positives):
                        filtered_candidates.append(candidate)

                if filtered_candidates:
                    # Return shortest clean candidate
                    return min(filtered_candidates, key=len)
                else:
                    # Fallback to original candidates
                    return min(title_candidates, key=len)

        except Exception as e:
            if self.debug:
                logger.warning(f"Error extracting title: {e}")

        return "Untitled Document"

    def _extract_title_from_blocks(self, blocks: List[TextBlock]) -> str:
        """Extract title from text blocks"""
        if not blocks:
            return "Untitled Document"

        # Get blocks from first page
        first_page_blocks = [b for b in blocks if b.page == 1]

        if not first_page_blocks:
            return "Untitled Document"

        # Find largest font size on first page
        max_size = max(block.size for block in first_page_blocks)

        # Get text with largest font size
        title_candidates = []
        for block in first_page_blocks:
            if (block.size == max_size and
                    5 <= len(block.text) <= 100 and
                    not self._is_likely_body_text(block.text) and
                    not any(fp in block.text.lower() for fp in self.false_positives)):
                title_candidates.append(block.text)

        if title_candidates:
            # Return shortest, cleanest title
            return min(title_candidates, key=len)

        return "Untitled Document"

    def _multi_strategy_detection(self, blocks: List[TextBlock]) -> List[Dict]:
        """Use multiple strategies to detect headings"""
        if not blocks:
            return []

        # Strategy 1: Pattern-based detection (highest confidence)
        pattern_headings = self._pattern_based_detection(blocks)

        # Strategy 2: Font-based detection
        font_headings = self._font_based_detection(blocks)

        # Strategy 3: Position-based detection
        position_headings = self._position_based_detection(blocks)

        # Combine and rank results
        all_headings = self._combine_strategies(pattern_headings, font_headings, position_headings)

        # Filter and clean
        filtered_headings = self._intelligent_filter(all_headings, blocks)

        # Sort by page and position
        filtered_headings.sort(key=lambda x: (x["page"], x.get("position", 0)))

        if self.debug:
            logger.info(f"Found {len(filtered_headings)} headings using multi-strategy detection")

        return filtered_headings

    def _pattern_based_detection(self, blocks: List[TextBlock]) -> List[Dict]:
        """Detect headings based on text patterns"""
        headings = []

        for block in blocks:
            text = block.text.strip()

            # Skip if too short or too long
            if len(text) < 2 or len(text) > 200:
                continue

            # Check against all patterns
            for pattern in self.heading_patterns:
                if re.match(pattern, text, re.IGNORECASE):
                    level = self._determine_pattern_level(text, pattern)
                    headings.append({
                        "level": level,
                        "text": text,
                        "page": block.page,
                        "confidence": 0.9,  # High confidence for pattern matches
                        "strategy": "pattern",
                        "size": block.size,
                        "position": block.bbox[1] if block.bbox else 0  # Y coordinate
                    })
                    break

        return headings

    def _font_based_detection(self, blocks: List[TextBlock]) -> List[Dict]:
        """Detect headings based on font characteristics"""
        if not blocks:
            return []

        headings = []

        # Calculate font statistics
        font_sizes = [block.size for block in blocks if block.size > 0]
        if not font_sizes:
            return []

        avg_size = statistics.mean(font_sizes)
        size_threshold_low = avg_size * 1.1
        size_threshold_high = avg_size * 1.3

        for block in blocks:
            text = block.text.strip()

            # Skip if inappropriate length
            if len(text) < 3 or len(text) > 150:
                continue

            # Skip obvious body text
            if self._is_likely_body_text(text):
                continue

            # Font-based criteria
            is_large = block.size > size_threshold_low
            is_very_large = block.size > size_threshold_high
            is_bold = block.is_bold

            confidence = 0.0
            level = "H3"

            if is_very_large and is_bold:
                confidence = 0.8
                level = "H1"
            elif is_very_large:
                confidence = 0.7
                level = "H2"
            elif is_large and is_bold:
                confidence = 0.6
                level = "H2"
            elif is_large:
                confidence = 0.5
                level = "H3"
            elif is_bold and len(text) < 50:
                confidence = 0.4
                level = "H3"

            if confidence > 0.4:  # Only include if reasonable confidence
                headings.append({
                    "level": level,
                    "text": text,
                    "page": block.page,
                    "confidence": confidence,
                    "strategy": "font",
                    "size": block.size,
                    "position": block.bbox[1] if block.bbox else 0
                })

        return headings

    def _position_based_detection(self, blocks: List[TextBlock]) -> List[Dict]:
        """Detect headings based on position and spacing"""
        headings = []

        # Group blocks by page
        pages = defaultdict(list)
        for block in blocks:
            pages[block.page].append(block)

        for page_num, page_blocks in pages.items():
            # Sort by vertical position
            page_blocks.sort(key=lambda b: b.bbox[1] if b.bbox else 0)

            # Look for isolated text (potential headings)
            for i, block in enumerate(page_blocks):
                text = block.text.strip()

                if len(text) < 3 or len(text) > 100:
                    continue

                if self._is_likely_body_text(text):
                    continue

                # Check if text is isolated (has space above and below)
                has_space_above = i == 0 or self._has_vertical_gap(page_blocks[i - 1], block)
                has_space_below = i == len(page_blocks) - 1 or self._has_vertical_gap(block, page_blocks[i + 1])

                if has_space_above and has_space_below and len(text) < 80:
                    headings.append({
                        "level": "H3",
                        "text": text,
                        "page": block.page,
                        "confidence": 0.3,
                        "strategy": "position",
                        "size": block.size,
                        "position": block.bbox[1] if block.bbox else 0
                    })

        return headings

    def _combine_strategies(self, *strategy_results) -> List[Dict]:
        """Combine results from multiple strategies"""
        all_headings = []
        seen = set()

        # Flatten all results
        for strategy_headings in strategy_results:
            for heading in strategy_headings:
                # Create a key to identify duplicates
                key = (heading["text"].lower().strip(), heading["page"])

                if key not in seen:
                    seen.add(key)
                    all_headings.append(heading)
                else:
                    # If we've seen this heading, keep the one with higher confidence
                    for i, existing in enumerate(all_headings):
                        existing_key = (existing["text"].lower().strip(), existing["page"])
                        if existing_key == key:
                            if heading["confidence"] > existing["confidence"]:
                                all_headings[i] = heading
                            break

        return all_headings

    def _intelligent_filter(self, headings: List[Dict], all_blocks: List[TextBlock]) -> List[Dict]:
        """Intelligent filtering to remove false positives"""
        if not headings:
            return []

        # Sort by confidence
        headings.sort(key=lambda x: x["confidence"], reverse=True)

        filtered = []
        for heading in headings:
            text = heading["text"].strip()

            # Basic filters
            if len(text) < 2 or len(text) > 200:
                continue

            if any(fp in text.lower() for fp in self.false_positives):
                continue

            if self._is_likely_body_text(text):
                continue

            # Check if it's likely a real heading based on context
            if self._is_contextually_valid_heading(heading, all_blocks):
                # Clean up the heading level and format
                clean_heading = {
                    "level": heading["level"],
                    "text": text,
                    "page": heading["page"]
                }
                filtered.append(clean_heading)

        return filtered

    def _determine_pattern_level(self, text: str, pattern: str) -> str:
        """Determine heading level based on matched pattern"""
        text_lower = text.lower()

        # Numbered patterns
        if re.match(r'^\d+\.\s+', text):
            return "H1"
        elif re.match(r'^\d+\.\d+\s+', text):
            return "H2"
        elif re.match(r'^\d+\.\d+\.\d+\s+', text):
            return "H3"

        # Chapter patterns
        if any(word in text_lower for word in ['chapter', 'ch.']):
            return "H1"

        # Major sections
        if any(word in text_lower for word in ['abstract', 'introduction', 'conclusion', 'references', 'bibliography']):
            return "H1"

        # Default
        return "H2"

    def _is_likely_body_text(self, text: str) -> bool:
        """Check if text is likely body text rather than a heading"""
        text_lower = text.lower()
        words = text_lower.split()

        if len(words) == 0:
            return True

        # Check for body text indicators
        body_word_count = sum(1 for word in words if word in self.body_text_indicators)
        body_ratio = body_word_count / len(words)

        # High ratio of body text words = likely body text
        if body_ratio > 0.4:
            return True

        # Very long text is likely body text
        if len(text) > 150:
            return True

        # Contains sentence-ending punctuation = likely body text
        if text.count('.') > 1 or text.count(',') > 2:
            return True

        return False

    def _has_vertical_gap(self, block1: TextBlock, block2: TextBlock) -> bool:
        """Check if there's a significant vertical gap between two blocks"""
        if not block1.bbox or not block2.bbox:
            return False

        gap = abs(block1.bbox[1] - block2.bbox[3])  # Gap between bottom of first and top of second
        return gap > 10  # Arbitrary threshold

    def _is_contextually_valid_heading(self, heading: Dict, all_blocks: List[TextBlock]) -> bool:
        """Check if a heading is contextually valid"""
        # For now, accept all headings that passed other filters
        # This could be expanded with more sophisticated context analysis
        return True


def main():
    """Example usage with different PDF types"""
    extractor = UniversalPDFOutlineExtractor(debug=True)

    # Test with multiple PDFs
    test_files = [
        "test.pdf"  # Your test file
    ]

    for pdf_path in test_files:
        try:
            print(f"\n{'=' * 60}")
            print(f"Processing: {pdf_path}")
            print('=' * 60)

            result = extractor.extract_outline(pdf_path)

            print(f"Title: {result['title']}")
            print(f"Method used: {result.get('method', 'unknown')}")
            print(f"Headings found: {len(result['outline'])}")

            if result['outline']:
                print("\nOutline:")
                for i, heading in enumerate(result['outline'], 1):
                    print(f"{i:2d}. {heading['level']} | Page {heading['page']} | {heading['text']}")
            else:
                print("No headings found")

            # Save individual results
            output_file = f"{pdf_path.replace('.pdf', '')}_outline.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"Results saved to: {output_file}")

        except FileNotFoundError:
            print(f"File not found: {pdf_path}")
        except Exception as e:
            print(f"Error processing {pdf_path}: {str(e)}")


if __name__ == "__main__":
    main()