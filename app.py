# from st_aggrid import AgGrid
# from st_aggrid.grid_options_builder import GridOptionsBuilder
import streamlit as st
import pandas as pd

import json
import os
import pandas as pd
from dotenv import load_dotenv
import gspread
import warnings
warnings.simplefilter('ignore')
from google.oauth2.service_account import Credentials 
import base64
import hashlib
import hmac
import time
from dotenv import load_dotenv
import extra_streamlit_components as stx


st.set_page_config(page_title='AGPH Search', page_icon="🔍", layout="wide")

# Inject CSS to remove the menu (optional)
hide_menu_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
"""
st.markdown(hide_menu_style, unsafe_allow_html=True)

load_dotenv()
creds_path = os.getenv('CREDS_PATH', 'token.json')
sheets_json_path = os.getenv('SHEETS_JSON_PATH', 'sheets.json')
SECRET_KEY = os.getenv('SECRET_KEY', 'default-secret-key') 

def validate_token():
    # Extract the token from query parameters
    params = st.query_params  # st.query_params for earlier versions
    if 'token' not in params:
        st.error("Access Denied: Login Required")
        st.stop()

    token = params['token']
    try:
        # Split the JWT into header, payload, and signature
        parts = token.split('.')
        if len(parts) != 3:
            raise ValueError("Invalid token format")

        # Decode header and payload
        header = json.loads(base64.urlsafe_b64decode(parts[0] + '==').decode('utf-8'))
        payload = json.loads(base64.urlsafe_b64decode(parts[1] + '==').decode('utf-8'))

        # Verify signature
        signature = base64.urlsafe_b64decode(parts[2] + '==')
        expected_signature = hmac.new(
            SECRET_KEY.encode(),
            f"{parts[0]}.{parts[1]}".encode(),
            hashlib.sha256
        ).digest()

        if not hmac.compare_digest(signature, expected_signature):
            raise ValueError("Invalid token signature")

        # Check expiration (if present)
        if 'exp' in payload and payload['exp'] < time.time():
            raise ValueError("Token has expired")

        # Access payload data (e.g., user and role)
        #st.success(f"Welcome {payload['user']}! Role: {payload['role']}")

    except ValueError as e:
        st.error(f"Access Denied: {e}")
        st.stop()

#validate_token()

# Initialize session state for new visitors
if "visited" not in st.session_state:
    st.session_state.visited = False

# Check if the user is new
if not st.session_state.visited:
    st.toast("Please Wait New Data is being fetched...", icon="ℹ️")  # Notify user
    st.cache_data.clear()  # Clear cache for new visitors
    st.session_state.visited = True  # Mark as visited

def read_sheets_from_json():
    if os.path.exists(sheets_json_path):
        with open(sheets_json_path, 'r') as file:
            return json.load(file)
    return {}

def operations_preprocess(data):
    import pandas as pd

    # Replace empty strings with NaN
    data = data.replace('', pd.NA)
    
    # Drop rows where all elements are NaN
    data = data.dropna(how='all')

    # Convert 'Date' columns to datetime
    date_columns = [
        'Date', 
        'Writing Start Date', 'Writing End Date', 
        'Proofreading Start Date', 'Proofreading End Date', 
        'Formating Start Date', 'Formating End Date'
    ]
    for col in date_columns:
        if col in data.columns:
            # Convert to datetime64[ns] first
            data[col] = pd.to_datetime(data[col], format="%d/%m/%Y", errors='coerce')

    if 'Date' in data.columns:
        
        # Add a column for the month name
        data['Month'] = data['Date'].dt.strftime('%B')

        # Add a column for the days since enrollment
        current_date = pd.Timestamp.now()  # Current datetime
        data['Since Enrolled'] = (current_date - data['Date']).dt.days

    return data

def connect_db():
    try:
        # Use st.cache_resource to only connect once
        @st.cache_resource
        def get_connection():
            return st.connection('mysql', type='sql')
        conn = get_connection()
        return conn
    except Exception as e:
        st.error(f"Error connecting to MySQL: {e}")
        st.stop()

# SQL query to consolidate book data with updated conditions
query = """
SELECT 
    b.book_id AS `Book ID`,
    b.title AS `Book Title`,
    b.date AS `Date`,
    COUNT(ba.author_id) AS `No of Author`,
    MAX(CASE WHEN rn = 1 THEN ba.author_id END) AS `Author Id 1`,
    MAX(CASE WHEN rn = 2 THEN ba.author_id END) AS `Author Id 2`,
    MAX(CASE WHEN rn = 3 THEN ba.author_id END) AS `Author Id 3`,
    MAX(CASE WHEN rn = 4 THEN ba.author_id END) AS `Author Id 4`,
    MAX(CASE WHEN rn = 1 THEN a.name END) AS `Author Name 1`,
    MAX(CASE WHEN rn = 2 THEN a.name END) AS `Author Name 2`,
    MAX(CASE WHEN rn = 3 THEN a.name END) AS `Author Name 3`,
    MAX(CASE WHEN rn = 4 THEN a.name END) AS `Author Name 4`,
    MAX(CASE WHEN rn = 1 THEN ba.author_position END) AS `Position 1`,
    MAX(CASE WHEN rn = 2 THEN ba.author_position END) AS `Position 2`,
    MAX(CASE WHEN rn = 3 THEN ba.author_position END) AS `Position 3`,
    MAX(CASE WHEN rn = 4 THEN ba.author_position END) AS `Position 4`,
    MAX(CASE WHEN rn = 1 THEN ba.corresponding_agent END) AS `Corresponding Author/Agent 1`,
    MAX(CASE WHEN rn = 2 THEN ba.corresponding_agent END) AS `Corresponding Author/Agent 2`,
    MAX(CASE WHEN rn = 3 THEN ba.corresponding_agent END) AS `Corresponding Author/Agent 3`,
    MAX(CASE WHEN rn = 4 THEN ba.corresponding_agent END) AS `Corresponding Author/Agent 4`,
    MAX(CASE WHEN rn = 1 THEN ba.publishing_consultant END) AS `Publishing Consultant 1`,
    MAX(CASE WHEN rn = 2 THEN ba.publishing_consultant END) AS `Publishing Consultant 2`,
    MAX(CASE WHEN rn = 3 THEN ba.publishing_consultant END) AS `Publishing Consultant 3`,
    MAX(CASE WHEN rn = 4 THEN ba.publishing_consultant END) AS `Publishing Consultant 4`,
    MAX(CASE WHEN rn = 1 THEN a.email END) AS `Email Address 1`,
    MAX(CASE WHEN rn = 2 THEN a.email END) AS `Email Address 2`,
    MAX(CASE WHEN rn = 3 THEN a.email END) AS `Email Address 3`,
    MAX(CASE WHEN rn = 4 THEN a.email END) AS `Email Address 4`,
    MAX(CASE WHEN rn = 1 THEN a.phone END) AS `Contact No. 1`,
    MAX(CASE WHEN rn = 2 THEN a.phone END) AS `Contact No. 2`,
    MAX(CASE WHEN rn = 3 THEN a.phone END) AS `Contact No. 3`,
    MAX(CASE WHEN rn = 4 THEN a.phone END) AS `Contact No. 4`,
    CASE 
        WHEN b.writing_end IS NOT NULL 
        AND b.proofreading_end IS NOT NULL 
        AND b.formatting_end IS NOT NULL 
        THEN 'TRUE' 
        ELSE 'FALSE' 
    END AS `Book Complete`,
    CASE WHEN b.apply_isbn = 1 THEN 'TRUE' ELSE 'FALSE' END AS `Apply ISBN`,
    b.isbn AS `ISBN`,
    MAX(CASE WHEN ba.cover_agreement_sent = 1 THEN 'TRUE' ELSE 'FALSE' END) AS `Send Cover Page and Agreement`,
    MAX(CASE WHEN ba.agreement_received = 1 THEN 'TRUE' ELSE 'FALSE' END) AS `Agreement Received`,
    MAX(CASE WHEN ba.digital_book_approved = 1 THEN 'TRUE' ELSE 'FALSE' END) AS `Digital Prof`,
    MAX(CASE WHEN ba.printing_confirmation = 1 THEN 'TRUE' ELSE 'FALSE' END) AS `Confirmation`,
    MAX(CASE WHEN rn = 1 THEN CASE WHEN ba.welcome_mail_sent = 1 THEN 'TRUE' ELSE 'FALSE' END END) AS `Welcome Mail / Confirmation 1`,
    MAX(CASE WHEN rn = 2 THEN CASE WHEN ba.welcome_mail_sent = 1 THEN 'TRUE' ELSE 'FALSE' END END) AS `Welcome Mail / Confirmation 2`,
    MAX(CASE WHEN rn = 3 THEN CASE WHEN ba.welcome_mail_sent = 1 THEN 'TRUE' ELSE 'FALSE' END END) AS `Welcome Mail / Confirmation 3`,
    MAX(CASE WHEN rn = 4 THEN CASE WHEN ba.welcome_mail_sent = 1 THEN 'TRUE' ELSE 'FALSE' END END) AS `Welcome Mail / Confirmation 4`,
    MAX(CASE WHEN rn = 1 THEN CASE WHEN ba.author_details_sent = 1 THEN 'TRUE' ELSE 'FALSE' END END) AS `Author Detail 1`,
    MAX(CASE WHEN rn = 2 THEN CASE WHEN ba.author_details_sent = 1 THEN 'TRUE' ELSE 'FALSE' END END) AS `Author Detail 2`,
    MAX(CASE WHEN rn = 3 THEN CASE WHEN ba.author_details_sent = 1 THEN 'TRUE' ELSE 'FALSE' END END) AS `Author Detail 3`,
    MAX(CASE WHEN rn = 4 THEN CASE WHEN ba.author_details_sent = 1 THEN 'TRUE' ELSE 'FALSE' END END) AS `Author Detail 4`,
    MAX(CASE WHEN rn = 1 THEN CASE WHEN ba.photo_recive = 1 THEN 'TRUE' ELSE 'FALSE' END END) AS `Photo 1`,
    MAX(CASE WHEN rn = 2 THEN CASE WHEN ba.photo_recive = 1 THEN 'TRUE' ELSE 'FALSE' END END) AS `Photo 2`,
    MAX(CASE WHEN rn = 3 THEN CASE WHEN ba.photo_recive = 1 THEN 'TRUE' ELSE 'FALSE' END END) AS `Photo 3`,
    MAX(CASE WHEN rn = 4 THEN CASE WHEN ba.photo_recive = 1 THEN 'TRUE' ELSE 'FALSE' END END) AS `Photo 4`,
    MAX(CASE WHEN rn = 1 THEN CASE WHEN ba.id_proof_recive = 1 THEN 'TRUE' ELSE 'FALSE' END END) AS `ID Proof 1`,
    MAX(CASE WHEN rn = 2 THEN CASE WHEN ba.id_proof_recive = 1 THEN 'TRUE' ELSE 'FALSE' END END) AS `ID Proof 2`,
    MAX(CASE WHEN rn = 3 THEN CASE WHEN ba.id_proof_recive = 1 THEN 'TRUE' ELSE 'FALSE' END END) AS `ID Proof 3`,
    MAX(CASE WHEN rn = 4 THEN CASE WHEN ba.id_proof_recive = 1 THEN 'TRUE' ELSE 'FALSE' END END) AS `ID Proof 4`,
    b.cover_by AS `Cover Page`,
    NULL AS `Back Page Update`,
    MAX(CASE WHEN rn = 1 THEN CASE WHEN ba.cover_agreement_sent = 1 THEN 'TRUE' ELSE 'FALSE' END END) AS `Send Cover Page and Agreement 1`,
    MAX(CASE WHEN rn = 2 THEN CASE WHEN ba.cover_agreement_sent = 1 THEN 'TRUE' ELSE 'FALSE' END END) AS `Send Cover Page and Agreement 2`,
    MAX(CASE WHEN rn = 3 THEN CASE WHEN ba.cover_agreement_sent = 1 THEN 'TRUE' ELSE 'FALSE' END END) AS `Send Cover Page and Agreement 3`,
    MAX(CASE WHEN rn = 4 THEN CASE WHEN ba.cover_agreement_sent = 1 THEN 'TRUE' ELSE 'FALSE' END END) AS `Send Cover Page and Agreement 4`,
    MAX(CASE WHEN rn = 1 THEN CASE WHEN ba.agreement_received = 1 THEN 'TRUE' ELSE 'FALSE' END END) AS `Agreement Received 1`,
    MAX(CASE WHEN rn = 2 THEN CASE WHEN ba.agreement_received = 1 THEN 'TRUE' ELSE 'FALSE' END END) AS `Agreement Received 2`,
    MAX(CASE WHEN rn = 3 THEN CASE WHEN ba.agreement_received = 1 THEN 'TRUE' ELSE 'FALSE' END END) AS `Agreement Received 3`,
    MAX(CASE WHEN rn = 4 THEN CASE WHEN ba.agreement_received = 1 THEN 'TRUE' ELSE 'FALSE' END END) AS `Agreement Received 4`,
    MAX(CASE WHEN rn = 1 THEN CASE WHEN ba.digital_book_approved = 1 THEN 'TRUE' ELSE 'FALSE' END END) AS `Digital Prof 1`,
    MAX(CASE WHEN rn = 2 THEN CASE WHEN ba.digital_book_approved = 1 THEN 'TRUE' ELSE 'FALSE' END END) AS `Digital Prof 2`,
    MAX(CASE WHEN rn = 3 THEN CASE WHEN ba.digital_book_approved = 1 THEN 'TRUE' ELSE 'FALSE' END END) AS `Digital Prof 3`,
    MAX(CASE WHEN rn = 4 THEN CASE WHEN ba.digital_book_approved = 1 THEN 'TRUE' ELSE 'FALSE' END END) AS `Digital Prof 4`,
    MAX(CASE WHEN rn = 1 THEN CASE WHEN ba.printing_confirmation = 1 THEN 'TRUE' ELSE 'FALSE' END END) AS `Confirmation 1`,
    MAX(CASE WHEN rn = 2 THEN CASE WHEN ba.printing_confirmation = 1 THEN 'TRUE' ELSE 'FALSE' END END) AS `Confirmation 2`,
    MAX(CASE WHEN rn = 3 THEN CASE WHEN ba.printing_confirmation = 1 THEN 'TRUE' ELSE 'FALSE' END END) AS `Confirmation 3`,
    MAX(CASE WHEN rn = 4 THEN CASE WHEN ba.printing_confirmation = 1 THEN 'TRUE' ELSE 'FALSE' END END) AS `Confirmation 4`,
    CASE WHEN b.ready_to_print = 1 THEN 'TRUE' ELSE 'FALSE' END AS `Ready to Print`,
    b.print_status AS `Print`,
    b.amazon_link AS `Amazon Link`,
    b.agph_link AS `AGPH Link`,
    b.google_link AS `Google Link`,
    b.flipkart_link AS `Flipkart Link`,
    NULL AS `Final Mail`,
    CASE WHEN b.deliver = 1 THEN 'TRUE' ELSE 'FALSE' END AS `Deliver`,
    b.google_review AS `Google Review`,
    NULL AS `Remark`,
    MAX(ba.delivery_date) AS `Delivery Date`,
    CASE WHEN b.writing_end IS NOT NULL THEN 'TRUE' ELSE 'FALSE' END AS `Writing Complete`,
    b.writing_by AS `Writing By`,
    b.writing_start AS `Writing Start Date`,
    TIME(b.writing_start) AS `Writing Start Time`,
    b.writing_end AS `Writing End Date`,
    TIME(b.writing_end) AS `Writing End Time`,
    CASE WHEN b.proofreading_end IS NOT NULL THEN 'TRUE' ELSE 'FALSE' END AS `Proofreading Complete`,
    b.proofreading_by AS `Proofreading By`,
    b.proofreading_start AS `Proofreading Start Date`,
    TIME(b.proofreading_start) AS `Proofreading Start Time`,
    b.proofreading_end AS `Proofreading End Date`,
    TIME(b.proofreading_end) AS `Proofreading End Time`,
    CASE WHEN b.formatting_end IS NOT NULL THEN 'TRUE' ELSE 'FALSE' END AS `Formating Complete`,
    b.formatting_by AS `Formating By`,
    b.formatting_start AS `Formating Start Date`,
    TIME(b.formatting_start) AS `Formating Start Time`,
    b.formatting_end AS `Formating End Date`,
    TIME(b.formatting_end) AS `Formating End Time`,
    MONTHNAME(b.date) AS `Month`,
    YEAR(b.date) AS `Year`,
    DATEDIFF(CURDATE(), b.date) AS `Since Enrolled`
