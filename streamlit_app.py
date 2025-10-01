import streamlit as st
import google.generativeai as genai
from fpdf import FPDF
from datetime import datetime, date
import unicodedata
import re
import os


# Function to format date into "Month Year" format
def format_date(date_input):
    if isinstance(date_input, datetime):  # Check if it's a datetime object
        return date_input.strftime("%B %Y")
    
    if isinstance(date_input, date):  # Correct check for 'date' from datetime module
        return date_input.strftime("%B %Y")
    
    if isinstance(date_input, str):  # Check if it's a string
        try:
            date_obj = datetime.strptime(date_input, "%Y-%m-%d")  # Parse the string to datetime
            return date_obj.strftime("%B %Y")
        except ValueError:
            return 'Invalid Date Format'
    
    return 'N/A'


# Function to validate 4-digit numbers for start and end year
def validate_year(year):
    if year.isdigit() and len(year) == 4:
        return year
    return None

# Function to validate CGPA (float values between 0.0 and 10.0)
def validate_cgpa(cgpa):
    try:
        cgpa_value = float(cgpa)
        if 0.0 <= cgpa_value <= 10.0:
            return cgpa_value
    except ValueError:
        pass
    return None

# Function to validate Percentage (float values between 0.0 and 100.0)
def validate_percentage(percentage):
    try:
        percentage_value = float(percentage)
        if 0.0 <= percentage_value <= 100.0:
            return percentage_value
    except ValueError:
        pass
    return None

# Function to validate email
def validate_email(email):
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(email_regex, email)

# Function to validate phone number with country code (e.g., +91 9988776655)
def validate_phone_number(phone_number):
    phone_regex = r'^\+(\d{1,4})[\s.-]?\(?(\d{1,3})\)?[\s.-]?(\d{1,4})[\s.-]?(\d{1,4})[\s.-]?(\d{1,9})$'
    return re.match(phone_regex, phone_number)

# Function to validate the Gemini API key by generating content
def validate_gemini_api_key(api_key):
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")  # Use the correct model name
        model.generate_content("Test the Gemini API")
        return True
    except Exception as e:
        st.error(f"Error: {e}")
        return False

# Function to refine a summary using Gemini for an ATS-friendly resume
def refine_summary(api_key, summary):
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")
        
        # Refine the summary with an ATS-friendly approach (3-line, concise)
        prompt = f"Please improve this summary to make it concise and ATS-friendly, in 3 lines: {summary}"
        response = model.generate_content(prompt)
        
        # Extract the refined summary
        if response and response.candidates and response.candidates[0].content.parts:
            refined_summary = response.candidates[0].content.parts[0].text
            # Limit to 3 lines if necessary
            refined_summary_lines = refined_summary.split('\n')
            refined_summary = '\n'.join(refined_summary_lines[:3])  # Ensure it's 3 lines
            return refined_summary.strip()
        else:
            raise ValueError("Failed to generate a refined summary.")
    except Exception as e:
        print("Error:", e)
        return summary  # Fallback to the original summary
    
# Function to refine work experience into concise bullet points
def refine_experience(api_key, experience):
    try:
        # Configure Gemini with the API key
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")

        # Request Gemini to refine the work experience into three concise bullet points
        response = model.generate_content(f"Refine the following work experience into three concise bullet points: {experience}")

        # Extract the refined experience description with bullet points
        if response and response.candidates and response.candidates[0].content.parts:
            refined_experience = response.candidates[0].content.parts[0].text
            
            # Clean up the formatting to remove unwanted symbols and ensure clean bullet points
            refined_experience = refined_experience.replace("*", "-")  # Remove stray asterisks
            refined_experience = refined_experience.strip()  # Clean up extra spaces
            
            # Ensure that the bullet points are properly split and formatted
            bullet_points = refined_experience.split("\n")
            bullet_points = [point.strip() for point in bullet_points if point.strip()]

            # Limit to only 3 bullet points
            bullet_points = bullet_points[:3]

            # Clean up and ensure only "-" is used for bullet points
            refined_experience = "\n".join([f"{point.strip()}" for point in bullet_points])
            
            return refined_experience.strip()
        else:
            raise ValueError("Failed to generate a refined work experience description.")
    except Exception as e:
        print(f"Error: {e}")
        return experience  # Fallback to the original experience description


