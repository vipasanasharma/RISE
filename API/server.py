import pandas as pd
from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import pandas as pd
import openai
import faiss
import numpy as np
import gc
from sentence_transformers import SentenceTransformer
import re
from dotenv import load_dotenv
import os

app = Flask(__name__)
# Allow requests from the React app
CORS(app)
load_dotenv()

# Get the OpenAI API key
openai_api_key = os.getenv("OPENAI_API_KEY")


# Load Excel data into separate DataFrames
excel_file = r'input\risefinal.xlsx'
personal_data_df = pd.read_excel(excel_file, sheet_name='Personal Data')
asset_allocation_df = pd.read_excel(excel_file, sheet_name='Asset Allocation')
wow_df = pd.read_excel(excel_file, sheet_name='wow')

# Route to get data based on client ID for the homepage
@app.route('/api/homepage-data', methods=['GET'])
def get_homepage_data():
    client_id = request.args.get('Client ID')

    if not client_id:
        return jsonify({"error": "Client ID is required"}), 400

    try:
        client_id = int(client_id)
    except ValueError:
        return jsonify({"error": "Invalid Client ID format"}), 400

    # Fetch data for the client ID from the Personal Data and Asset Allocation DataFrames
    client_data = personal_data_df[personal_data_df['Client ID'] == client_id]
    asset_data = asset_allocation_df[asset_allocation_df['Client ID'] == client_id]

    if client_data.empty or asset_data.empty:
        return jsonify({"error": "Client ID not found"}), 404

    # Extracting relevant data
    homepage_data = {
        "goals": {
            "retirementCorpus": client_data.get('Retirement Corpus Goal', pd.Series(['Data not available'])).values[0],
            "childEducation": client_data.get('Child Education Corpus Goal', pd.Series(['Data not available'])).values[0],
            "propertyPurchase": client_data.get('Property Purchase Corpus Goal', pd.Series(['Data not available'])).values[0]
        },
        "debt": {
            "totalDebt": client_data.get('Debt (JPY)', pd.Series(['Data not available'])).values[0]
        },
        "assetAllocation": {
            "equity": asset_data.get('Initial Equity Value (JPY)', pd.Series(['Data not available'])).values[0],
            "realEstate": asset_data.get('Initial Real Estate Value (JPY)', pd.Series(['Data not available'])).values[0],
            "corporateBonds": asset_data.get('Initial Corp Bonds Value (JPY)', pd.Series(['Data not available'])).values[0],
            "governmentBonds": asset_data.get('Initial Govt Bonds Value (JPY)', pd.Series(['Data not available'])).values[0]
        }
    }
    return jsonify(homepage_data)

# Route to get profile data based on client ID
@app.route('/api/profile-data', methods=['GET'])
def get_profile_data():
    client_id = request.args.get('Client ID')

    if not client_id:
        return jsonify({"error": "Client ID is required"}), 400

    try:
        client_id = int(client_id)
    except ValueError:
        return jsonify({"error": "Invalid Client ID format"}), 400

    # Fetch data for the client ID from the Personal Data DataFrame
    client_data = personal_data_df[personal_data_df['Client ID'] == client_id]

    if client_data.empty:
        return jsonify({"error": "Client ID not found"}), 404

    # Extracting relevant data
    profile_data = {
        "name": client_data.get('Name', pd.Series(['Data not available'])).values[0],
        "age": client_data.get('Age', pd.Series(['Data not available'])).values[0],
        "clientId": client_data.get('Client ID', pd.Series(['Data not available'])).values[0],
        "riskTolerance": client_data.get('Risk Profile', pd.Series(['Data not available'])).values[0],
        "financialGoals": client_data.get('Future Expected Net Worth (JPY)', pd.Series(['Data not available'])).values[0]
    }
    return jsonify(profile_data)


# Route to get nudge data based on client ID
@app.route('/api/nudge-data', methods=['GET'])
def get_nudge_data():
    file_path=(r"input\risefinal.xlsx")
    client_id = request.args.get('Client ID')
    personal_data, asset_allocation, weekly_data = load_data(file_path)

    user_personal_data, user_asset_allocation, user_weekly_data = get_client_data(personal_data, asset_allocation, weekly_data, client_id)
    if user_personal_data is None:
            return
        
     # Process week by week starting from week 256
    for week in range(259, 261):
        print(f"Processing Week {week}...")
        week_data = user_weekly_data[user_weekly_data['Week'] == week]
        if week_data.empty:
            print(f"No data available for Week {week}.")
            continue

        # Create prompt for the current week
        prompt = prepare_prompt(user_personal_data, user_weekly_data, user_asset_allocation, user_personal_data, week)
        response = generate_nudges_for_chunk(prompt)
        print(f"Week {week} Response:\n{response}")
        projections_after_data = extract_projections_after(response)
        print(projections_after_data)
   
    # return response
    return {
        "llm_response": response,
        "projections_after_data": projections_after_data
    }



