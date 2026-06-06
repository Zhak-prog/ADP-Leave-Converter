import streamlit as str
import pandas as pd
from google import genai
from PIL import Image
import io

# Set page configuration
str.set_page_config(page_title="Roster Image to Table Converter", layout="wide")

# Add the JLL Logo at the top of the interface
str.image(
    "https://raw.githubusercontent.com/Zhak-prog/ADP-Leave-Converter/main/1000014225.png" if False else "https://logo.clearbit.com/jll.com", 
    width=150
)

str.title("🗓️ Schedule Roster Image Converter")
str.write("Upload your roster image to convert it into a structured data table.")
# Sidebar for API Key configuration
with str.sidebar:
    str.header("Configuration")
    api_key = str.text_input("Enter Google Gemini API Key:", type="password")
    str.markdown("[Get a free API key here](https://aistudio.google.com/)")

# Image uploader
uploaded_file = str.file_uploader("Choose a schedule image...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # Display the uploaded image
    image = Image.open(uploaded_file)
    str.image(image, caption="Uploaded Schedule Image", use_container_width=True)
    
    if str.button("Process Schedule Image", type="primary"):
        if not api_key:
            str.error("Please enter your Gemini API Key in the sidebar.")
        else:
            with str.spinner("Analyzing image and generating table..."):
                try:
                    # Initialize the Gemini Client
                    client = genai.Client(api_key=api_key)
                    
                    # Convert PIL Image to bytes for the API
                    img_byte_arr = io.BytesIO()
                    image.save(img_byte_arr, format=image.format if image.format else 'JPEG')
                    img_bytes = img_byte_arr.getvalue()
                    
                    # Strict prompt instructing the AI how to format and handle the data extraction
                    prompt = """
                    Analyze this schedule roster image and convert it into a Markdown table structure. 
                    Follow these rules strictly:
                    1. The first column must be 'Employee Name'.
                    2. Extract all 31 days. Convert the dates into the header format 'mm/dd/yyyy'. Assume the month starts on a Friday (use May 2026 as the standard layout baseline where Day 1 is 05/01/2026).
                    3. If a day is a Saturday or Sunday, replace its value entirely with 'X'.
                    4. For weekdays (Monday through Friday):
                       - If the cell contains a seat/chair icon, write 'Workday'.
                       - If the cell contains a clock icon, write 'On Leave'.
                       - If the cell contains a briefcase icon, write 'Holiday/OB'.
                       - If the cell is blank or unassigned, leave it blank.
                    5. Output ONLY the raw Markdown table. Do not include introductory text, explanations, or conclusions.
                    """
                    
                    # Call the Gemini 2.5 Flash model
                    response = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=[
                            genai.types.Part.from_bytes(
                                data=img_bytes,
                                mime_type=f"image/{image.format.lower() if image.format else 'jpeg'}"
                            ),
                            prompt
                        ]
                    )
                    
                    # Display results
                    str.success("Data successfully extracted!")
                    
                    # Render the Markdown table directly in the app
                    str.markdown("### Processed Schedule Table")
                    str.markdown(response.text)
                    
                    # Add a download option by attempting to parse the markdown table into CSV
                    try:
                        lines = [line for line in response.text.strip().split('\n') if '|' in line]
                        if len(lines) > 2:
                            # Parse headers
                            headers = [cell.strip() for cell in lines[0].split('|')[1:-1]]
                            # Parse rows (skip the separator row index 1)
                            rows = []
                            for line in lines[2:]:
                                row = [cell.strip() for cell in line.split('|')[1:-1]]
                                if row:
                                    rows.append(row)
                            
                            df = pd.DataFrame(rows, columns=headers)
                            csv = df.to_csv(index=False).encode('utf-8')
                            
                            str.download_button(
                                label="📥 Download Table as CSV",
                                data=csv,
                                file_name="extracted_schedule.csv",
                                mime="text/csv",
                            )
                    except Exception as parse_err:
                        str.info("Could not generate a CSV file link, but the visual table above is complete.")
                        
                except Exception as e:
                    str.error(f"An error occurred during processing: {e}")