FROM books b
LEFT JOIN (
    SELECT 
        ba.*,
        ROW_NUMBER() OVER (PARTITION BY ba.book_id ORDER BY ba.author_position, ba.id) AS rn
    FROM book_authors ba
) ba ON b.book_id = ba.book_id AND ba.rn <= 4
LEFT JOIN authors a ON ba.author_id = a.author_id
GROUP BY b.book_id, b.title, b.date, b.apply_isbn, b.isbn, b.ready_to_print, b.print_status, b.deliver, 
         b.google_review, b.flipkart_link, b.google_link, b.agph_link, b.amazon_link, 
         b.writing_by, b.proofreading_by, b.formatting_by, b.writing_start, b.writing_end, 
         b.proofreading_start, b.proofreading_end, b.formatting_start, b.formatting_end, 
         b.cover_by
ORDER BY b.book_id;
"""

with st.spinner("Data fetching in progress...", show_time=False):
    conn = connect_db()
    df = conn.query(query, show_spinner=False)

try:
    # Fetch data from a Google Sheet
    @st.cache_data(show_spinner=False)
    def fetch_operations_sheet_data(sheet_id):
        worksheet = gc.open_by_key(sheet_id).sheet1
        data = worksheet.get_all_records()
        return pd.DataFrame(data)

    scope = ["https://www.googleapis.com/auth/spreadsheets"]
    credentials = Credentials.from_service_account_file(creds_path, scopes = scope)
    gc = gspread.authorize(credentials)
    sheets = read_sheets_from_json()

    with st.spinner("Loading operations data..."):
        operations_data = fetch_operations_sheet_data(sheets['Operations'])
        operations_data = operations_preprocess(operations_data)

    # Function to get book and author details with error handling
    def get_book_and_author_details(book_info):
        try:
            book_details = []
            no_of_authors = int(book_info.get('No of Author', 0))  # Use `.get` to handle missing keys
            
            for i in range(1, no_of_authors + 1):
                # Safely get author details
                author_data = {
                    "Author ID": book_info.get(f'Author Id {i}', None),
                    "Author Name": book_info.get(f'Author Name {i}', None),
                    "Position": book_info.get(f'Position {i}', None),
                    "Email": book_info.get(f'Email Address {i}', None),
                    "Contact": book_info.get(f'Contact No. {i}', None),
                    "Publishing Consultant": book_info.get(f'Publishing Consultant {i}', None),
                    "Welcome Mail": book_info.get(f'Welcome Mail / Confirmation {i}', None),
                    "Author Detail": book_info.get(f'Author Detail {i}', None),
                    "Photo": book_info.get(f'Photo {i}', None),
                    "ID Proof": book_info.get(f'ID Proof {i}', None),
                    "Send Cover Page": book_info.get(f'Send Cover Page and Agreement {i}', None),
                    "Agreement Received": book_info.get(f'Agreement Received {i}', None),
                    "Digital Prof": book_info.get(f'Digital Prof {i}', None),
                    "Confirmation": book_info.get(f'Confirmation {i}', None),
                }
                book_details.append(author_data)
            return book_details
        except Exception:
            st.error("Something went wrong while retrieving author details.")
            return []


    # Initialize session state for the text input field
    if "previous_search_column" not in st.session_state:
        st.session_state["previous_search_column"] = ""
    if "search_query" not in st.session_state:
        st.session_state["search_query"] = ""

    # Title
    st.title("📚 AGPH Advance Search")

    # Columns for search inputs
    col1, col2 = st.columns(2)

    # Dropdown for selecting the search column
    with col1:
        search_column = st.selectbox(
            "🗃️ Select Column to Search:", 
            ['Book ID', 'Book Title', 'Author Name', 'ISBN']
        )

    # Check if the selected column has changed
    if search_column != st.session_state["previous_search_column"]:
        # Reset the search query if the column changes
        st.session_state["search_query"] = ""
        st.session_state["previous_search_column"] = search_column

    # Text input for search query
    with col2:
        search_query = st.text_input(
            "🔍 Enter your search term:", 
            value=st.session_state["search_query"],
            key="search_query"
        )

    # Filter results
    filtered_data = pd.DataFrame()
    try:
        if search_query:
            if search_column == "Author Name":
                # Logic for Author Name
                mask = (operations_data['Author Name 1'].str.contains(search_query, case=False, na=False) |
                        operations_data['Author Name 2'].str.contains(search_query, case=False, na=False) |
                        operations_data['Author Name 3'].str.contains(search_query, case=False, na=False) |
                        operations_data['Author Name 4'].str.contains(search_query, case=False, na=False))
                filtered_data = operations_data[mask]
            elif search_column == "Book Title":
                # Logic for Book Title
                filtered_data = operations_data[
                    operations_data['Book Title'].str.contains(search_query, case=False, na=False)
                ]
            elif search_column == "Book ID":
                # Logic for Book ID
                try:
                    book_id = int(search_query)
                    filtered_data = operations_data[operations_data['Book ID'] == book_id]
                except ValueError:
                    st.error("Book ID must be a number!")
            elif search_column == "ISBN":
                # Logic for ISBN
                operations_data['ISBN'] = operations_data['ISBN'].astype(str).str.strip()
                filtered_data = operations_data[operations_data['ISBN'] == search_query]
    except Exception:
        st.error("Something went wrong while processing your search query.")


    # full dataframe search
    # mask = operations.apply(lambda row: row.astype(str).str.contains(search_string, case=False, na=False).any(), axis=1)
    # result = operations[mask]

    # Display results
    if not filtered_data.empty:
        st.success(f"Found {len(filtered_data)} results for '{search_query}' in '{search_column}'")

        for _, book in filtered_data.iterrows():
            # Determine book status
            deliver_status = str(book['Deliver']).strip().lower()
            status = "Pending" if deliver_status == "false" else "Delivered"
            status_color = "#ff6b6b" if status == "Pending" else "#51cf66"

            # Handle missing ISBN
            
            isbn_display = (
                            str(book['ISBN']).lower().strip()
                            if pd.notna(book['ISBN']) and str(book['ISBN']).lower().strip() != "nan" and book['ISBN'] != ""
                            else "<span style='color:#ff6b6b;font-weight:bold;'>Pending</span>"
                        )

            # Helper function for highlighting boolean values
            def highlight_boolean(value):
                value = str(value).strip().lower()
                if value == "true":
                    return "<span style='color: #51cf66; font-weight: bold;'> Yes</span>"
                else:
                    return "<span style='color: #ff6b6b; font-weight: bold;'> No</span>"

            def generate_link_icons(book):
                icons = {
                    "Amazon Link": "https://img.icons8.com/color/48/000000/amazon.png",
                    "Google Link": "https://img.icons8.com/color/48/000000/google-logo.png",
                    "Flipkart Link": "https://img.icons8.com/?size=100&id=UU2im0hihoyi&format=png&color=000000",
                    "AGPH Link": "https://img.icons8.com/ios-filled/50/000000/open-book.png",
                }
                links_html = ""
                for column, icon_url in icons.items():
                    # Safely retrieve the link and handle missing or invalid values
                    link = book.get(column, None)
                    if link is not None and pd.notna(link) and str(link).strip() != "":
                        links_html += f"<a href='{str(link).strip()}' target='_blank'><img src='{icon_url}' alt='{column}' style='width:24px; margin-right:8px;'></a>"
                return links_html


            with st.container():
                st.markdown(
                    f"""
                    <div style="
                        background-color: #f8f9fa;
                        padding: 20px;
                        border-radius: 12px;
                        margin-bottom: 20px;
                        box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.1);
                        border: 1px solid #dee2e6;
                        font-family: 'Arial', sans-serif;">
                        <h3 style="
                            color: #495057;
                            background-color: #e9ecef;
                            padding: 10px 15px;
                            border-radius: 8px;
                            margin-bottom: 20px;
                            font-weight: 600;
                            text-align: center;">
                            📖 {book['Book Title']}
                            <span style="
                                background-color: {status_color};
                                color: white;
                                padding: 5px 10px;
                                border-radius: 15px;
                                font-size: 14px;
                                margin-left: 10px;">
                                {status}
                            </span>
                        </h3>
                        <div style="
                            display: grid;
                            grid-template-columns: repeat(3, 1fr);
                            gap: 20px;
                            font-size: 14px;
                            color: #343a40;">
                            <div>
                                <p>🔖 <b>Book ID:</b> {book['Book ID']}</p>
                                <p>📚 <b>ISBN:</b> {isbn_display}</p>
                                <p>📅 <b>Enroll Date:</b> {book['Date']}</p>
                                <p>🗓️ <b>Book Month:</b> {book['Month']}</p>
                                <p>⌛ <b>Since Enrolled:</b> {book['Since Enrolled']}</p>
                            </div>
                            <div>
                                <p>👥 <b>No of Authors:</b> {book['No of Author']}</p>
                                <p>✅ <b>Book Done:</b> {highlight_boolean(book['Book Complete'])}</p>
                                <p>📄 <b>Agreement Received:</b> {highlight_boolean(book['Agreement Received'])}</p>
                                <p>📤 <b>Send Cover Page:</b> {highlight_boolean(book['Send Cover Page and Agreement'])}</p>
                                <p>🖼️ <b>Digital Prof:</b> {highlight_boolean(book['Digital Prof'])}</p>
                            </div>
                            <div>
                                <p>🔔 <b>Confirmation:</b> {highlight_boolean(book['Confirmation'])}</p>
                                <p>🖨️ <b>Ready to Print:</b> {highlight_boolean(book['Ready to Print'])}</p>
                                <p>📦 <b>Print:</b> {highlight_boolean(book['Print'])}</p>
                                <p>🚚 <b>Deliver:</b> {highlight_boolean(book['Deliver'])}</p>
                                <div><p>🔗 <b>Links:</b> {generate_link_icons(book)}</p></div>
                            </div>
                            </div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                # Expandable section for author details
                with st.expander("📋 View Author Details"):
                    authors = get_book_and_author_details(book)  # Fetch authors details
                    total_authors = len(authors)

                    # Helper function to highlight boolean values
                    def highlight_boolean(value):
                        value = str(value).strip().lower()
                        if value == "true":
                            return "<span style='color: #51cf66; font-weight: bold;'>Yes</span>"
                        else:
                            return "<span style='color: #ff6b6b; font-weight: bold;'>No</span>"

                    # Create a 4-column layout for author cards
                    for idx, author in enumerate(authors, start=1):
                        if idx % 4 == 1:  # Start a new row for every 4 authors
                            cols = st.columns(4)  # Create 4 columns

                        # Card content
                        with cols[(idx - 1) % 4]:
                            st.markdown(
                                f"""
                                <div style="
                                    background-color: #ffffff;
                                    border-radius: 12px;
                                    box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.1);
                                    padding: 15px;
                                    margin-bottom: 20px;
                                    border: 1px solid #dee2e6;
                                    font-family: 'Arial', sans-serif;">
                                    <h4 style="
                                        color: #495057;
                                        background-color: #e9ecef;
                                        padding: 10px;
                                        border-radius: 8px;
                                        margin-bottom: 15px;
                                        text-align: center;">
                                        Author {idx} 
                                        <span style="font-size: 14px; font-weight: 400; color: #868e96;">
                                            ({author['Position']})
                                        </span>
                                    </h4>
                                    <p style="font-size: 16px; font-weight: bold; color: #1c7ed6; margin-bottom: 10px;">
                                        {author['Author Name']}
                                    </p>
                                    <p><b>Author ID:</b> {author['Author ID']}</p>
                                    <p><b>Email:</b> {author['Email']}</p>
                                    <p><b>Contact:</b> {author['Contact']}</p>
                                    <p><b>Publishing Consultant:</b> 
                                    <span style="color:rgb(236, 116, 35); font-weight: bold;">{author['Publishing Consultant']}</span>
                                    </p>
                                    <p><b>Welcome Mail:</b> {highlight_boolean(author['Welcome Mail'])}</p>
                                    <p><b>Photo:</b> {highlight_boolean(author['Photo'])}</p>
                                    <p><b>ID Proof:</b> {highlight_boolean(author['ID Proof'])}</p>
                                    <p><b>Send Cover Page:</b> {highlight_boolean(author['Send Cover Page'])}</p>
                                    <p><b>Agreement Received:</b> {highlight_boolean(author['Agreement Received'])}</p>
                                    <p><b>Digital Profile:</b> {highlight_boolean(author['Digital Prof'])}</p>
                                    <p><b>Confirmation:</b> {highlight_boolean(author['Confirmation'])}</p>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )

                def handle_missing(value):
                    if pd.isna(value) or str(value).strip().lower() in ["nan", ""]:
                        return "<span style='color: #ff6b6b; font-weight: bold;'>Pending</span>"
                    return value

                with st.expander("📘 Operation Details"):
                    # Layout: Three cards in a row
                    col1, col2, col3 = st.columns(3)

                    # Writing Details
                    with col1:
                        status = "Done" if book['Writing Complete'] == "TRUE" else "Pending"
                        status_color = "#51cf66" if status == "Done" else "#ff6b6b"
                        st.markdown(
                            f"""
                            <div style="
                                background-color: #ffffff;
                                border-radius: 12px;
                                box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.1);
                                padding: 15px;
                                margin-bottom: 20px;
                                border: 1px solid #dee2e6;
                                font-family: 'Arial', sans-serif;">
                                <h4 style="
                                    color: #495057;
                                    background-color: #e9ecef;
                                    padding: 10px;
                                    border-radius: 8px;
                                    margin-bottom: 15px;
                                    text-align: center;
                                    font-size: 20px;">
                                    ✍️ Writing Details 
                                    <span style="
                                    background-color: {status_color};
                                    color: white;
                                    padding: 5px 10px;
                                    border-radius: 15px;
                                    font-size: 12px;
                                    margin-left: 10px;">
                                    {status}
                                </span>
                                </h4>
                                <div style="font-size: 14px; color: #495057; line-height: 1.6;">
                                    <p><b>Writing Complete:</b> {highlight_boolean(book['Writing Complete'])}</p>
                                    <p><b>Written By:</b> 
                                        <span style="color: #1c7ed6; font-weight: bold;">{handle_missing(book['Writing By'])}</span>
                                    </p>
                                    <p><b>Start Date:</b> {handle_missing(book['Writing Start Date'])}</p>
                                    <p><b>Start Time:</b> {handle_missing(book['Writing Start Time'])}</p>
                                    <p><b>End Date:</b> {handle_missing(book['Writing End Date'])}</p>
                                    <p><b>End Time:</b> {handle_missing(book['Writing End Time'])}</p>
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                    # Proofreading Details
                    with col2:
                        status = "Done" if book['Proofreading Complete'] == "TRUE" else "Pending"
                        status_color = "#51cf66" if status == "Done" else "#ff6b6b"
                        st.markdown(
                            f"""
                            <div style="
                                background-color: #ffffff;
                                border-radius: 12px;
                                box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.1);
                                padding: 15px;
                                margin-bottom: 20px;
                                border: 1px solid #dee2e6;
                                font-family: 'Arial', sans-serif;">
                                <h4 style="
                                    color: #495057;
                                    background-color: #e9ecef;
                                    padding: 10px;
                                    border-radius: 8px;
                                    margin-bottom: 15px;
                                    text-align: center;
                                    font-size: 20px;">
                                    📝 Proofreading Details 
                                    <span style="
                                        background-color: {status_color};
                                        color: white;
                                        padding: 5px 10px;
                                        border-radius: 15px;
                                        font-size: 12px;
                                        margin-left: 10px;">
                                        {status}
                                    </span>
                                </h4>
                                <div style="font-size: 14px; color: #495057; line-height: 1.6;">
                                    <p><b>Proofreading Complete:</b> {highlight_boolean(book['Proofreading Complete'])}</p>
                                    <p><b>Proofread By:</b> 
                                        <span style="color: #1c7ed6; font-weight: bold;">{handle_missing(book['Proofreading By'])}</span>
                                    </p>
                                    <p><b>Start Date:</b> {handle_missing(book['Proofreading Start Date'])}</p>
                                    <p><b>Start Time:</b> {handle_missing(book['Proofreading Start Time'])}</p>
                                    <p><b>End Date:</b> {handle_missing(book['Proofreading End Date'])}</p>
                                    <p><b>End Time:</b> {handle_missing(book['Proofreading End Time'])}</p>
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                    # Formatting Details
                    with col3:
                        status = "Done" if book['Formating Complete'] == "TRUE" else "Pending"
                        status_color = "#51cf66" if status == "Done" else "#ff6b6b"
                        st.markdown(
                            f"""
                            <div style="
                                background-color: #ffffff;
                                border-radius: 12px;
                                box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.1);
                                padding: 15px;
                                margin-bottom: 20px;
                                border: 1px solid #dee2e6;
                                font-family: 'Arial', sans-serif;">
                                <h4 style="
                                    color: #495057;
                                    background-color: #e9ecef;
                                    padding: 10px;
                                    border-radius: 8px;
                                    margin-bottom: 15px;
                                    text-align: center;
                                    font-size: 20px;">
                                    📂 Formatting Details 
                                    <span style="
                                        background-color: {status_color};
                                        color: white;
                                        padding: 5px 10px;
                                        border-radius: 15px;
                                        font-size: 12px;
                                        margin-left: 10px;">
                                        {status}
                                    </span>
                                </h4>
                                <div style="font-size: 14px; color: #495057; line-height: 1.6;">
                                    <p><b>Formatting Complete:</b> {highlight_boolean(book['Formating Complete'])}</p>
                                    <p><b>Formatted By:</b> 
                                        <span style="color: #1c7ed6; font-weight: bold;">{handle_missing(book['Formating By'])}</span>
                                    </p>
                                    <p><b>Start Date:</b> {handle_missing(book['Formating Start Date'])}</p>
                                    <p><b>Start Time:</b> {handle_missing(book['Formating Start Time'])}</p>
                                    <p><b>End Date:</b> {handle_missing(book['Formating End Date'])}</p>
                                    <p><b>End Time:</b> {handle_missing(book['Formating End Time'])}</p>
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )


    else:
        if search_query:
            st.error(f"No results found for '{search_query}' in '{search_column}'")
        else:
            st.info("Enter a search term to begin.")

