import requests
import pdfplumber
import re
import logging
import msal
import os

# Install required packages
# !pip install pdfplumber msal

class AIUBPDFScraper:
    def __init__(self):
        """Initialize scraper"""
        self.base_url = "https://www.aiub.edu"
        self.setup_logging()

    def setup_logging(self):
        """Setup basic logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def download_pdf(self, pdf_url: str) -> bytes:
        """Download PDF from AIUB website"""
        try:
            full_url = os.path.join(self.base_url, pdf_url)
            self.logger.info(f"Downloading PDF from: {full_url}")
            response = requests.get(full_url)
            response.raise_for_status()
            self.logger.info("PDF downloaded successfully")
            return response.content
        except Exception as e:
            self.logger.error(f"Error downloading PDF: {str(e)}")
            return None

    def extract_student_ids(self, pdf_content: bytes):
        """Extract student IDs from the PDF content"""
        student_ids = []
        pattern = r'\b\d{2}-\d{5}-\d\b'  # Match student ID format
        try:
            with open('temp.pdf', 'wb') as f:
                f.write(pdf_content)

            with pdfplumber.open('temp.pdf') as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if 'ENGLISH WRITING SKILLS & COMMUNICATIONS' in text.upper():
                        matches = re.finditer(pattern, text)
                        student_ids.extend([match.group() for match in matches])

            os.remove('temp.pdf')
            return list(set(student_ids))
        except Exception as e:
            self.logger.error(f"Error extracting student IDs: {str(e)}")
            return []

    def send_teams_message(self, email, password, message):
        """Authenticate and send message to student"""
        client_id = 'your-client-id'  # Your registered application client ID
        client_secret = 'your-client-secret'  # Your registered application client secret
        authority = 'https://login.microsoftonline.com/common'

        # Create MSAL app instance for username/password flow
        app = msal.PublicClientApplication(client_id, authority=authority)

        # Try to acquire token using username and password
        result = app.acquire_token_by_username_password(
            username=f"{email}@student.aiub.edu",
            password=password,
            scopes=["User.Read", "Chat.ReadWrite"]
        )

        if "access_token" in result:
            self.logger.info("Authentication successful")
            # Use the token to call Microsoft Graph API (Teams messages)
            # Your token is in result['access_token']
            # Send Teams message using the access token (you will need to interact with Graph API directly)
            full_email = f"{email}@student.aiub.edu"  # Ensure full email format
            # Teams messaging API would go here
            self.logger.info(f"Message would be sent to {full_email}: {message}")
        else:
            self.logger.error("Authentication failed. Please check your username and password.")
            self.logger.error(f"Error: {result.get('error_description')}")


def main():
    # Input credentials
    teams_email = input("Enter your Microsoft Teams email (without @student.aiub.edu): ")
    teams_password = input("Enter your Microsoft Teams password: ")

    # Scraping setup
    CONFIG = {
        'pdf_url': 'Files/Uploads/day-3-slot-3-mid_fall-24-25.pdf',
    }

    scraper = AIUBPDFScraper()

    # Download and extract student IDs from the PDF
    pdf_content = scraper.download_pdf(CONFIG['pdf_url'])
    if pdf_content:
        student_ids = scraper.extract_student_ids(pdf_content)
        if student_ids:
            print(f"Found {len(student_ids)} student IDs: {student_ids}")

            # Get the message from the user
            message = input("Enter the message to send: ")

            # Send the message to the test student (full email address)
            scraper.send_teams_message(teams_email, teams_password, message)
        else:
            print("No student IDs found")
    else:
        print("Failed to download PDF")


# Run the script
if __name__ == "__main__":
    main()