# Function to refine project descriptions into concise details using Gemini API
def refine_project(api_key, project_description):
    try:
        # Configure Gemini with the API key
        genai.configure(api_key=api_key)  # Set up API configuration
        model = genai.GenerativeModel("gemini-2.5-flash")  # Choose the Gemini model

        # Request Gemini to refine the project description into concise bullet points
        response = model.generate_content(f"Refine the following project description into three concise bullet points: {project_description}")
        
        # Ensure the response contains the necessary information
        if response and response.candidates and response.candidates[0].content.parts:
            refined_project = response.candidates[0].content.parts[0].text  # Extract the refined text
            
            # Split the refined text into bullet points
            bullet_points = refined_project.split("\n")
            bullet_points = [point.strip(" -*") for point in bullet_points if point.strip()]  # Clean and remove unwanted symbols
            
            # Limit to 3 bullet points
            bullet_points = bullet_points[:3]
            
            # Format bullet points consistently
            refined_project = "\n".join([f"- {point}" for point in bullet_points])
            
            return refined_project.strip()
        else:
            raise ValueError("Failed to generate a refined project description.")
    except Exception as e:
        print(f"Error: {e}")
        return "\n".join([f"- {line.strip()}" for line in project_description.split("\n") if line.strip()])  # Fallback

