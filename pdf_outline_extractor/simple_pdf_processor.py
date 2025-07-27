"""
Simple PDF Outline Processor
For processing a single PDF file easily
"""

import json
import sys
from pathlib import Path
from universal_pdf_extractor import UniversalPDFOutlineExtractor


def process_single_pdf(pdf_path: str, output_path: str = None, debug: bool = True):
    """Process a single PDF and save results"""

    pdf_file = Path(pdf_path)

    if not pdf_file.exists():
        print(f"Error: File '{pdf_path}' not found!")
        return False

    if not pdf_file.suffix.lower() == '.pdf':
        print(f"Error: '{pdf_path}' is not a PDF file!")
        return False

    print(f"Processing: {pdf_file.name}")
    print("-" * 50)

    # Create extractor
    extractor = UniversalPDFOutlineExtractor(debug=debug)

    try:
        # Extract outline
        result = extractor.extract_outline(str(pdf_file))

        # Display results
        print(f"Title: {result['title']}")
        print(f"Method used: {result.get('method', 'unknown')}")
        print(f"Headings found: {len(result['outline'])}")

        if 'error' in result:
            print(f"Error: {result['error']}")
            return False

        if result['outline']:
            print("\nOutline:")
            print("-" * 50)
            for i, heading in enumerate(result['outline'], 1):
                indent = "  " * (int(heading['level'][1]) - 1)
                print(f"{i:2d}. {indent}{heading['level']} | Page {heading['page']} | {heading['text']}")
        else:
            print("No headings found in the document.")

        # Save results
        if output_path is None:
            output_path = pdf_file.with_suffix('.json')

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        print(f"\nResults saved to: {output_path}")
        return True

    except Exception as e:
        print(f"Error processing PDF: {str(e)}")
        return False


def main():
    """Main function with command line support"""
    if len(sys.argv) < 2:
        print("Usage: python simple_pdf_processor.py <pdf_file> [output_file]")
        print("Example: python simple_pdf_processor.py sample.pdf")
        print("Example: python simple_pdf_processor.py sample.pdf output.json")
        return

    pdf_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None

    success = process_single_pdf(pdf_path, output_path, debug=True)

    if success:
        print("\n✓ Processing completed successfully!")
    else:
        print("\n✗ Processing failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()