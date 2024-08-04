import streamlit as st
import pandas as pd
import numpy as np
from streamlit_lottie import st_lottie
import requests

# Load data for flipakrt
df_comm_flipkart = pd.read_excel(r"Rate card.xlsx", sheet_name="All Commission")
df_shipping_flipkart = pd.read_excel(r"Rate card.xlsx", sheet_name="All Shipping fee")
df_reverse_flipkart = pd.read_excel(r"Rate card.xlsx", sheet_name="Reverse shipping fee")
df_pick_pack_flipkart = pd.read_excel(r"Rate card.xlsx", sheet_name="Pick and Pack fee")
df_fixed_flipkart = pd.read_excel(r"Rate card.xlsx", sheet_name="Fixed fee")

# Load data for Amazon
df_pick_pack_amazon = pd.read_excel(r"Rate card.xlsx", sheet_name="Pick and Pack Amazon")
df_shipping_amazon = pd.read_excel(r"Rate card.xlsx", sheet_name="Shipping Amazon")
df_referral_amazon = pd.read_excel(r"Rate card.xlsx", sheet_name="Referral fee Amazon")
df_closing_amazon = pd.read_excel(r"Rate card.xlsx", sheet_name="Closing fee Amazon")

# Define functions for Flipkart

# Make sure to return 1 in case of not found for those functions which are being multiplied and 0 for those functions which are added
# Fixed fee depends upon the Seller account the product or Category (So I need the details of all sellers)
def fixed_fee_flipkart(fullfillment_type, seller_tier):
    row = df_fixed_flipkart[(df_fixed_flipkart['Fullfillment Type'] == fullfillment_type) & (df_fixed_flipkart['Seller Tier'] == seller_tier)]
    if not row.empty:
        return row['Price'].iloc[0]
    else:
        return 0
    
# Check whether the file contains an updated list of all the vertical and price buckets
def commission_fee_flipkart(platform, vertical, fullfillment, price):
    row = df_comm_flipkart[(df_comm_flipkart['Platform'] == platform) & (df_comm_flipkart['Vertical'] == vertical) & (df_comm_flipkart['Fullfillment Type'] == fullfillment) & (df_comm_flipkart['Lower ASP'] <= price) & ((df_comm_flipkart['Upper ASP'] >= price) | (df_comm_flipkart['Upper ASP'] == 0))]
    if not row.empty:
        return row['Commission'].iloc[0] * price
    else:
        return 0

# Does Shipping fee depends upon the Seller Tier as well as the weight of the product, or its just the weight ?
def shipping_fee_flipkart(local, zonal, national, weight, platform, seller_tier, fullfillment_type):
    row = df_shipping_flipkart[(df_shipping_flipkart['Platform'] == platform) & (df_shipping_flipkart['Seller Tier'] == seller_tier) & (df_shipping_flipkart['Fullfillment Type'] == fullfillment_type) & (df_shipping_flipkart['Lower weight'] <= weight) & (df_shipping_flipkart['Upper weight'] >= weight)]
    if not row.empty:
        return row['Local'].iloc[0] * local + row['Zonal'].iloc[0] * zonal + row['National'].iloc[0] * national
    else:
        return 0
    
# Is this applicable for Non-FBF or FBF ? Ans: It is applicable to FBF only
def pick_pack_fee_flipkart(fullfillment_type, local, zonal, national, weight):
    row = df_pick_pack_flipkart[(df_pick_pack_flipkart['Fullfillment Type'] == fullfillment_type) & (df_pick_pack_flipkart['Lower weight'] <= weight) & (df_pick_pack_flipkart['Upper weight'] >= weight)]
    if not row.empty:
        return row['Local'].iloc[0] * local + row['Zonal'].iloc[0] * zonal + row['National'].iloc[0] * national
    else:
        return 0
    
# Is this only dependent on weight of the product or it also depends upon the Seller Tier ?
def reverse_ship_fee_flipkart(local, zonal, national, weight):
    row = df_reverse_flipkart[(df_reverse_flipkart['Lower weight'] <= weight) & (df_reverse_flipkart['Upper weight'] >= weight)]
    if not row.empty:
        return row['Local'].iloc[0] * local + row['Zonal'].iloc[0] * zonal + row['National'].iloc[0] * national
    else:
        return 0