except Exception as e:
    st.error(f"An error occurred: {e}")
    st.error("Likely Data is not Correctly Filled in MasterSheet")


# # Step 1: Identify date columns
# date_columns = [col for col in master_data.columns if "Date" in col or "date" in col.lower()]

# if date_columns:
#     # Use st.columns to arrange widgets side by side
#      1:
#         selected_date_col = st.selectbox("Select a date column to filter by:", date_columns)
#     with col2:
#         # Ensure the selected column is in datetime format
#         master_data[selected_date_col] = pd.to_datetime(master_data[selected_date_col], errors='coerce')
#         start_date = st.date_input("Start Date", value=master_data[selected_date_col].min().date())
    
#     # Date range filter
#     col3, col4 = st.columns(2)
#     with col3:
#         end_date = st.date_input("End Date", value=master_data[selected_date_col].max().date())
#     with col4:
#         search_value = st.text_input("Search for a value (case-insensitive):")
        
#     # Filter DataFrame by date range
#     master_data = master_data[(master_data[selected_date_col] >= pd.Timestamp(start_date)) & 
#             (master_data[selected_date_col] <= pd.Timestamp(end_date))]
    

# if search_value:
#     # Filter DataFrame by search value
#     master_data = master_data[master_data.astype(str).apply(lambda row: row.str.contains(search_value, case=False).any(), axis=1)]

