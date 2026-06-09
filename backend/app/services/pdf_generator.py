import re
import markdown
from xhtml2pdf import pisa
import os
from datetime import datetime
from ..logging_config import get_custom_logger

logger = get_custom_logger("pdf_generator", "pdf_generator.log")


def _mermaid_to_text(md: str) -> str:
    """Replace Mermaid graph TD blocks with simple indented text trees."""
    result_lines = []
    in_mermaid = False
    node_labels = {}

    for line in md.split("\n"):
        stripped = line.strip()

        if stripped == "```mermaid":
            in_mermaid = True
            result_lines.append("```")
            continue

        if in_mermaid and stripped == "```":
            in_mermaid = False
            node_labels.clear()
            result_lines.append("```")
            continue

        if in_mermaid:
            if stripped.startswith("graph "):
                continue

            # Extract all NodeID["Label"] from this line
            for m in re.finditer(r'(\w+)\["([^"]+)"\]', stripped):
                node_labels[m.group(1)] = m.group(2)
            for m in re.finditer(r'(\w+)\[([^\]]+)\]', stripped):
                node_labels[m.group(1)] = m.group(2)

            parts = re.split(r'\s*-->\s*|\s*==>\s*', stripped)
            labels = []
            for p in parts:
                p = p.strip()
                m = re.match(r'\w+\["?([^\]]*)"?\]', p)
                if m:
                    labels.append(m.group(1).strip('"'))
                else:
                    labels.append(node_labels.get(p, p))
            indent = "  " * (stripped.count("    "))
            result_lines.append(f"{indent}{' > '.join(labels)}")
        else:
            result_lines.append(line)

    return "\n".join(result_lines)


def convert_md_to_pdf(md_content: str, output_path: str):
    """
    Converts Markdown content to PDF and saves it using xhtml2pdf.
    """
    logger.info(f"Starting convert_md_to_pdf. Input markdown size: {len(md_content)} chars | Destination: '{output_path}'")

    try:
        # Convert Mermaid blocks to readable text before markdown processing
        md_content = _mermaid_to_text(md_content)
        html_content = markdown.markdown(md_content, extensions=['fenced_code', 'tables'])
        logger.info(f"Fenced code and tables Markdown converted to HTML successfully. HTML size: {len(html_content)} chars.")

        styled_html = f"""<html>
<head>
<style>
    @page {{
        size: a4;
        margin: 2cm 2.5cm;
        @frame footer {{
            -pdf-frame-content: footer;
            right: 2.5cm; left: 2.5cm; top: 28.7cm; height: 1cm;
        }}
    }}
    body {{
        font-family: Helvetica, Arial, sans-serif;
        font-size: 11pt;
        line-height: 1.6;
        color: #333;
    }}
    h1 {{
        font-size: 22pt;
        color: #1a3a5c;
        border-bottom: 3px solid #1a3a5c;
        padding-bottom: 6px;
        margin-top: 30px;
    }}
    h2 {{
        font-size: 16pt;
        color: #2c5f8a;
        border-bottom: 1px solid #b0c4de;
        padding-bottom: 4px;
        margin-top: 24px;
    }}
    h3 {{
        font-size: 13pt;
        color: #3a7bb5;
        margin-top: 18px;
    }}
    p {{ margin: 6px 0; text-align: justify; }}
    pre {{
        background-color: #f5f6fa;
        padding: 10px 12px;
        border-left: 4px solid #3a7bb5;
        font-family: "Courier New", monospace;
        font-size: 9pt;
        white-space: pre-wrap;
        word-wrap: break-word;
        page-break-inside: avoid;
    }}
    code {{
        font-family: "Courier New", monospace;
        font-size: 9.5pt;
        background-color: #f0f0f0;
        padding: 1px 4px;
    }}
    table {{
        border-collapse: collapse;
        width: 100%;
        margin: 12px 0;
        font-size: 10pt;
    }}
    th {{
        background-color: #1a3a5c;
        color: white;
        padding: 8px 10px;
        border: 1px solid #1a3a5c;
        text-align: left;
    }}
    td {{
        padding: 6px 10px;
        border: 1px solid #ddd;
    }}
    tr:nth-child(even) {{ background-color: #f8f9fa; }}
    ul, ol {{ margin: 4px 0; padding-left: 24px; }}
    li {{ margin: 2px 0; }}
    blockquote {{
        border-left: 4px solid #3a7bb5;
        margin: 12px 0;
        padding: 6px 14px;
        background: #f0f5fa;
        font-style: italic;
    }}
    hr {{
        border: none;
        border-top: 1px solid #ddd;
        margin: 20px 0;
    }}
    #footer {{
        font-size: 8pt;
        color: #999;
        text-align: center;
        border-top: 1px solid #ddd;
        padding-top: 4px;
    }}
    .cover {{
        text-align: center;
        padding-top: 120px;
        padding-bottom: 60px;
    }}
    .cover h1 {{
        font-size: 28pt;
        border: none;
        color: #1a3a5c;
    }}
    .cover .subtitle {{
        font-size: 14pt;
        color: #666;
        margin-top: 10px;
    }}
    .cover .date {{
        font-size: 10pt;
        color: #999;
        margin-top: 40px;
    }}
</style>
</head>
<body>

<div id="footer">
    AutoDocGen — Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')} — Page <pdf:pagenumber> of <pdf:pagecount>
</div>

{html_content}

</body>
</html>"""

        logger.info(f"Rendering styled HTML to PDF file...")
        with open(output_path, "wb") as result_file:
            pisa_status = pisa.CreatePDF(
                styled_html,
                dest=result_file
            )

        if pisa_status.err:
            logger.error(f"xhtml2pdf/Pisa reported errors during compilation. Status code: {pisa_status.err}")
        else:
            logger.info(f"PDF successfully generated and saved to: '{output_path}'")

        return output_path
    except Exception as e:
        logger.error(f"Error during Markdown to PDF conversion process: {e}")
        raise e