# Route to update the Excel file based on user's rebalance decision
@app.route('/api/update-excel', methods=['POST'])
def update_excel():
    data = request.get_json()
    client_id = data.get('clientId')
    updated_projections = data.get('updatedProjections')

    # Simulating the Excel update logic
    if updated_projections:
        # Print the updated projections for debugging
        print(f"Updating Excel for Client ID: {client_id}")
        print(f"New Projections: {updated_projections}")

        # Your logic to update the Excel file would go here
        # (for example, calling a function to update the weekly data)
        rebalance = 'yes'
        week = 1  # Example week, you can dynamically set this
        if rebalance == 'yes':
            # Perform the rebalance operation (updating weekly data)
            print(f"Rebalanced portfolio for Client {client_id} for Week {week}.")
            return jsonify({"message": f"Rebalanced portfolio for Client {client_id} for Week {week}."})
        else:
            print(f"Skipping rebalancing for Client {client_id}.")
            return jsonify({"message": f"Skipping rebalancing for Client {client_id}."})

    return jsonify({"error": "Invalid request"}), 400

# Route to get weekly performance data based on client ID


# Route to get weekly performance data based on client ID
@app.route('/api/wow-data', methods=['GET'])
def get_wow_data():
    client_id = request.args.get('Client ID')

    if not client_id:
        return jsonify({"error": "Client ID is required"}), 400

    try:
        client_id = int(client_id)
    except ValueError:
        return jsonify({"error": "Invalid Client ID format"}), 400

    # Fetch data for the client ID from the wow DataFrame
    client_wow_data = wow_df[wow_df['Client ID'] == client_id]  # Make sure Client ID is included in the wow sheet

    if client_wow_data.empty:
        return jsonify({"error": "Client ID not found in wow data"}), 404

    # Process and return relevant data from the wow DataFrame
    # Example: Get last week's performance
    last_week_data = client_wow_data.iloc[-1]  # Get last row as an example
    return jsonify(last_week_data.to_dict())


# Load Excel sheets
def load_data(file_path):
    personal_data = pd.read_excel(file_path, sheet_name='Personal Data')
    asset_allocation = pd.read_excel(file_path, sheet_name='Asset Allocation')
    weekly_data = pd.read_excel(file_path, sheet_name='wow')  # Load the 'wow' sheet
    return personal_data, asset_allocation, weekly_data

# Step 6: Generate output using OpenAI's model
def generate_nudges_for_chunk(prompt):
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a financial expert generating hyper-personalized investment nudges."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=10000,
        temperature=0.7
    )
    return response.choices[0].message['content'].strip()


# Step 1: Get client-specific data from the Excel file
def get_client_data(personal_data, asset_allocation, weekly_data, client_id):
    client_data = personal_data[personal_data['Client ID'] == int(client_id)]
    if client_data.empty:
        print("Invalid Client ID. Please make sure the ID exists in the dataset.")
        return None, None, None

    user_personal_data = personal_data[personal_data['Client ID'] == int(client_id)]
    user_asset_allocation = asset_allocation[asset_allocation['Client ID'] == int(client_id)]
    user_weekly_data = weekly_data[weekly_data['Client ID'] == int(client_id)]
    return user_personal_data, user_asset_allocation, user_weekly_data


# Step 5: Prepare the prompt for RAG pipeline
def prepare_prompt(user_profile, user_weekly_data, user_asset_allocation, user_personal_data, week):
    # Get the data only for the current week
    current_week_data = user_weekly_data[user_weekly_data['Week'] == week].to_string(index=False)
    personal_data_snippet = user_personal_data.to_string(index=False)
    asset_allocation_data_snippet = user_asset_allocation.to_string(index=False)

    prompt = f"""
    You are an AI financial advisor for Japanese HNIs. Given the user's financial profile and weekly market data, perform the following tasks:
    1. Extract Weekly Data:

    Using the following data for Week {week}, extract the exact values for Equity, Real Estate, Corporate Bonds, and Government Bonds for the week:

    Output Format for Weekly Data below -
    Current Week: {current_week_data}

    Additionally, extract the week-over-week percentage changes for these assets over the specified week.

    2. Generate Hyper-Personalized Nudges for Rebalancing:
    For the week, provide hyper-personalized investment actions to rebalance the portfolio based on:
    - The values of assets before rebalancing (as seen in the data for Week {week})
    - The values of assets after suggested rebalancing
    - The user's financial goals (retirement corpus, child education, property purchase){personal_data_snippet}
    - The user's risk tolerance and desired portfolio return{personal_data_snippet}
    - Market conditions during the week and changes in asset values
    - Explain why specific asset allocations should be adjusted, using these principles:
        - Should the user increase or decrease exposure to Equity, Real Estate, Corporate Bonds, or Government Bonds? Why?
        - If recommending changes, how much (%) of the portfolio should be adjusted, and what future returns or benefits are expected from this rebalance?
        - Highlight how these actions contribute to:
            - Achieving future financial goals, such as reaching the retirement corpus earlier or securing child education funds.{personal_data_snippet}
            - Progress toward debt repayment, explaining how rebalancing can free up funds to pay off debt sooner.{personal_data_snippet}
            - Securing the user’s financial position for their dependents by ensuring stable returns and risk management, safeguarding future income and wealth growth.

    3. Recommend specific assets or sectors to invest in based on the user's financial goals and preferences.
    Provide a brief analysis of why these assets are ideal during the given week, factoring in Japanese market trends and future expectations.
    Include the names of the recommended assets and state why they align with the user’s risk profile and goals, such as expected future growth, risk level, and alignment with their retirement corpus or debt repayment strategy.

    Conclude with a concise summary of the rebalancing actions with exact data points and projections before and after rebalancing.
    Include estimated improvements in portfolio performance and future returns.
    Ensure the output format of "Projections Before" & "Projections After" remains consistent and is in JSON format.  the jsons contain only the before after values of "Equity", "Real Estate","Corporate Bonds",  "Government Bonds". For example:

    "Projections Before" {{json_value_1}},
    "Projections After" {{json_value_2}}
    """
    return prompt