# # Step 3: Configure AgGrid
# gb = GridOptionsBuilder.from_dataframe(master_data)
# gb.configure_column("Book ID", rowGroup=True, hide=True)
# gb.configure_pagination(enabled=True,paginationPageSize=15)  # Enable pagination
# gb.configure_default_column(editable=False, filterable=True, sorteable = True, groupable = True)
# gb.configure_auto_height(autoHeight = True)
# gb.configure_side_bar(filters_panel=True, columns_panel=True)
# gb.configure_grid_options(domLayout='normal', enableRowGroup=True, groupSelectsChildren=True, groupDefaultExpanded=-1)


# # Add JavaScript for column auto-sizing
# custom_js = """
# function autoSizeAllColumns(gridOptions) {
#     const allColumnIds = [];
#     gridOptions.columnApi.getAllColumns().forEach((column) => {
#         allColumnIds.push(column.colId);
#     });
#     gridOptions.columnApi.autoSizeColumns(allColumnIds);
# }
# autoSizeAllColumns(gridOptions);
# """

# # Add JS customization
# gb.configure_grid_options(onGridReady=custom_js)

# grid_options = gb.build()

# # Step 4: Display AgGrid
# response = AgGrid(
#     master_data,
#      height=500,
#     gridOptions=grid_options,
#     update_mode="MODEL_CHANGED",
#      fit_columns_on_grid_load=True,
#     allow_unsafe_jscode=True # Theme options: "streamlit", "material", etc.
# )