def categorize_skills(skills_list):
    # Define the skill sets
    programming_skills_set = {
        "python", "java", "c++", "c", "c#", "javascript", "typescript", "ruby", "go", "rust", "swift", "kotlin", "php",
        "sass", "less", "react", "angular", "vue", "next.js", "nuxt.js", "jquery", "express", "django",
        "flask", "laravel", "spring", "asp.net", "flutter", "react native", "xamarin", "ionic", "r", "matlab", "sas", 
        "stata", "julia", "numpy", "pandas", "tensorflow", "keras", "scikit-learn", "pytorch", "sql", "pl/sql", "t-sql", 
        "mongodb", "postgresql", "mysql", "sqlite", "cassandra", "bash", "shell", "powershell", "perl", "ansible", 
        "chef", "puppet", "assembly", "fortran", "cobol", "lua", "haskell", "elixir", "clojure", "scheme", "prolog", 
        "unity", "unreal engine", "godot", "solidity", "web3.js", "truffle", "hardhat", "cardano", "mlflow", 
        "pytorch lightning", "huggingface", "jupyter", "openai api", "jest", "mocha", "junit", "pytest", "selenium", 
        "awk", "sed", "vhdl", "verilog"
    }

    technical_skills_set = {
        "linux", "windows server", "unix", "macos", "ubuntu", "red hat", "centos", "aws", "azure", "google cloud","html", "css",
        "oracle cloud", "ibm cloud", "digitalocean", "heroku", "docker", "kubernetes", "openshift", "podman", "rancher", 
        "vmware", "virtualbox", "hyper-v", "vagrant", "sql", "nosql", "postgresql", "mysql", "mongodb", "cassandra", 
        "redis", "elasticsearch", "dynamodb", "bigquery", "hadoop", "snowflake", "redshift", "jenkins", "gitlab ci/cd", 
        "github actions", "terraform", "ansible", "chef", "puppet", "circleci", "argo cd", "prometheus", "grafana", 
        "splunk", "elk stack", "new relic", "datadog", "zabbix", "vpn", "firewalls", "nginx", "apache", "load balancers", 
        "wireshark", "snort", "burp suite", "metasploit", "iam", "active directory", "okta", "sso", "zero trust", 
        "penetration testing", "threat modeling", "vulnerability management", "ransomware protection", "siem", 
        "endpoint detection", "xdr", "splunk for security", "cyber threat intelligence", "iso 27001", "gdpr compliance", 
        "bash scripting", "powershell", "python scripting", "perl scripting", "yaml", "json", "xml", "pandas", "numpy", 
        "matplotlib", "seaborn", "scikit-learn", "tensorflow", "pytorch", "keras", "apache spark", "databricks", 
        "hive", "sas", "tableau", "power bi", "apache kafka", "apache hadoop", "databricks", "beam", "presto", "flink", 
        "airflow", "openai", "huggingface", "llama", "dalle", "stable diffusion", "midjourney", "langchain", "chatgpt", 
        "gpt-4", "transformers", "t5", "controlnet", "alpaca", "ai-driven threat analysis", "ai-based firewalls", 
        "ml in cybersecurity", "mlops", "kubeflow", "mlflow", "tensorflow serving", "pytorch serve", "sagemaker", 
        "vertex ai", "blockchain", "web3", "ethereum", "smart contracts", "solidity", "nft", "defi", "postman", 
        "swagger", "restapi", "graphql", "grpc", "iot", "mqtt", "edge computing", "arduino", "raspberry pi", "zigbee", 
        "lorawan", "5g networks", "quantum computing", "augmented reality", "virtual reality", "xr", "metaverse", 
        "digital twins", "ai ethics", "autonomous systems"
    }

    tools_set = {
        "git", "github", "gitlab", "bitbucket", "svn", "mercurial", "docker", "kubernetes", "openshift", "rancher", 
        "podman", "jenkins", "gitlab ci/cd", "github actions", "circleci", "travis ci", "bamboo", "vscode", 
        "intellij idea", "pycharm", "eclipse", "netbeans", "atom", "sublime text", "notepad++", "xcode", 
        "android studio", "gdb", "valgrind", "pdb", "lldb", "chrome devtools", "firebug", "visualvm", "prometheus", 
        "grafana", "splunk", "elk stack", "datadog", "zabbix", "new relic", "selenium", "junit", "pytest", "cucumber", 
        "testng", "katalon", "soapui", "postman", "dbeaver", "pgadmin", "heidisql", "mysql workbench", 
        "oracle sql developer", "mongodb compass", "tableplus", "sqlmap", "maven", "gradle", "ant", "cmake", "make", 
        "aws cli", "azure cli", "google cloud sdk", "terraform", "ansible", "packer", "figma", "adobe xd", "sketch", 
        "invision", "balsamiq", "canva", "jira", "confluence", "trello", "monday.com", "asana", "slack", "zoom", 
        "teams", "terminator", "hyper", "iterm2", "putty", "kitty", "alacritty", "powershell", "bash", "zsh", "fish", 
        "tmux", "vagrant", "virtualbox", "vmware", "wireshark", "ngrok", "postman", "swagger", "grpc"
    }

    # Categorizing based on predefined categories
    programming_skills = [skill for skill in skills_list if skill.lower() in programming_skills_set]
    technical_skills = [skill for skill in skills_list if skill.lower() in technical_skills_set]
    tools = [skill for skill in skills_list if skill.lower() in tools_set]
    other_skills = [skill for skill in skills_list if skill.lower() not in 
                    programming_skills_set and skill.lower() not in technical_skills_set and skill.lower() not in tools_set]

    # Format the output as requested
    categorized_skills = {
        "Programming Skills": ", ".join(programming_skills) if programming_skills else "No skills provided.",
        "Technical Skills": ", ".join(technical_skills) if technical_skills else "No skills provided.",
        "Tools": ", ".join(tools) if tools else "No skills provided.",
        "Other Skills": ", ".join(other_skills) if other_skills else "No skills provided."
    }

    return categorized_skills


