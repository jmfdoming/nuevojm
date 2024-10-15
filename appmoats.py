from pandas import read_excel, notna
from streamlit import text_input, write, error, subheader, markdown, columns, info

def load_data():
    try:
        return read_excel("moats.xlsx")
    except FileNotFoundError:
        error("The file 'moats.xlsx' was not found. Please check the file location.")
        return None
    except Exception as e:
        error(f"An error occurred while loading the file: {e}")
        return None

def get_company_data(df, ticker):
    result = df[df['Simbol'].str.upper() == ticker.upper()]
    return result

def main():
    markdown("<h3 style='text-align: center; color: #1E90FF; margin-top: 0; margin-bottom: 5px;'>Analysis of Competitive Advantages of Companies</h3>", unsafe_allow_html=True)
    
        
    data = load_data()
    if data is None:
        return
    
    ticker = text_input("Enter the ticker of the company:", key="ticker_input", max_chars=10, help="Enter up to 10 characters", label_visibility="collapsed")
    
    if ticker:
        company_data = get_company_data(data, ticker)
        
        if not company_data.empty:
            company_data[['Cost Advantage', 'Efficient Scale', 'Intangible Assets', 'Network Effect', 'Switch Cost']] = company_data[['Cost Advantage', 'Efficient Scale', 'Intangible Assets', 'Network Effect', 'Switch Cost']].replace({1: 'yes', 0: ''})
            
            # Display the main company information
            col1, col2 = columns(2, gap="small")
            with col1:
                name = company_data['Name'].iloc[0]
                markdown(f"<h4>{name}</h4>", unsafe_allow_html=True)
            
            with col2:
                moat = company_data['Economic Moat'].iloc[0]
                markdown(f"<h4>Economic Moat: {moat}</h4>", unsafe_allow_html=True)
                # Display only the competitive advantage fields with 'yes'
                for column in ['Cost Advantage', 'Efficient Scale', 'Intangible Assets', 'Network Effect', 'Switch Cost']:
                    if company_data[column].iloc[0] == 'yes':
                        markdown(f"<h4>{column}</h4>", unsafe_allow_html=True)
            
            # Display rationale of the moat
            markdown("<hr style='margin-top: 20px; margin-bottom: 20px;'>", unsafe_allow_html=True)
            subheader(f"Rationale of the Moat - {company_data['Name'].iloc[0]}", anchor=False)
            markdown(f"<div style='background-color:#F0F8FF; padding: 3px; margin-top: 0; margin-bottom: 5px; border-radius: 3px;'>{company_data['Rational'].iloc[0]}</div>", unsafe_allow_html=True)
        else:
            error("No data found for the entered ticker.")

if __name__ == "__main__":
    main()
