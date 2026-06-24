"""
stock_universe.py — the maintained list of stocks VinStock screens against.

This is data, not logic. To expand coverage (toward 500+, 1000+, eventually
the full NSE list), edit/extend UNIVERSE below or replace seed_universe()
with a call to a real NSE/BSE constituents API — nothing in the screening
engine needs to change.

IMPORTANT — accuracy note: index membership (Nifty 50 / Next 50 / Midcap
100) changes over time via NSE's periodic reviews, and we could not
verify an exact, current, complete official list at build time. The
`index_membership` tag below is a best-effort label for organizing the
UI (grouping/filtering), not a guarantee of current official index
status. Treat it as approximate and correct it from nseindia.com's
official index files when accuracy here matters.

Each entry: (symbol, name, index_membership, sector)
"""

UNIVERSE = [
    # ---- Banking & Financial Services ----
    ("HDFCBANK.NS", "HDFC Bank", "Nifty 50", "Financial Services"),
    ("ICICIBANK.NS", "ICICI Bank", "Nifty 50", "Financial Services"),
    ("SBIN.NS", "State Bank of India", "Nifty 50", "Financial Services"),
    ("KOTAKBANK.NS", "Kotak Mahindra Bank", "Nifty 50", "Financial Services"),
    ("AXISBANK.NS", "Axis Bank", "Nifty 50", "Financial Services"),
    ("BAJFINANCE.NS", "Bajaj Finance", "Nifty 50", "Financial Services"),
    ("BAJAJFINSV.NS", "Bajaj Finserv", "Nifty 50", "Financial Services"),
    ("HDFCLIFE.NS", "HDFC Life Insurance", "Nifty 50", "Financial Services"),
    ("SBILIFE.NS", "SBI Life Insurance", "Nifty 50", "Financial Services"),
    ("ICICIPRULI.NS", "ICICI Prudential Life", "Nifty Next 50", "Financial Services"),
    ("ICICIGI.NS", "ICICI Lombard General Insurance", "Nifty Next 50", "Financial Services"),
    ("PNB.NS", "Punjab National Bank", "Nifty Midcap 100", "Financial Services"),
    ("BANKBARODA.NS", "Bank of Baroda", "Nifty Midcap 100", "Financial Services"),
    ("CANBK.NS", "Canara Bank", "Nifty Midcap 100", "Financial Services"),
    ("IDFCFIRSTB.NS", "IDFC First Bank", "Nifty Midcap 100", "Financial Services"),
    ("FEDERALBNK.NS", "Federal Bank", "Nifty Midcap 100", "Financial Services"),
    ("AUBANK.NS", "AU Small Finance Bank", "Nifty Midcap 100", "Financial Services"),
    ("CHOLAFIN.NS", "Cholamandalam Investment", "Nifty Midcap 100", "Financial Services"),
    ("MUTHOOTFIN.NS", "Muthoot Finance", "Nifty Midcap 100", "Financial Services"),
    ("LICHSGFIN.NS", "LIC Housing Finance", "Nifty Midcap 100", "Financial Services"),
    ("SHRIRAMFIN.NS", "Shriram Finance", "Nifty Next 50", "Financial Services"),
    ("PFC.NS", "Power Finance Corporation", "Nifty Next 50", "Financial Services"),
    ("RECLTD.NS", "REC Limited", "Nifty Next 50", "Financial Services"),
    ("LICI.NS", "Life Insurance Corporation", "Nifty Next 50", "Financial Services"),

    # ---- IT ----
    ("TCS.NS", "Tata Consultancy Services", "Nifty 50", "Information Technology"),
    ("INFY.NS", "Infosys", "Nifty 50", "Information Technology"),
    ("HCLTECH.NS", "HCL Technologies", "Nifty 50", "Information Technology"),
    ("WIPRO.NS", "Wipro", "Nifty 50", "Information Technology"),
    ("TECHM.NS", "Tech Mahindra", "Nifty 50", "Information Technology"),
    ("LTIM.NS", "LTIMindtree", "Nifty Next 50", "Information Technology"),
    ("PERSISTENT.NS", "Persistent Systems", "Nifty Midcap 100", "Information Technology"),
    ("COFORGE.NS", "Coforge", "Nifty Midcap 100", "Information Technology"),
    ("MPHASIS.NS", "Mphasis", "Nifty Midcap 100", "Information Technology"),
    ("LTTS.NS", "L&T Technology Services", "Nifty Midcap 100", "Information Technology"),

    # ---- Energy / Oil & Gas ----
    ("RELIANCE.NS", "Reliance Industries", "Nifty 50", "Energy"),
    ("ONGC.NS", "Oil & Natural Gas Corp", "Nifty 50", "Energy"),
    ("BPCL.NS", "Bharat Petroleum", "Nifty Next 50", "Energy"),
    ("IOC.NS", "Indian Oil Corporation", "Nifty Next 50", "Energy"),
    ("GAIL.NS", "GAIL India", "Nifty Midcap 100", "Energy"),
    ("HINDPETRO.NS", "Hindustan Petroleum", "Nifty Midcap 100", "Energy"),
    ("PETRONET.NS", "Petronet LNG", "Nifty Midcap 100", "Energy"),
    ("OIL.NS", "Oil India", "Nifty Midcap 100", "Energy"),

    # ---- Power & Infra ----
    ("NTPC.NS", "NTPC", "Nifty 50", "Power"),
    ("POWERGRID.NS", "Power Grid Corporation", "Nifty 50", "Power"),
    ("ADANIPOWER.NS", "Adani Power", "Nifty Next 50", "Power"),
    ("TATAPOWER.NS", "Tata Power", "Nifty Midcap 100", "Power"),
    ("ADANIENT.NS", "Adani Enterprises", "Nifty 50", "Diversified"),
    ("ADANIPORTS.NS", "Adani Ports & SEZ", "Nifty 50", "Infrastructure"),
    ("LT.NS", "Larsen & Toubro", "Nifty 50", "Infrastructure"),
    ("SIEMENS.NS", "Siemens", "Nifty Next 50", "Capital Goods"),
    ("ABB.NS", "ABB India", "Nifty Midcap 100", "Capital Goods"),
    ("CUMMINSIND.NS", "Cummins India", "Nifty Midcap 100", "Capital Goods"),
    ("BEL.NS", "Bharat Electronics", "Nifty Next 50", "Defence"),
    ("HAL.NS", "Hindustan Aeronautics", "Nifty Next 50", "Defence"),
    ("BHEL.NS", "Bharat Heavy Electricals", "Nifty Midcap 100", "Capital Goods"),

    # ---- FMCG ----
    ("HINDUNILVR.NS", "Hindustan Unilever", "Nifty 50", "FMCG"),
    ("ITC.NS", "ITC", "Nifty 50", "FMCG"),
    ("NESTLEIND.NS", "Nestle India", "Nifty 50", "FMCG"),
    ("BRITANNIA.NS", "Britannia Industries", "Nifty 50", "FMCG"),
    ("TATACONSUM.NS", "Tata Consumer Products", "Nifty 50", "FMCG"),
    ("DABUR.NS", "Dabur India", "Nifty Next 50", "FMCG"),
    ("GODREJCP.NS", "Godrej Consumer Products", "Nifty Next 50", "FMCG"),
    ("MARICO.NS", "Marico", "Nifty Midcap 100", "FMCG"),
    ("COLPAL.NS", "Colgate-Palmolive India", "Nifty Midcap 100", "FMCG"),
    ("VBL.NS", "Varun Beverages", "Nifty Next 50", "FMCG"),
    ("UBL.NS", "United Breweries", "Nifty Midcap 100", "FMCG"),

    # ---- Auto ----
    ("MARUTI.NS", "Maruti Suzuki", "Nifty 50", "Automobile"),
    ("TATAMOTORS.NS", "Tata Motors", "Nifty 50", "Automobile"),
    ("M&M.NS", "Mahindra & Mahindra", "Nifty 50", "Automobile"),
    ("BAJAJ-AUTO.NS", "Bajaj Auto", "Nifty 50", "Automobile"),
    ("EICHERMOT.NS", "Eicher Motors", "Nifty 50", "Automobile"),
    ("TVSMOTOR.NS", "TVS Motor Company", "Nifty Next 50", "Automobile"),
    ("ASHOKLEY.NS", "Ashok Leyland", "Nifty Midcap 100", "Automobile"),
    ("BOSCHLTD.NS", "Bosch Limited", "Nifty Midcap 100", "Auto Components"),
    ("MOTHERSON.NS", "Samvardhana Motherson", "Nifty Next 50", "Auto Components"),
    ("BALKRISIND.NS", "Balkrishna Industries", "Nifty Midcap 100", "Auto Components"),
    ("MRF.NS", "MRF Limited", "Nifty Midcap 100", "Auto Components"),
    ("EXIDEIND.NS", "Exide Industries", "Nifty Midcap 100", "Auto Components"),

    # ---- Pharma & Healthcare ----
    ("SUNPHARMA.NS", "Sun Pharmaceutical", "Nifty 50", "Pharma"),
    ("DRREDDY.NS", "Dr Reddy's Laboratories", "Nifty 50", "Pharma"),
    ("CIPLA.NS", "Cipla", "Nifty 50", "Pharma"),
    ("DIVISLAB.NS", "Divi's Laboratories", "Nifty 50", "Pharma"),
    ("APOLLOHOSP.NS", "Apollo Hospitals", "Nifty 50", "Healthcare"),
    ("MAXHEALTH.NS", "Max Healthcare Institute", "Nifty 50", "Healthcare"),
    ("LUPIN.NS", "Lupin", "Nifty Next 50", "Pharma"),
    ("AUROPHARMA.NS", "Aurobindo Pharma", "Nifty Midcap 100", "Pharma"),
    ("TORNTPHARM.NS", "Torrent Pharmaceuticals", "Nifty Midcap 100", "Pharma"),
    ("ALKEM.NS", "Alkem Laboratories", "Nifty Midcap 100", "Pharma"),
    ("BIOCON.NS", "Biocon", "Nifty Midcap 100", "Pharma"),
    ("ZYDUSLIFE.NS", "Zydus Lifesciences", "Nifty Midcap 100", "Pharma"),
    ("MANKIND.NS", "Mankind Pharma", "Nifty Midcap 100", "Pharma"),
    ("FORTIS.NS", "Fortis Healthcare", "Nifty Midcap 100", "Healthcare"),

    # ---- Metals & Mining ----
    ("TATASTEEL.NS", "Tata Steel", "Nifty 50", "Metals"),
    ("JSWSTEEL.NS", "JSW Steel", "Nifty 50", "Metals"),
    ("HINDALCO.NS", "Hindalco Industries", "Nifty 50", "Metals"),
    ("COALINDIA.NS", "Coal India", "Nifty 50", "Mining"),
    ("VEDL.NS", "Vedanta", "Nifty Next 50", "Metals"),
    ("JINDALSTEL.NS", "Jindal Steel & Power", "Nifty Midcap 100", "Metals"),
    ("SAIL.NS", "Steel Authority of India", "Nifty Midcap 100", "Metals"),
    ("NMDC.NS", "NMDC Limited", "Nifty Midcap 100", "Mining"),
    ("HINDZINC.NS", "Hindustan Zinc", "Nifty Midcap 100", "Metals"),
    ("NATIONALUM.NS", "National Aluminium", "Nifty Midcap 100", "Metals"),

    # ---- Telecom ----
    ("BHARTIARTL.NS", "Bharti Airtel", "Nifty 50", "Telecommunication"),
    ("INDUSTOWER.NS", "Indus Towers", "Nifty Next 50", "Telecommunication"),
    ("IDEA.NS", "Vodafone Idea", "Nifty Midcap 100", "Telecommunication"),

    # ---- Cement & Construction Materials ----
    ("ULTRACEMCO.NS", "UltraTech Cement", "Nifty 50", "Cement"),
    ("GRASIM.NS", "Grasim Industries", "Nifty 50", "Diversified"),
    ("SHREECEM.NS", "Shree Cement", "Nifty Next 50", "Cement"),
    ("AMBUJACEM.NS", "Ambuja Cements", "Nifty Midcap 100", "Cement"),
    ("ACC.NS", "ACC Limited", "Nifty Midcap 100", "Cement"),
    ("DALBHARAT.NS", "Dalmia Bharat", "Nifty Midcap 100", "Cement"),

    # ---- Consumer Durables / Retail ----
    ("TITAN.NS", "Titan Company", "Nifty 50", "Consumer Durables"),
    ("ASIANPAINT.NS", "Asian Paints", "Nifty 50", "Consumer Durables"),
    ("BERGEPAINT.NS", "Berger Paints", "Nifty Midcap 100", "Consumer Durables"),
    ("HAVELLS.NS", "Havells India", "Nifty Next 50", "Consumer Durables"),
    ("VOLTAS.NS", "Voltas", "Nifty Midcap 100", "Consumer Durables"),
    ("DIXON.NS", "Dixon Technologies", "Nifty Midcap 100", "Consumer Durables"),
    ("TRENT.NS", "Trent Limited", "Nifty 50", "Retail"),
    ("DMART.NS", "Avenue Supermarts (DMart)", "Nifty Next 50", "Retail"),
    ("KALYANKJIL.NS", "Kalyan Jewellers", "Nifty Midcap 100", "Retail"),

    # ---- New-age / Internet ----
    ("ETERNAL.NS", "Eternal (Zomato)", "Nifty 50", "Internet/E-commerce"),
    ("NYKAA.NS", "FSN E-Commerce (Nykaa)", "Nifty Midcap 100", "Internet/E-commerce"),
    ("PAYTM.NS", "One97 Communications (Paytm)", "Nifty Midcap 100", "Internet/Fintech"),
    ("POLICYBZR.NS", "PB Fintech (Policybazaar)", "Nifty Midcap 100", "Internet/Fintech"),
    ("IRCTC.NS", "Indian Railway Catering & Tourism", "Nifty Midcap 100", "Internet/Services"),

    # ---- Aviation / Transport ----
    ("INDIGO.NS", "InterGlobe Aviation (IndiGo)", "Nifty 50", "Aviation"),

    # ---- Real Estate ----
    ("DLF.NS", "DLF Limited", "Nifty Next 50", "Real Estate"),
    ("GODREJPROP.NS", "Godrej Properties", "Nifty Midcap 100", "Real Estate"),
    ("OBEROIRLTY.NS", "Oberoi Realty", "Nifty Midcap 100", "Real Estate"),
    ("LODHA.NS", "Macrotech Developers (Lodha)", "Nifty Midcap 100", "Real Estate"),
    ("PHOENIXLTD.NS", "Phoenix Mills", "Nifty Midcap 100", "Real Estate"),

    # ---- Chemicals ----
    ("PIDILITIND.NS", "Pidilite Industries", "Nifty Next 50", "Chemicals"),
    ("SRF.NS", "SRF Limited", "Nifty Midcap 100", "Chemicals"),
    ("UPL.NS", "UPL Limited", "Nifty Next 50", "Chemicals"),
    ("DEEPAKNTR.NS", "Deepak Nitrite", "Nifty Midcap 100", "Chemicals"),
    ("AARTIIND.NS", "Aarti Industries", "Nifty Midcap 100", "Chemicals"),
    ("PIIND.NS", "PI Industries", "Nifty Midcap 100", "Chemicals"),
    ("LINDEINDIA.NS", "Linde India", "Nifty Midcap 100", "Chemicals"),

    # ---- Diversified / Conglomerate ----
    ("TATACHEM.NS", "Tata Chemicals", "Nifty Midcap 100", "Chemicals"),
    ("TATAELXSI.NS", "Tata Elxsi", "Nifty Midcap 100", "Information Technology"),
    ("BAJAJHLDNG.NS", "Bajaj Holdings", "Nifty Midcap 100", "Financial Services"),
    ("PAGEIND.NS", "Page Industries", "Nifty Midcap 100", "Textiles"),
    ("ABCAPITAL.NS", "Aditya Birla Capital", "Nifty Midcap 100", "Financial Services"),
    ("INDHOTEL.NS", "Indian Hotels Company", "Nifty Midcap 100", "Hospitality"),
    ("SUPREMEIND.NS", "Supreme Industries", "Nifty Midcap 100", "Plastics"),
    ("ESCORTS.NS", "Escorts Kubota", "Nifty Midcap 100", "Automobile"),
    ("JUBLFOOD.NS", "Jubilant FoodWorks", "Nifty Midcap 100", "Retail/FMCG"),
    ("CONCOR.NS", "Container Corporation of India", "Nifty Midcap 100", "Logistics"),
    ("INDIANB.NS", "Indian Bank", "Nifty Midcap 100", "Financial Services"),
    ("UNIONBANK.NS", "Union Bank of India", "Nifty Midcap 100", "Financial Services"),
    ("BANKINDIA.NS", "Bank of India", "Nifty Midcap 100", "Financial Services"),
    ("YESBANK.NS", "Yes Bank", "Nifty Midcap 100", "Financial Services"),
    ("RBLBANK.NS", "RBL Bank", "Nifty Midcap 100", "Financial Services"),
    ("PEL.NS", "Piramal Enterprises", "Nifty Midcap 100", "Financial Services"),
    ("GICRE.NS", "General Insurance Corporation", "Nifty Midcap 100", "Financial Services"),
    ("NIACL.NS", "New India Assurance", "Nifty Midcap 100", "Financial Services"),
    ("APLAPOLLO.NS", "APL Apollo Tubes", "Nifty Midcap 100", "Metals"),
    ("POLYCAB.NS", "Polycab India", "Nifty Midcap 100", "Consumer Durables"),
    ("KEI.NS", "KEI Industries", "Nifty Midcap 100", "Consumer Durables"),
    ("CGPOWER.NS", "CG Power and Industrial Solutions", "Nifty Midcap 100", "Capital Goods"),
    ("THERMAX.NS", "Thermax", "Nifty Midcap 100", "Capital Goods"),
    ("BHARATFORG.NS", "Bharat Forge", "Nifty Midcap 100", "Auto Components"),
    ("SCHAEFFLER.NS", "Schaeffler India", "Nifty Midcap 100", "Auto Components"),
    ("ABFRL.NS", "Aditya Birla Fashion and Retail", "Nifty Midcap 100", "Retail"),
    ("PVRINOX.NS", "PVR INOX", "Nifty Midcap 100", "Media/Entertainment"),
    ("ZEEL.NS", "Zee Entertainment Enterprises", "Nifty Midcap 100", "Media/Entertainment"),
    ("SUNTV.NS", "Sun TV Network", "Nifty Midcap 100", "Media/Entertainment"),
    ("LALPATHLAB.NS", "Dr Lal PathLabs", "Nifty Midcap 100", "Healthcare"),
    ("METROPOLIS.NS", "Metropolis Healthcare", "Nifty Midcap 100", "Healthcare"),
    ("SYNGENE.NS", "Syngene International", "Nifty Midcap 100", "Pharma"),
    ("GLAND.NS", "Gland Pharma", "Nifty Midcap 100", "Pharma"),
    ("LAURUSLABS.NS", "Laurus Labs", "Nifty Midcap 100", "Pharma"),
    ("IPCALAB.NS", "IPCA Laboratories", "Nifty Midcap 100", "Pharma"),
    ("GLENMARK.NS", "Glenmark Pharmaceuticals", "Nifty Midcap 100", "Pharma"),
    ("NAVINFLUOR.NS", "Navin Fluorine International", "Nifty Midcap 100", "Chemicals"),
    ("CLEAN.NS", "Clean Science and Technology", "Nifty Midcap 100", "Chemicals"),
    ("FINEORG.NS", "Fine Organic Industries", "Nifty Midcap 100", "Chemicals"),
    ("ASTRAL.NS", "Astral Limited", "Nifty Midcap 100", "Plastics"),
    ("RAMCOCEM.NS", "Ramco Cements", "Nifty Midcap 100", "Cement"),
    ("JKCEMENT.NS", "JK Cement", "Nifty Midcap 100", "Cement"),
    ("GMRAIRPORT.NS", "GMR Airports", "Nifty Midcap 100", "Infrastructure"),
    ("IRFC.NS", "Indian Railway Finance Corp", "Nifty Midcap 100", "Financial Services"),
    ("RVNL.NS", "Rail Vikas Nigam", "Nifty Midcap 100", "Infrastructure"),
    ("IRB.NS", "IRB Infrastructure Developers", "Nifty Midcap 100", "Infrastructure"),
]


def get_universe():
    """Return the list of (symbol, name, index_membership, sector) tuples."""
    return UNIVERSE


def universe_size():
    return len(UNIVERSE)