def generate_pdf(data):
    pdf = FPDF()
    pdf.add_page()

    

    icons = {
        "phone": "phone_icon.png",
        "email": "email_icon.png",
        "linkedin": "linkedin_icon.png",
        "github": "github_icon.png",
        "personal_url": "personal_url_icon.png",
        "location": "location_icon.png"
    }

    # Set font and define fallback for unsupported characters
    font_filename = "DejaVuSansCondensed.ttf"
    if os.path.exists(font_filename):
        pdf.add_font('DejaVu', '', font_filename, uni=True)
        pdf.set_font('DejaVu', '', 12)
    else:
        pdf.set_font("Arial", size=12)

    ## Add Header (Full Name) at the top
    pdf.set_font("Arial", 'B', size=22)
    pdf.set_text_color(0, 0, 0)
    pdf.set_y(2)  # Set the y position for full name at the top
    pdf.cell(0, 10, txt=data.get('full_name', '').upper(), align='C', ln=True)  # Left align the name and avoid line break


    # Add Address with location icon on the same line
    address = data.get('address', '')
    if address:
        pdf.set_font("Arial", size=12)
        page_width = pdf.w - 2 * pdf.l_margin
        icon_width = 5
        address_width = pdf.get_string_width(address)
        total_width = icon_width + address_width
        x_position = (page_width - total_width) / 2

        pdf.set_xy(x_position, pdf.get_y())  # Adjust to add minimal spacing
        pdf.image(icons['location'], x=pdf.get_x(), y=pdf.get_y(), w=icon_width, h=5)
        pdf.set_x(pdf.get_x() + icon_width)
        google_maps_link = f"https://www.google.com/maps/search/?api=1&query={address.replace(' ', '+')}"
        pdf.cell(0, 5, txt=address, link=google_maps_link, align='L', ln=True)

    pdf.ln(1)  # To ensure there's no excessive gap after the address section

    # Horizontal Contact Info Section
    pdf.set_font("Arial", size=12)
    contact_info = []

    if data.get('phone_number', ''):
        contact_info.append((icons['phone'], f"+91 {data.get('phone_number').replace('+91 ', '')}", f"tel:+91{data.get('phone_number').replace('+91 ', '')}"))
    if data.get('email', ''):
        contact_info.append((icons['email'], "MAIL", f"mailto:{data.get('email', '').strip()}"))
    if data.get('linkedin_url', ''):
        contact_info.append((icons['linkedin'], "LINKEDIN", data.get('linkedin_url', '').strip()))
    if data.get('github_url', ''):
        contact_info.append((icons['github'], "GITHUB", data.get('github_url', '').strip()))
    if data.get('personal_url', ''):
        contact_info.append((icons['personal_url'], "PERSONALURL", data.get('personal_url', '').strip()))

    for icon, text, link in contact_info:
        pdf.image(icon, x=pdf.get_x(), y=pdf.get_y(), w=5, h=5)
        pdf.set_x(pdf.get_x() + 5)
        pdf.write(5, text, link=link)
        pdf.set_x(pdf.get_x() + 10)
    pdf.ln(3)


    # Add "SUMMARY" title in bold, left-aligned
    pdf.set_font("Arial", 'B', size=14)
    pdf.cell(0, 10, txt="SUMMARY", ln=False, align='L')  # Add title without moving to the next line

    # Draw the horizontal line immediately below the title
    current_y = pdf.get_y() + 7  # Align the line close to the title
    pdf.set_line_width(0.5)
    pdf.set_draw_color(0, 0, 0)
    pdf.line(10, current_y, pdf.w - 10, current_y)  # Draw the line

    # Immediately display the refined summary text below the horizontal line
    pdf.set_y(current_y + 1)  # Minimal adjustment to avoid overlap with the line
    summary = data.get('summary', '')
    refined_summary = refine_summary(api_key, summary)

    # Display the summary data without any extra gap
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 6, txt=refined_summary.strip(), align='L')  # Align text to the left
    pdf.ln(0)
    
    # Use the built-in Arial font
    pdf.set_font("Arial", style="B", size=14)  # Bold and increased font size for the title

    # Add "EXPERIENCE" title in bold, left-aligned
    pdf.cell(0, 10, txt="EXPERIENCE", ln=False, align='L')  # Add title without moving to the next line

    # Draw the horizontal line immediately below the title
    current_y = pdf.get_y() + 7  # Align the line close to the title
    pdf.set_line_width(0.5)
    pdf.set_draw_color(0, 0, 0)
    pdf.line(10, current_y, pdf.w - 10, current_y)  # Draw the line

    # Immediately move to the next line below the horizontal line
    pdf.set_y(current_y + 1)  # Minimal adjustment to avoid overlap with the line

    # Add the formatted experience section
    for exp in data['experiences']:
        pdf.set_font("Arial", style="B", size=12)

        # Set role and company in the left part, with date aligned to the right
        role_company_text = f"{exp['role']} ({exp['company']})"

        # Check if end date is None, replace with 'Present'
        end_date = exp['end_date'] if exp['end_date'] else 'Present'
        start_end_date = f"{exp['start_date']} - {end_date}"

        # Add role and company on the left, and align the date to the right
        pdf.cell(130, 8, txt=role_company_text, ln=False)  # Left part (role + company)
        pdf.cell(60, 8, txt=start_end_date, align='R', ln=True)  # Right part (date)

        pdf.set_font("Arial", size=11)

        # Split and add each bullet point on a new line
        bullet_points = exp['description'].split('\n')
        for point in bullet_points:
            if point.strip():  # Avoid adding empty lines
                # Use "-" for bullet points
                pdf.multi_cell(0, 6, txt=f" {point.strip()}", border=0, align='L')

    # No extra gaps added after the experience section
    pdf.ln(0)
    
    # Use the built-in Arial font
    pdf.set_font("Arial", style="B", size=14)  # Bold and increased font size for the title

    # Add "PROJECTS" title in bold, left-aligned
    pdf.cell(0, 10, txt="PROJECTS", ln=False, align='L')  # Add title without moving to the next line

    # Draw the horizontal line immediately below the title
    current_y = pdf.get_y() + 7  # Align the line close to the title
    pdf.set_line_width(0.5)
    pdf.set_draw_color(0, 0, 0)
    pdf.line(10, current_y, pdf.w - 10, current_y)  # Draw the line

    # Move to the next line below the horizontal line
    pdf.set_y(current_y + 1)  # Minimal adjustment to avoid overlap with the line

    # Iterate over projects
    for proj in data['projects']:
        pdf.set_font("Arial", style="B", size=12)

        # Print the project name and add clickable URL (if available)
        project_text = proj['project_name']
        if proj.get('project_url'):
            pdf.cell(0, 8, txt=f"{project_text} ({proj['project_url']})", ln=True, link=proj['project_url'])
        else:
            pdf.cell(0, 8, txt=project_text, ln=True)

        # Refine and format the project description
        refined_description = refine_project(api_key, proj['description'])
        pdf.set_font("Arial", size=11)

        # Add bullet points with reduced spacing
        for point in refined_description.split("\n"):
            if point.strip():  # Avoid empty lines
                pdf.multi_cell(0, 6, txt=f" {point.strip()}", border=0, align='L')
        
    pdf.ln(0)


    # Set font and title for the "EDUCATION" section
    pdf.set_font("Arial", style="B", size=14)  # Bold and increased font size for the title

    # Add "EDUCATION:" title in bold, left-aligned
    pdf.cell(0, 6, txt="EDUCATION:", ln=True, align="L")  # Add title and move to the next line

    # Draw the horizontal line immediately below the title
    current_y = pdf.get_y() + 1  # Align the line close to the title
    pdf.set_line_width(0.5)
    pdf.set_draw_color(0, 0, 0)
    pdf.line(10, current_y, pdf.w - 10, current_y)  # Draw the line
    pdf.set_y(current_y + 1)  # Align content immediately below the line

    # Loop through education records
    for edu in data['education_records']:
        # Ensure degree, institution, and grade_value are strings
        degree_text = str(edu['degree'])  # Convert degree to string if it's not already
        institution = str(edu['institution'])  # Convert institution to string if it's not already
        grade_value = str(edu['grade_value'])  # Convert grade_value to string if it's not already
    
        # Ensure year fields are strings for proper formatting
        start_year = str(edu['start_year'])  # Convert start year to string
        end_year = str(edu['end_year'])  # Convert end year to string
    
        # Degree and year range
        degree_with_year = f"({start_year}-{end_year})"
    
        # Set font for degree and year range
        pdf.set_font("Arial", size=12)  # Regular font for degree and year
        pdf.cell(130, 6, txt=degree_text, align="L")  # Degree on the left
        pdf.set_font("Arial", style="B", size=12)  # Bold font for year range
        pdf.cell(0, 6, txt=degree_with_year, align="R", ln=True)  # Year range on the right in bold

        # Institution and grade
        grade_type = edu['grade_type']
        if grade_type == "CGPA":
            grade_text = f"(CGPA: {grade_value})"
        elif grade_type == "Percentage":
            grade_text = f"({grade_value}%)"
        else:
            grade_text = "(None)"
    
        # Add institution on the left and grade on the right
        pdf.set_font("Arial", size=12)  # Regular font for institution
        pdf.cell(130, 6, txt=institution, align="L")  # Institution name on the left
        pdf.set_font("Arial", style="B", size=12)  # Bold for grade
        pdf.cell(0, 6, txt=grade_text, align="R", ln=True)  # Grade on the right

    # No extra line breaks or gaps
    pdf.ln(0)

    # Extracting the categorized skills from the data
    categorized_skills = data["categorized_skills"]

    # Add the "SKILLS" header
    pdf.set_font("Arial", style="B", size=12)
    pdf.cell(0, 10, txt="SKILLS:", ln=True)

    # Add a horizontal line
    pdf.set_draw_color(0, 0, 0)
    pdf.set_line_width(0.5)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())

    # Add categorized skills using write()
    for category, skills in categorized_skills.items():
        # Add category in bold
        pdf.set_font("Arial", style="B", size=11)
        pdf.write(5, f"{category}:")  # Category text

        # Add skills in regular font on the same line
        pdf.set_font("Arial", size=11)
        pdf.write(5, f" {skills}\n")  # Skills text right after category without newline

    # Ensure a new line after each category-skills pair
    pdf.ln(1)  # Adjust this number to change the gap between each pair




    
    # Set the title in uppercase
    pdf.set_font("Arial", style="B", size=14)  # Bold font for title
    pdf.cell(0, 6, txt="CERTIFICATIONS", ln=True, align="L")  # Uppercase title with reduced height

    # Add a horizontal line
    pdf.set_draw_color(0, 0, 0)
    pdf.set_line_width(0.5)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())

    # Add certifications in one line
    pdf.set_font("Arial", size=12)  # Regular font for certifications
    for cert in data['certifications']:
        certification_name = cert['certification_name']
        issuing_company = cert['issuing_company']
        issue_date = format_date(cert['issue_date'])

        # Format: "AWS Certified Solutions Architect - Amazon Web Services        January 2025"
        text = f"{certification_name} - {issuing_company}"

        # Add certification name and issuing company (left-aligned)
        pdf.cell(0, 6, txt=text, border=0, ln=0, align="L")

        # Add issue date in bold (right-aligned)
        pdf.set_font("Arial", style="B", size=12)  # Bold font for the date
        pdf.cell(-60)  # Adjust positioning for the date to align to the right
        pdf.cell(60, 6, txt=issue_date, border=0, ln=1, align="R")  # Right-aligned date

        # Reset font to regular for subsequent certifications
        pdf.set_font("Arial", size=12)


    output_file = "resume.pdf"
    pdf.output(output_file)
    return output_file