# Define functions for Amazon

def pick_pack_fee_amazon(fullfillment_type, size_brand):
    if (fullfillment_type == "FBA"):
        if (size_brand == "Standard"):
            return 14
        else:
            return 26
    else:
        return 0

def referal_fee_amazon(vertical, price):
    row = df_referral_amazon[
        df_referral_amazon['Vertical'].apply(lambda x: vertical in map(str.strip, x.split(','))) &
        (df_referral_amazon['Lower price'] <= price) &
        (df_referral_amazon['Upper price'] >= price)]
    
    if not row.empty:
        return row['Commission'].iloc[0] * price
    else:
        return 0


def closing_fee_amazon(fullfillment_type, price, vertical):
    if ((fullfillment_type == "Easy Ship" or fullfillment_type == "Easy Ship Prime") and (price <= 250)):
        return 4
    elif ((fullfillment_type == "Easy Ship" or fullfillment_type == "Easy Ship Prime") and (price >= 251 and price <=500)):
        return 9
    elif ((fullfillment_type == "Easy Ship" or fullfillment_type == "Easy Ship Prime") and (price >= 501 and price <=1000)):
        return 30
    elif ((fullfillment_type == "Easy Ship" or fullfillment_type == "Easy Ship Prime") and (price >= 1001)):
        return 61
    elif ((fullfillment_type == "FBA") and (price <=250)):
        row = df_closing_amazon[
        df_closing_amazon['Single_star_product'].apply(lambda x: vertical in map(str.strip, x.split(',')))]
        if not row.empty:
            return 12
        else:
            return 25
        
    elif ((fullfillment_type == "FBA") and (price >= 251 and price <=500)):
        row = df_closing_amazon[
        df_closing_amazon['Two_star_product'].apply(lambda x: vertical in map(str.strip, x.split(',')))]
        if not row.empty:
            return 12
        else:
            return 20

    elif ((fullfillment_type == "FBA") and (price >= 501 and price <= 1000)):
        return 25
    elif ((fullfillment_type == "FBA") and (price > 1000)):
        row = df_closing_amazon[
        df_closing_amazon['Three_star_product'].apply(lambda x: vertical in map(str.strip, x.split(',')))]
        if not row.empty:
            return 70
        else:
            return 50
    

def shipping_fee_amazon(platform, size_brand, seller_tier, fullfillment_type, local, zonal, national, weight):
    row = df_shipping_amazon[(df_shipping_amazon['Platform'] == platform) & (df_shipping_amazon['Size brand'] == size_brand) & (df_shipping_amazon['Seller Tier'] == seller_tier) & (df_shipping_amazon['Fullfillment Type'] == fullfillment_type) & (df_shipping_amazon['Lower weight'] <= weight) & (df_shipping_amazon['Upper weight'] >= weight)]
    if not row.empty:
        return row['Local'].iloc[0] * local + row['Zonal'].iloc[0] * zonal + row['National'].iloc[0] * national
    else:
        return 0
    


# Define functions for Jiomart
def fixed_fee_jiomart(category):
    return fixed_fee_flipkart(category)

def commission_fee_jiomart(price):
    return commission_fee_flipkart(price)

def shipping_fee_jiomart(local, zonal, national, weight):
    return shipping_fee_flipkart(local, zonal, national, weight)

def reverse_ship_fee_jiomart(local, zonal, national, weight):
    return reverse_ship_fee_flipkart(local, zonal, national, weight)