# st.data_editor(df,
#     column_config={
#         "Print": st.column_config.CheckboxColumn(
#             "Print",
#             default=False,
#         )
#     },
#     disabled =True,
#     hide_index=True,)


# import streamlit as st
# import pandas as pd

# import streamlit as st
# import pandas as pd
# from st_aggrid import AgGrid, GridOptionsBuilder

# # # Example book data
# # books_data = [
# #     {"Book ID": 1, "Book Title": "Book A", "Author": "Author 1", "Role": "Main Author"},
# #     {"Book ID": 2, "Book Title": "Book B", "Author": "Author 2", "Role": "Main Author"},
# #     {"Book ID": 3, "Book Title": "Book C", "Author": "Author 3", "Role": "Main Author"},
# # ]

# # # Example author details
# # authors_data = [
# #     {"Book ID": 1, "Book Title": "", "Author": "Author 1", "Role": "Editor"},
# #     {"Book ID": 1, "Book Title": "", "Author": "Author 2", "Role": "Writer"},
# #     {"Book ID": 1, "Book Title": "", "Author": "Author 3", "Role": "Reviewer"},
# #     {"Book ID": 2, "Book Title": "", "Author": "Author 4", "Role": "Editor"},
# #     {"Book ID": 2, "Book Title": "", "Author": "Author 5", "Role": "Writer"},
# #     {"Book ID": 2, "Book Title": "", "Author": "Author 6", "Role": "Reviewer"},
# #     {"Book ID": 3, "Book Title": "", "Author": "Author 7", "Role": "Editor"},
# # ]