# Function to process String and extract JSON Object.
def extract_projections_after(response: str) -> dict:
    # Use regex to find all JSON-like objects in the string
    json_matches = re.findall(r'\{.*?\}', response, re.DOTALL)

    # Check if there are at least two JSON objects in the response
    if len(json_matches) >= 2:
        # Extract the second JSON object (Projections After)
        json_string = json_matches[1]

        # Parse the JSON string into a Python dictionary
        try:
            projections_after = json.loads(json_string)
            return projections_after
        except json.JSONDecodeError:
            print("Error: Failed to decode the JSON string.")
            return None
    else:
        print("Error: Less than two JSON objects found in the response.")
        return None
# Memory management function to clear variables
def clear_memory(*vars):
    for var in vars:
        del var
    gc.collect()



# Now we update subsequent weeks based on new rebalanced values for the current week
def update_weekly_data(user_weekly_data, week, new_values):
    # Update the weekly data for the current week (week n) with the new rebalanced values
    user_weekly_data.loc[user_weekly_data['Week'] == week, ['Equity Value', 'Real Estate Value',
                                                            'Govt Bonds Value', 'Corp Bonds Value']] = new_values

    # Now, we update subsequent weeks based on the new rebalanced values for week n
    for future_week in range(week + 1, 261):
        print(f"Processing future week: {future_week}")

        # Get the week-over-week percentage changes for each asset
        wow_equity_change = user_weekly_data.loc[user_weekly_data['Week'] == future_week, 'wow equity change'].values[0] / 100
        wow_real_estate_change = user_weekly_data.loc[user_weekly_data['Week'] == future_week, 'wow real estate change'].values[0] / 100
        wow_govt_bonds_change = user_weekly_data.loc[user_weekly_data['Week'] == future_week, 'wow govt bonds change'].values[0] / 100
        wow_corp_bonds_change = user_weekly_data.loc[user_weekly_data['Week'] == future_week, 'wow corp bonds change'].values[0] / 100

        print(f"WoW changes for Week {future_week} - Equity: {wow_equity_change}, Real Estate: {wow_real_estate_change}, "
              f"Govt Bonds: {wow_govt_bonds_change}, Corp Bonds: {wow_corp_bonds_change}")

        # Calculate the new values for the future week using the rebalanced values from the previous week (week n or n+1, ...)
        user_weekly_data.loc[user_weekly_data['Week'] == future_week, 'Equity Value'] = \
            user_weekly_data.loc[user_weekly_data['Week'] == future_week - 1, 'Equity Value'].values[0] * (1 + wow_equity_change)

        user_weekly_data.loc[user_weekly_data['Week'] == future_week, 'Real Estate Value'] = \
            user_weekly_data.loc[user_weekly_data['Week'] == future_week - 1, 'Real Estate Value'].values[0] * (1 + wow_real_estate_change)

        user_weekly_data.loc[user_weekly_data['Week'] == future_week, 'Govt Bonds Value'] = \
            user_weekly_data.loc[user_weekly_data['Week'] == future_week - 1, 'Govt Bonds Value'].values[0] * (1 + wow_govt_bonds_change)

        user_weekly_data.loc[user_weekly_data['Week'] == future_week, 'Corp Bonds Value'] = \
            user_weekly_data.loc[user_weekly_data['Week'] == future_week - 1, 'Corp Bonds Value'].values[0] * (1 + wow_corp_bonds_change)

        # Print the updated values for debugging purposes
        print(f"Updated values for Week {future_week}:")
        print(user_weekly_data.loc[user_weekly_data['Week'] == future_week])

    return user_weekly_data

# Function to save updated data back to Excel
def save_data(file_path, user_weekly_data):
    # Load the existing Excel file
    with pd.ExcelWriter(file_path, mode='a', engine='openpyxl', if_sheet_exists='replace') as writer:
        user_weekly_data.to_excel(writer, sheet_name='wow', index=False)


   
# Run the Flask server
if __name__ == '__main__':
    app.run(debug=True)