# Streamlit App
st.title("MastermindHub ATS Resume Generator")
st.subheader("Built by UMARFAROOQ")
st.subheader("Enter Your Gemini API Key")

# Input API Key
api_key = st.text_input("API Key", type="password")

if api_key:
    if validate_gemini_api_key(api_key):
        st.success("API Key is valid!")

        # Collect user details with examples in input fields
        full_name = st.text_input("Full Name (e.g., 'John Doe')")  # Example: 'John Doe'
        address = st.text_area("Address (e.g., '1234 Elm Street, Apartment 56B, Springfield, IL, 62704, USA')")  # Example: '1234 Elm Street, Apartment 56B, Springfield, IL, 62704, USA'
        phone_number = st.text_input("Phone Number (e.g., '+91 9988776655')")  # Example: '+91 9988776655'
        # Validate phone number
        if phone_number and not validate_phone_number(phone_number):
            st.warning("Please enter a valid phone number with country code (e.g., +91 9988776655)")
        email = st.text_input("Email (e.g., 'johndoe123@example.com')")  # Example: 'johndoe@example.com'
        # Validate email
        if email and not validate_email(email):
            st.warning("Please enter a valid email address!")
        linkedin_url = st.text_input("LinkedIn URL (e.g., 'https://www.linkedin.com/in/johndoe/')")  # Example: 'https://www.linkedin.com/in/johndoe/'
        github_url = st.text_input("GitHub URL (Optional, e.g., 'https://github.com/johndoe1234567')")  # Example: 'https://github.com/johndoe'
        personal_website = st.text_input("Personal Website URL (Optional, e.g., 'https://www.johndoe.com')")  # Example: 'https://www.johndoe.com'
        summary = st.text_area("Summary (e.g., 'A motivated software engineer with 3+ years of experience in full-stack development.')")  # Example: 'A motivated software engineer with 3+ years of experience in full-stack development.'

        # Streamlit UI to gather work experience
        st.subheader("Work Experience")
        num_experiences = st.number_input("Number of Experiences", min_value=1, max_value=5, value=1)
        experiences = []
        for i in range(num_experiences):
            with st.expander(f"Experience {i+1}"):
                role = st.text_input(f"Role {i+1} (e.g., 'Software Engineer')", key=f"role_{i+1}")
                company = st.text_input(f"Company {i+1} (e.g., 'TechCorp Inc.')", key=f"company_{i+1}")
                start_date = st.date_input(f"Start Date {i+1} (e.g., '2021-06-01')", key=f"start_date_{i+1}")
                end_date = st.date_input(f"End Date {i+1} (optional, e.g., '2023-08-31')", key=f"end_date_{i+1}")
                is_currently_working = st.checkbox(f"Currently Working in Company {i+1}", key=f"current_{i+1}")
                description = st.text_area(
                    f"Description {i+1} (e.g., 'Developed scalable web applications, optimized backend performance, and led a team of 5 developers.')",
                    key=f"description_{i+1}"
                )

                # Append experience to the list
                experiences.append({
                    "role": role,
                    "company": company,
                    "start_date": format_date(start_date),
                    "end_date": None if is_currently_working else format_date(end_date),
                    "description": description,
                })

        # Process each experience description and refine it
        for exp in experiences:
            if exp['description']:
                refined_experience = refine_experience(api_key, exp['description'])
                exp['description'] = refined_experience


        # Input for Projects
        st.subheader("Projects")
        num_projects = st.number_input("Number of Projects", min_value=1, max_value=10, step=1, value=1, key="num_proj")
        projects = []
        for i in range(1, num_projects + 1):
            with st.expander(f"Project {i}"):
                project_name = st.text_input(f"Project Title {i} (e.g., 'AI-Powered Resume Builder')", key=f"proj_name_{i}")  
                # Example: 'AI-Powered Resume Builder'
                project_url = st.text_input(f"Project URL {i} (Optional, e.g., 'https://github.com/username/resume-builder')", key=f"proj_url_{i}")  
                # Example: 'https://github.com/username/resume-builder'
                project_description = st.text_area(
                    f"Project Description {i} (e.g., 'Developed an AI-powered tool to generate customized resumes based on user inputs, using Python and Streamlit.')",
                    key=f"proj_desc_{i}"
                )  # Example: 'Developed an AI-powered tool...'
                projects.append({
                    "project_name": project_name,
                    "project_url": project_url,
                    "description": project_description,
                })

        # Education Section
        st.subheader("Education")
        num_education = st.number_input(
            "Number of Education Records", min_value=1, max_value=5, step=1, value=1, key="num_edu"
        )
        education_records = []
        has_errors = False
        for i in range(1, num_education + 1):
            with st.expander(f"Education {i}"):
                degree = st.text_input(f"Degree {i} (e.g., 'Bachelor of Technology in Computer Science')", key=f"degree_{i}")  
                institution = st.text_input(f"Institution {i} (e.g., 'PBR Visvodaya Institute of Technology & Science')", key=f"institution_{i}")  
                start_year = st.text_input(f"Start Year {i} (e.g., '2020')", key=f"start_year_{i}")  
                start_year_valid = validate_year(start_year)
                if start_year and not start_year_valid:
                    st.warning(f"Invalid Start Year {i}. Please enter a 4-digit number.")
                    has_errors = True        
                end_year = st.text_input(f"End Year {i} (e.g., '2024')", key=f"end_year_{i}")  
                end_year_valid = validate_year(end_year)
                if end_year and not end_year_valid:
                    st.warning(f"Invalid End Year {i}. Please enter a 4-digit number.")
                    has_errors = True        
                grade_type = st.selectbox(f"Grade Type {i}", options=["CGPA", "Percentage"], key=f"grade_type_{i}")
                grade_value = None
                if grade_type == "CGPA":
                    cgpa = st.text_input(f"CGPA {i} (e.g., '8.5')", key=f"cgpa_{i}")  
                    grade_value = validate_cgpa(cgpa)
                    if grade_value is None and cgpa:
                        st.warning(f"Invalid CGPA {i}. Please enter a value between 0.0 and 10.0.")
                        has_errors = True
                elif grade_type == "Percentage":
                    percentage = st.text_input(f"Percentage {i} (e.g., '85')", key=f"percentage_{i}")  
                    grade_value = validate_percentage(percentage)
                    if grade_value is None and percentage:
                        st.warning(f"Invalid Percentage {i}. Please enter a value between 0.0 and 100.0.")
                        has_errors = True
                # Add Education Record if No Errors
                if not has_errors:
                    education_records.append({
                        "degree": degree,
                        "institution": institution,
                        "start_year": start_year_valid,
                        "end_year": end_year_valid,
                        "grade_type": grade_type,
                        "grade_value": grade_value,
                    })

        # Skills Section
        st.subheader("Skills")
        skills = st.text_area(
            "Skills (Enter each skill on a new line or separate with commas, e.g., Python, Java, HTML, CSS, React)"
        )

        # Split skills into a list based on commas or newlines
        skills_list = [skill.strip() for skill in skills.replace(',', '\n').splitlines() if skill.strip()]
    
        # Certifications Section
        st.subheader("Certifications")
        num_certifications = st.number_input(
            "Number of Certifications", min_value=1, max_value=5, step=1, value=1, key="num_cert"
        )
        certifications = []
        for i in range(1, num_certifications + 1):
            with st.expander(f"Certification {i}"):
                certification_name = st.text_input(
                    f"Certification Name {i} (e.g., 'AWS Certified Solutions Architect')", key=f"cert_name_{i}"
                )
        # Example: "AWS Certified Solutions Architect"

                issuing_company = st.text_input(
                    f"Issuing Company {i} (e.g., 'Amazon Web Services')", key=f"cert_company_{i}"
                )
        # Example: "Amazon Web Services"

                issue_date = st.date_input(f"Issue Date {i} (e.g., '2024-01-01')", key=f"cert_date_{i}")
        # Example: "2024-01-01"

                certifications.append({
                    "certification_name": certification_name,
                    "issuing_company": issuing_company,
                    "issue_date": issue_date,
                })

        # Check for all mandatory fields
        if st.button("Generate PDF Resume"):
            # Validate all fields
            if not full_name:
                st.warning("Please enter your full name!")
            elif not address:
                st.warning("Please enter your address!")
            elif not phone_number:
                st.warning("Please enter your phone number!")
            elif not email:
                st.warning("Please enter your email address!")            
            elif not summary:
                st.warning("Please enter your Professional Summary!")
            elif not any(exp["role"] and exp["company"] and exp["description"] for exp in experiences):  # Ensure role, company, and description are provided
                st.warning("Please enter your Work Experiences with Role, Company, and Description!")
            elif not any(proj["project_name"] and proj["description"] for proj in projects):  # Ensure project details are provided
                st.warning("Please enter your projects!")
            elif not any(edu["degree"] and edu["institution"] for edu in education_records):  # Ensure education details are provided
                st.warning("Please enter your education records!")
            elif not skills:
                st.warning("Please enter your skills!")
            elif not any(cert["certification_name"] and cert["issuing_company"] for cert in certifications):  # Ensure certifications are provided
                st.warning("Please enter your certifications!")
            else:
            # Collect data for PDF generation
                data = {
                    "full_name": full_name,
                    "address": address,
                    "phone_number": phone_number,
                    "email": email,
                    "linkedin_url": linkedin_url,
                    "github_url": github_url,
                    "personal_url": personal_website,                                        
                    "summary": refine_summary(api_key, summary) if summary else "No summary provided.",
                    "experiences": experiences,
                    "projects": projects,
                    "education_records": education_records,
                    "categorized_skills": categorize_skills(skills_list),
                    "certifications": certifications,
                }
        
                # Generate the PDF
                try:
                    pdf_file = generate_pdf(data)  # Ensure generate_pdf is implemented correctly
                    st.success("PDF Resume Generated Successfully!")
                    st.download_button(
                        label="Download Resume",
                        data=open(pdf_file, "rb").read(),
                        file_name="resume.pdf",
                        mime="application/pdf",
                    )
                except Exception as e:
                    st.error(f"An error occurred while generating the resume: {e}")
        
    else:
        st.error("Invalid API Key. Please check and enter a valid API Key.")
else:
    # Provide the link to create a new Gemini API key
    st.write("Don't have an API key? No worries! You can easily create one:")
    st.markdown("[Get Gemini API Key here](https://aistudio.google.com/app/apikey)")
    st.write("After obtaining your API key, enter it above to proceed.")