# # # Combine data
# # all_data = books_data + authors_data
# df = pd.DataFrame(master_data)

# # Configure AgGrid
# builder = GridOptionsBuilder.from_dataframe(df)

# # Enable row grouping by "Book ID" and "Book Title"
# builder.configure_column("Book ID", rowGroup=True, hide=True)
# # builder.configure_column("Book Title", rowGroup=True, hide=True)
# # builder.configure_column("Author", editable=False)

# builder.configure_pagination(enabled=True,paginationPageSize=20)  # Enable pagination
# builder.configure_default_column(editable=False, filterable=True, sorteable = True, groupable = True)
# builder.configure_auto_height(autoHeight = True)
# builder.configure_side_bar(filters_panel=True, columns_panel=True)
# builder.configure_grid_options(domLayout='normal') 

# # Allow expandable rows
# builder.configure_grid_options(enableRowGroup=True, groupSelectsChildren=True, groupDefaultExpanded=0)
# builder.configure_grid_options(onGridReady=custom_js)

# # Build the grid options
# grid_options = builder.build()

# # Display the AgGrid table
# st.write("📚 Books and Authors Table with Collapsible Rows")
# AgGrid(
#     df,
#     gridOptions=grid_options,
#     height=400,
#     fit_columns_on_grid_load=True,
#     allow_unsafe_jscode=True
# )



val = stx.stepper_bar(steps=["Ready", "Get Set", "Go","Ok", "Done","Break"],)
st.info(f"Phase #{val}")
