import markdown
from xhtml2pdf import pisa
import os
from ..logging_config import get_custom_logger

logger = get_custom_logger("pdf_generator", "pdf_generator.log")

def convert_md_to_pdf(md_content: str, output_path: str):
    """
    Converts Markdown content to PDF and saves it using xhtml2pdf.
    """
    logger.info(f"Starting convert_md_to_pdf. Input markdown size: {len(md_content)} chars | Destination: '{output_path}'")
    
    try:
        # Convert MD to HTML
        html_content = markdown.markdown(md_content, extensions=['fenced_code', 'tables'])
        logger.info(f"Fenced code and tables Markdown converted to HTML successfully. HTML size: {len(html_content)} chars.")
        
        # Add basic styling for the PDF
        styled_html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Helvetica, sans-serif; padding: 20px; }}
                h1, h2, h3 {{ color: #2c3e50; }}
                pre {{ background-color: #f4f4f4; padding: 10px; border: 1px solid #ddd; word-wrap: break-word; white-space: pre-wrap; }}
                code {{ font-family: Courier; }}
                table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            {html_content}
        </body>
        </html>
        """
        
        logger.info(f"Rendering styled HTML to PDF file...")
        # Generate PDF
        with open(output_path, "wb") as result_file:
            pisa_status = pisa.CreatePDF(
                styled_html,                # the HTML to convert
                dest=result_file            # file handle to receive result
            )
            
        if pisa_status.err:
            logger.error(f"xhtml2pdf/Pisa reported errors during compilation. Status code: {pisa_status.err}")
        else:
            logger.info(f"PDF successfully generated and saved to: '{output_path}'")
            
        return output_path
    except Exception as e:
        logger.error(f"Error during Markdown to PDF conversion process: {e}")
        raise e