# Calculate SP function
def calculate_sp(row, platform):
    if platform == 'Flipkart':
        current_sp = row['MRP']
        net_sp = current_sp * (1 - row['RTO'] - row['RVP']) / (1 + row['GST'])
        abs_ads = current_sp * row['Ads']
        pre_set = 1e9

        while pre_set > row['Expected Settlement'] and pre_set - row['Expected Settlement'] > 0.5:
            pre_set = (net_sp - (1 - row['RTO'] - row['RVP']) * commission_fee_flipkart(row['Platform'], row['Vertical'], row['Fullfillment Type'], current_sp) - 
                       (1 - row['RTO']) * (fixed_fee_flipkart(row['Fullfillment Type'], row['Seller Tier']) + shipping_fee_flipkart(row['Local'], row['Zonal'], row['National'], row['Weight'], row['Platform'], row['Seller Tier'], row['Fullfillment Type'])) - 
                       reverse_ship_fee_flipkart(row['Local'], row['Zonal'], row['National'], row['Weight']) * row['RVP'] - 
                       abs_ads * (1 - row['RTO'] - row['RVP']) - pick_pack_fee_flipkart(row['Fullfillment Type'], row['Local'], row['Zonal'], row['National'], row['Weight'])) / (1 - row['RTO'] - row['RVP'])
    
            current_sp = current_sp - (pre_set - row['Expected Settlement']) / 2
            abs_ads = current_sp * row['Ads']
            net_sp = current_sp * (1 - row['RTO'] - row['RVP']) / (1 + row['GST'])

        return current_sp
    
    elif platform == 'Amazon':
        current_sp = row['MRP']
        net_sp = current_sp * (1 - row['RTO'] - row['RVP']) / (1 + row['GST'])
        abs_ads = current_sp * row['Ads']
        pre_set = 1e9


        while (pre_set > row['Expected Settlement'] and pre_set - row['Expected Settlement'] > 0.5):
            pre_set = (net_sp - (1 - row['RTO'] - row['RVP'])*referal_fee_amazon(row['Vertical'], current_sp) - 
                       (1 - row['RTO'])*(closing_fee_amazon(row['Fullfillment Type'], current_sp, row['Vertical']) + shipping_fee_amazon(row['Platform'], row['Size brand'], row['Seller Tier'], row['Fullfillment Type'], row['Local'], row['Zonal'], row['National'], row['Weight'])) - 
                       abs_ads*(1 - row['RTO'] - row['RVP']) - pick_pack_fee_amazon(row['Fullfillment Type'], row['Size brand'])) / (1 - row['RTO'] - row['RVP'])
            
            current_sp = current_sp - (pre_set - row['Expected Settlement']) / 2
            abs_ads = current_sp * row['Ads']
            net_sp = current_sp * (1 - row['RTO'] - row['RVP']) / (1 + row['GST'])
        
        return current_sp

    elif platform == 'Jiomart':
        pass

    elif platform == 'Meesho':
        pass

# Streamlit UI
st.set_page_config(page_title="Nexten Pricing Calculator", page_icon=":moneybag:", layout="wide")

def load_lottie_url(url):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

lottie_icon = load_lottie_url("https://lottie.host/94b04dc4-9475-4a8d-9c94-9ce757defaf4/6yOlZmefOI.json")

with st.container():
    st.image("nexten.png", width=100)  # Nexten Logo

    st.title("Nexten Pricing Calculator")

with st.container():
    left_column, right_column = st.columns((2, 1))

    with left_column:
        platform = st.selectbox("Select Platform", ["Flipkart", "Amazon", "Jiomart", "Meesho"])

        uploaded_file = st.file_uploader("Upload your Excel file", type=["xlsx"])

        if uploaded_file:
            df_input = pd.read_excel(uploaded_file)
            st.write("Input Data", df_input)
            
            # The file must have 'Category', 'Local', 'Zonal', 'National', 'Weight', 'Ads', 'MRP', 'RVP', 'RTO', 'GST', 'Expected Settlement'
            df_input['SP'] = df_input.apply(lambda row: calculate_sp(row, platform), axis=1)
            
            st.write("Output Data with SP", df_input)
            

            output = df_input.to_excel("output_with_sp.xlsx", index=False)

            # Download link for the Excel file
            with open("output_with_sp.xlsx", "rb") as file:
                btn = st.download_button(
                    label="Download Output Excel",
                    data=file,
                    file_name="output_with_sp.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

    with right_column:
        st_lottie(lottie_icon, height=300, key="e_commerce")