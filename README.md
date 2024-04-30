didi_hackathon_pdf_manipulator
==============================
This script is a simple PDF manipulator that can apply various filters to the images in a PDF file.
It can also describe the images in the PDF file using the OpenAI API.
The script can be used from the command line and has the following options:

```
usage: manipulate_pdf.py [-h] [-v] [-o OUTPUT_FILE] [--blur BLUR] [--gray] [--black] [--emboss] [--describe] [--openai-key OPENAI_KEY] [--description-prompt DESCRIPTION_PROMPT] [--max-openai-tokens MAX_OPENAI_TOKENS]
                         [--font-size FONT_SIZE]
                         pdf_file

Change images in a PDF file.

positional arguments:
  pdf_file              Input

options:
  -h, --help            show this help message and exit
  -v, --verbose         Verbose mode
  -o OUTPUT_FILE, --output-file OUTPUT_FILE
                        Output file
  --blur BLUR           [0-50] Apply a blur effect to the images of the PDF.
  --gray                Gray scale the images of the PDF
  --black               Blacken the images of the PDF
  --emboss              Apply a emboss effect to the images of the PDF
  --describe            Apply a description to the content of the PDF
  --openai-key OPENAI_KEY
                        OpenAI key
  --description-prompt DESCRIPTION_PROMPT
                        Prompt for the description
  --max-openai-tokens MAX_OPENAI_TOKENS
                        Max tokens
  --font-size FONT_SIZE
                        Font size

```

**Example:**
This example will apply a blur effect with the intensity of 10 to the images in the PDF file
and print a short description of the content of each image on top of the image.

```
python manipulate_pdf.py --blur 10 --describe --openai-key sk-proj-BWmV64[...]7a example.pdf
```

**Requirements:**
- Python 3.6+
- OpenAI API key
- `pillow` and `requests` libraries (can be installed with `pip install -r requirements.txt`)