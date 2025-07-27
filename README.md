# PDF Outline Extractor

A Python tool that automatically extracts hierarchical document outlines from PDFs, generating structured table of contents with heading levels and page numbers in JSON/HTML format.

## 🚀 Features

- **Multi-strategy detection**: Combines pattern matching, font analysis, and position detection
- **Hierarchical structure**: Identifies H1, H2, H3 heading levels automatically
- **Multiple output formats**: JSON, HTML reports, and CSV summaries
- **Batch processing**: Handle single files or entire directories
- **Fast & reliable**: Processes documents in milliseconds with high accuracy
- **Robust filtering**: Removes false positives and body text automatically

## 📋 Requirements

- Python 3.8 or higher
- PyMuPDF (fitz)

## 🛠️ Installation

1. Clone the repository:
```bash
git clone https://github.com/KamalKumarMachireddy/PDF-Outline-Extractor-Round-1A.git
cd PDF-Outline-Extractor-Round-1A
```

2. Install dependencies:
```bash
pip install PyMuPDF==1.23.14
```

Or using requirements.txt:
```bash
pip install -r requirements.txt
```

## 🎯 Quick Start

### Process a single PDF:
```bash
python simple_pdf_processor.py sample.pdf
```

### Process multiple PDFs in a directory:
```bash
python batch_pdf_processor.py --input ./pdfs --output ./results
```

### Use in your Python code:
```python
from universal_pdf_extractor import UniversalPDFOutlineExtractor

extractor = UniversalPDFOutlineExtractor(debug=True)
result = extractor.extract_outline("document.pdf")

print(f"Title: {result['title']}")
print(f"Found {len(result['outline'])} headings")

for heading in result['outline']:
    print(f"{heading['level']} - Page {heading['page']}: {heading['text']}")
```

## 📊 Output Example

```json
{
  "title": "Understanding AI Systems",
  "outline": [
    {
      "level": "H1",
      "text": "1. Introduction",
      "page": 1
    },
    {
      "level": "H2", 
      "text": "What is Artificial Intelligence?",
      "page": 2
    },
    {
      "level": "H3",
      "text": "Machine Learning Basics", 
      "page": 3
    }
  ],
  "method": "structure_analysis"
}
```

## 📁 Project Structure

```
pdf-outline-extractor/
├── universal_pdf_extractor.py    # Main extraction engine
├── batch_pdf_processor.py        # Batch processing tool
├── simple_pdf_processor.py       # Single file processor
├── test.pdf                      # pdf file
├── README.md                     # This file
└── output/                       # Generated reports (auto-created)
```

## 🎨 Command Line Options

### Single File Processing:
```bash
python simple_pdf_processor.py <pdf_file> [output_file]
```

### Batch Processing:
```bash
python batch_pdf_processor.py [options]

Options:
  --input, -i    Input directory (default: current directory)
  --output, -o   Output directory (default: output)
  --debug, -d    Enable debug output
```

## 📈 Performance

- **Speed**: Processes most documents in under 0.1 seconds
- **Accuracy**: Multi-strategy approach ensures high detection rates
- **Scalability**: Handles documents up to 50 pages efficiently
- **Memory**: Optimized for low memory usage

## 🔧 Supported Document Types

- ✅ Academic papers
- ✅ Technical documentation  
- ✅ Business reports
- ✅ Books and chapters
- ✅ Research papers
- ✅ User manuals
- ✅ Any structured PDF document

## 🎯 Use Cases

Perfect for:
- **Researchers**: Generate TOCs for paper collections
- **Students**: Navigate complex academic documents
- **Content Managers**: Index document libraries
- **Developers**: Automate document analysis workflows
- **Digital Libraries**: Create searchable document indexes

## 🛡️ Detection Strategies

The extractor uses three complementary strategies:

1. **Pattern Matching**: Detects numbered sections, chapters, common headings
2. **Font Analysis**: Identifies headings by size, weight, and formatting
3. **Position Analysis**: Finds isolated text with appropriate spacing

## 📝 Output Formats

- **JSON**: Structured data for programmatic use
- **HTML**: Beautiful reports with styling and navigation
- **CSV**: Spreadsheet-compatible summaries

## 🐛 Troubleshooting

### Common Issues:

**"No PDF files found!"**
- Check that PDF files exist in the specified directory
- Ensure files have .pdf extension

**PyMuPDF installation issues:**
```bash
pip install --upgrade pip
pip install PyMuPDF==1.23.14
```

**Memory issues with large PDFs:**
- The extractor limits processing to 50 pages for performance
- For larger documents, consider splitting them first

### Test Installation:
```python
import fitz  # PyMuPDF
print("PyMuPDF version:", fitz.version)
print("Installation successful!")
```

## 📊 Example Results

Processing 2 PDFs with 88 total headings:
- ✅ 100% success rate
- ⚡ 0.07s total processing time
- 📈 44 headings average per document

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Built with [PyMuPDF](https://pymupdf.readthedocs.io/) for PDF processing
- Inspired by the need for better document analysis tools

## 📞 Support

If you encounter any issues or have questions:
- Open an issue on GitHub
- Check the troubleshooting section above
- Review the example usage in the code

---

**Made with ❤️ for better document processing**
