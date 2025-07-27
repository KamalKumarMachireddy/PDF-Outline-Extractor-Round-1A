"""
Batch PDF Outline Processor - Fixed Version
Process multiple PDFs and generate comprehensive reports
"""

import os
import json
import time
from pathlib import Path
from typing import List, Dict
import argparse
from universal_pdf_extractor import UniversalPDFOutlineExtractor


class BatchPDFProcessor:
    """Process multiple PDFs and generate reports"""

    def __init__(self, input_dir: str = ".", output_dir: str = "output", debug: bool = False):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.debug = debug
        self.extractor = UniversalPDFOutlineExtractor(debug=debug)

        # Create output directory
        self.output_dir.mkdir(exist_ok=True)

    def find_pdf_files(self) -> List[Path]:
        """Find all PDF files in input directory"""
        pdf_files = list(self.input_dir.glob("*.pdf"))
        if self.debug:
            print(f"Found {len(pdf_files)} PDF files in {self.input_dir}")
        return pdf_files

    def process_single_pdf(self, pdf_path: Path) -> Dict:
        """Process a single PDF file"""
        try:
            start_time = time.time()
            result = self.extractor.extract_outline(str(pdf_path))
            processing_time = time.time() - start_time

            # Add metadata
            result['metadata'] = {
                'filename': pdf_path.name,
                'file_size': pdf_path.stat().st_size,
                'processing_time': round(processing_time, 2),
                'success': 'error' not in result
            }

            return result

        except Exception as e:
            return {
                'title': 'Error',
                'outline': [],
                'error': str(e),
                'metadata': {
                    'filename': pdf_path.name,
                    'file_size': pdf_path.stat().st_size if pdf_path.exists() else 0,
                    'processing_time': 0,
                    'success': False
                }
            }

    def process_all_pdfs(self) -> Dict:
        """Process all PDFs and return comprehensive results"""
        pdf_files = self.find_pdf_files()

        # Initialize summary with default values
        summary = {
            'total_files': len(pdf_files),
            'successful': 0,
            'failed': 0,
            'total_headings_found': 0,
            'average_headings_per_document': 0.0,
            'processing_date': time.strftime('%Y-%m-%d %H:%M:%S')
        }

        if not pdf_files:
            print("No PDF files found!")
            return {'results': [], 'summary': summary}

        results = []
        success_count = 0
        total_headings = 0

        print(f"Processing {len(pdf_files)} PDF files...")
        print("-" * 60)

        for i, pdf_path in enumerate(pdf_files, 1):
            print(f"[{i}/{len(pdf_files)}] Processing: {pdf_path.name}")

            result = self.process_single_pdf(pdf_path)
            results.append(result)

            # Update statistics
            if result['metadata']['success']:
                success_count += 1
                total_headings += len(result['outline'])
                print(f"  ✓ Found {len(result['outline'])} headings in {result['metadata']['processing_time']}s")
            else:
                print(f"  ✗ Error: {result.get('error', 'Unknown error')}")

            # Save individual result
            output_file = self.output_dir / f"{pdf_path.stem}_outline.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)

        # Update summary
        summary.update({
            'successful': success_count,
            'failed': len(pdf_files) - success_count,
            'total_headings_found': total_headings,
            'average_headings_per_document': round(total_headings / max(success_count, 1), 1)
        })

        return {
            'results': results,
            'summary': summary
        }

    def generate_html_report(self, batch_results: Dict) -> str:
        """Generate an HTML report of all results"""
        summary = batch_results.get('summary', {})

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>PDF Outline Extraction Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
        .summary {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; margin-bottom: 30px; }}
        .pdf-result {{ border: 1px solid #ddd; margin: 20px 0; padding: 20px; border-radius: 5px; }}
        .success {{ border-left: 5px solid #4CAF50; }}
        .error {{ border-left: 5px solid #f44336; }}
        .outline {{ margin-left: 20px; }}
        .heading {{ margin: 5px 0; }}
        .h1 {{ font-weight: bold; color: #333; }}
        .h2 {{ font-weight: bold; color: #666; margin-left: 20px; }}
        .h3 {{ color: #999; margin-left: 40px; }}
        table {{ border-collapse: collapse; width: 100%; margin: 10px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        .no-data {{ color: #888; font-style: italic; }}
    </style>
</head>
<body>
    <h1>PDF Outline Extraction Report</h1>

    <div class="summary">
        <h2>Summary</h2>
        <table>
            <tr><th>Metric</th><th>Value</th></tr>
            <tr><td>Total Files Processed</td><td>{summary.get('total_files', 0)}</td></tr>
            <tr><td>Successful Extractions</td><td>{summary.get('successful', 0)}</td></tr>
            <tr><td>Failed Extractions</td><td>{summary.get('failed', 0)}</td></tr>
            <tr><td>Total Headings Found</td><td>{summary.get('total_headings_found', 0)}</td></tr>
            <tr><td>Average Headings per Document</td><td>{summary.get('average_headings_per_document', 0.0)}</td></tr>
            <tr><td>Processing Date</td><td>{summary.get('processing_date', 'Unknown')}</td></tr>
        </table>
    </div>

    <h2>Individual Results</h2>
"""

        results = batch_results.get('results', [])

        if not results:
            html_content += '<p class="no-data">No PDF files were processed.</p>'
        else:
            for result in results:
                metadata = result.get('metadata', {})
                success_class = "success" if metadata.get('success', False) else "error"

                html_content += f"""
    <div class="pdf-result {success_class}">
        <h3>{metadata.get('filename', 'Unknown file')}</h3>
        <p><strong>Title:</strong> {result.get('title', 'Unknown')}</p>
        <p><strong>Status:</strong> {'Success' if metadata.get('success', False) else 'Failed'}</p>
        <p><strong>File Size:</strong> {metadata.get('file_size', 0):,} bytes</p>
        <p><strong>Processing Time:</strong> {metadata.get('processing_time', 0)}s</p>
        <p><strong>Headings Found:</strong> {len(result.get('outline', []))}</p>

        {'<p><strong>Error:</strong> ' + result.get('error', '') + '</p>' if 'error' in result else ''}

        {f'<div class="outline"><h4>Outline:</h4>' if result.get('outline') else ''}
"""

            for heading in result.get('outline', []):
                level_class = heading.get('level', 'h3').lower()
                html_content += f'<div class="heading {level_class}">{heading.get("level", "H3")} - Page {heading.get("page", "?")}: {heading.get("text", "")}</div>\n'

            if result.get('outline'):
                html_content += '</div>'

            html_content += '</div>\n'

        html_content += """
</body>
</html>
"""

        return html_content

    def save_comprehensive_report(self, batch_results: Dict):
        """Save comprehensive reports in multiple formats"""
        # Save JSON report
        json_report_path = self.output_dir / "batch_report.json"
        with open(json_report_path, 'w', encoding='utf-8') as f:
            json.dump(batch_results, f, indent=2, ensure_ascii=False)

        # Save HTML report
        html_content = self.generate_html_report(batch_results)
        html_report_path = self.output_dir / "batch_report.html"
        with open(html_report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        # Save CSV summary
        csv_report_path = self.output_dir / "batch_summary.csv"
        with open(csv_report_path, 'w', encoding='utf-8') as f:
            f.write("Filename,Title,Success,Headings_Found,File_Size,Processing_Time,Method\n")
            for result in batch_results.get('results', []):
                metadata = result.get('metadata', {})
                f.write(f'"{metadata.get("filename", "")}",')
                f.write(f'"{result.get("title", "")}",')
                f.write(f'{metadata.get("success", False)},')
                f.write(f'{len(result.get("outline", []))},')
                f.write(f'{metadata.get("file_size", 0)},')
                f.write(f'{metadata.get("processing_time", 0)},')
                f.write(f'"{result.get("method", "unknown")}"\n')

        print(f"\nReports saved:")
        print(f"  JSON: {json_report_path}")
        print(f"  HTML: {html_report_path}")
        print(f"  CSV:  {csv_report_path}")


def main():
    """Command-line interface for batch processing"""
    parser = argparse.ArgumentParser(description="Batch PDF Outline Extractor")
    parser.add_argument("--input", "-i", default=".",
                        help="Input directory containing PDF files (default: current directory)")
    parser.add_argument("--output", "-o", default="output",
                        help="Output directory for results (default: output)")
    parser.add_argument("--debug", "-d", action="store_true",
                        help="Enable debug output")

    args = parser.parse_args()

    # Create processor
    processor = BatchPDFProcessor(
        input_dir=args.input,
        output_dir=args.output,
        debug=args.debug
    )

    # Process all PDFs
    print("Starting batch PDF processing...")
    start_time = time.time()

    batch_results = processor.process_all_pdfs()

    # Save comprehensive reports
    processor.save_comprehensive_report(batch_results)

    # Print final summary
    total_time = time.time() - start_time
    summary = batch_results['summary']

    print(f"\n{'=' * 60}")
    print("BATCH PROCESSING COMPLETE")
    print(f"{'=' * 60}")
    print(f"Total files processed: {summary['total_files']}")
    print(f"Successful extractions: {summary['successful']}")
    print(f"Failed extractions: {summary['failed']}")
    print(f"Total headings found: {summary['total_headings_found']}")
    print(f"Average headings per document: {summary['average_headings_per_document']}")
    print(f"Total processing time: {total_time:.2f}s")
    print(f"Average time per document: {total_time / max(summary['total_files'], 1):.2f}s")
    print(f"\nResults saved in: {processor.output_dir}")


if __name__ == "__main__":
    main()