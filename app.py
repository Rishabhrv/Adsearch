from st_aggrid import AgGrid
from st_aggrid.grid_options_builder import GridOptionsBuilder
import streamlit as st
import pandas as pd

st.set_page_config(page_title='Advance search', page_icon=None, layout="wide")


# Load your dataset
operations_data = pd.read_csv("operations_data.csv")
master_data = pd.read_csv('master_data.csv')

import streamlit as st
import pandas as pd

# Function to get book and author details
def get_book_and_author_details(book_info):
    book_details = []
    no_of_authors = int(book_info['No of Author'])
    
    for i in range(1, no_of_authors + 1):
        # Safely get author details
        author_data = {
            "Author ID": book_info.get(f'Author Id {i}', None),
            "Author Name": book_info.get(f'Author Name {i}', None),
            "Position": book_info.get(f'Position {i}', None),
            "Email": book_info.get(f'Email Address {i}', None),
            "Contact": book_info.get(f'Contact No. {i}', None),
            "Welcome Mail": book_info.get(f'Welcome Mail / Confirmation {i}', None),
            "Author Detail": book_info.get(f'Author Detail {i}', None),
            "Photo": book_info.get(f'Photo {i}', None),
            "ID Proof": book_info.get(f'ID Proof {i}', None),
            "Send Cover Page": book_info.get(f'Send Cover Page and Agreement {i}', None),
            "Agreement Received": book_info.get(f'Agreement Received {i}', None),
            "Digital Prof": book_info.get(f'Digital Prof {i}', None),
            "Plagiarism Report": book_info.get(f'Plagiarism Report {i}', None),
            "Confirmation": book_info.get(f'Confirmation {i}', None),
        }
        book_details.append(author_data)
    return book_details


# Streamlit App
st.title("📚 AGPH Advance Search")

# Columns for search inputs
col1, col2 = st.columns(2)

with col1:
    search_column = st.selectbox("🗃️ Select Column to Search:", ['Book ID', 'Book Title', 'Author Name', 'ISBN'])
with col2:
    search_query = st.text_input("🔍 Enter your search term:")

# Filter results
filtered_data = pd.DataFrame()
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

# Display results
if not filtered_data.empty:
    st.success(f"Found {len(filtered_data)} results for '{search_query}' in '{search_column}'")

    for _, book in filtered_data.iterrows():
        # Determine book status
        deliver_status = str(book['Deliver']).strip().lower()
        status = "Pending" if deliver_status == "false" else "Delivered"
        status_color = "#ff6b6b" if status == "Pending" else "#51cf66"

        # Handle missing ISBN
        
        isbn_display = (str(book['ISBN']).lower().strip() if str(book['ISBN']).lower().strip() != "nan" and book['ISBN'] != "" 
                        else "<span style='color:#ff6b6b;font-weight:bold;'>Pending</span>")

        # Helper function for highlighting boolean values
        def highlight_boolean(value):
            value = str(value).strip().lower()
            if value == "true":
                return "<span style='color: #51cf66; font-weight: bold;'> Yes</span>"
            else:
                return "<span style='color: #ff6b6b; font-weight: bold;'> No</span>"

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
                            <p>📜 <b>Plagiarism Report:</b> {highlight_boolean(book['Plagiarism Report'])}</p>
                            <p>🔔 <b>Confirmation:</b> {highlight_boolean(book['Confirmation'])}</p>
                            <p>🖨️ <b>Ready to Print:</b> {highlight_boolean(book['Ready to Print'])}</p>
                            <p>📦 <b>Print:</b> {highlight_boolean(book['Print'])}</p>
                            <p>🚚 <b>Deliver:</b> {highlight_boolean(book['Deliver'])}</p>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )





            # Expandable section for author details
            with st.expander("📋 View Author Details"):
                authors = get_book_and_author_details(book)
                for idx, author in enumerate(authors, start=1):
                    st.markdown(f"**Author {idx}:**")
                    st.markdown(f"- **Author ID:** {author['Author ID']}")
                    st.markdown(f"- **Name:** {author['Author Name']}")
                    st.markdown(f"- **Position:** {author['Position']}")
                    st.markdown(f"- **Email:** {author['Email']}")
                    st.markdown(f"- **Contact:** {author['Contact']}")
                    st.markdown(f"- **Welcome Mail:** {author['Welcome Mail']}")
                    st.markdown(f"- **Author Detail:** {author['Author Detail']}")
                    st.markdown(f"- **Photo:** {author['Photo']}")
                    st.markdown(f"- **ID Proof:** {author['ID Proof']}")
                    st.markdown(f"- **Send Cover Page:** {author['Send Cover Page']}")
                    st.markdown(f"- **Agreement Received:** {author['Agreement Received']}")
                    st.markdown(f"- **Digital Profile:** {author['Digital Prof']}")
                    st.markdown(f"- **Plagiarism Report:** {author['Plagiarism Report']}")
                    st.markdown(f"- **Confirmation:** {author['Confirmation']}")
                    st.markdown("---")
else:
    if search_query:
        st.error(f"No results found for '{search_query}' in '{search_column}'")
    else:
        st.info("Enter a search term to begin.")











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
