"""
Use Llama 3.2 model for converting natural language question to query
"""

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pymssql
import subprocess
import warnings
import time
import psutil
import logging
import platform
import re

# --- Streamlit App Layout Setup ---

# Sidebar setup
st.sidebar.title("SmartShelf")
app_selector = st.sidebar.selectbox(
    "Select an option:", ["", "AI Assistant", "Sales Forecast"]
)

# Display welcome message if no app is selected
if app_selector == "":
    st.markdown(
        "<h1 style='font-size: 40px;'>SmartShelf</h1>", unsafe_allow_html=True
    )  # Increased title size
    st.markdown(
        "<p style='font-size: 18px;'>Hello! Please select an option from the menu on the left.<br>"
        "To ask inventory related questions select AI Assistant option, and for sales forecast, please select the Sales Forecast option.</p>",
        unsafe_allow_html=True,
    )  # Increased message size

# --- AI Assistant Code ---

if app_selector == "AI Assistant":
    # Suppress warnings
    warnings.filterwarnings("ignore")

    # Set up logging configuration
    logging.basicConfig(
        filename="llama_log.txt", level=logging.INFO, format="%(message)s"
    )

    # Log hardware information function
    def log_hardware_info():
        cpu_info = platform.processor()
        ram_info = psutil.virtual_memory()
        disk_info = psutil.disk_usage("/")

        logging.info("--- Hardware Info ---")
        logging.info(f"CPU: {cpu_info}")
        logging.info(f"Total RAM: {ram_info.total / (1024 ** 3):.2f} GB")
        logging.info(f"Available RAM: {ram_info.available / (1024 ** 3):.2f} GB")
        logging.info(f"Total Disk Space: {disk_info.total / (1024 ** 3):.2f} GB")
        logging.info(f"Available Disk Space: {disk_info.free / (1024 ** 3):.2f} GB")

    # Log hardware info at the start
    log_hardware_info()

    # Database connection parameters
    SERVER = "localhost"
    DATABASE = "ContosoRetailDW"
    USERNAME = "**"
    PASSWORD = "********"

    conn = pymssql.connect(
        server=SERVER, user=USERNAME, password=PASSWORD, database=DATABASE, as_dict=True
    )

    # Function to execute SQL queries
    def execute_sql(query):
        try:
            # Create a cursor and execute the query
            cursor = conn.cursor()
            cursor.execute(query)

            # Fetch all data from the query result
            data = cursor.fetchall()

            # Get column names from the cursor description
            columns = [desc[0] for desc in cursor.description]

            # Create a DataFrame using the fetched data and column names
            df = pd.DataFrame(data, columns=columns)

            return df

        except Exception as e:
            print(f"An error occurred while executing the SQL query: {e}")
            return None

    # Function to generate SQL from natural language
    def generate_sql(natural_language_query):
        prompt = (
            "The database has a table named dbo.DimMachine with the following columns - MachineKey, MachineLabel, StoreKey, MachineType, MachineName, MachineDescription, VendorName, MachineOS, MachineSource, MachineHardware, MachineSoftware, Status, ServiceStartDate, DecommissionDate, LastModifiedDate, ETLLoadID, LoadDate, UpdateDate.\n\n"
            "The database has another table named dbo.DimProductSubcategory with the following columns - ProductSubcategoryKey, ProductSubcategoryLabel, ProductSubcategoryName, ProductSubcategoryDescription, ProductCategoryKey, ETLLoadID, LoadDate, UpdateDate.\n\n"
            "The database has another table named dbo.DimProduct with the following columns - ProductKey, ProductLabel, ProductName, ProductDescription, ProductSubcategoryKey, Manufacturer, BrandName, ClassID, ClassName, StyleID, StyleName, ColorID, ColorName, Size, SizeRange, SizeUnitMeasureID, Weight, WeightUnitMeasureID, UnitOfMeasureID, UnitOfMeasureName, StockTypeID, StockTypeName, UnitCost, UnitPrice, AvailableForSaleDate, StopSaleDate, Status, ImageURL, ProductURL, ETLLoadID, LoadDate, UpdateDate.\n\n"
            "The database has another table named dbo.DimProductCategory with the following columns - ProductCategoryKey, ProductCategoryLabel, ProductCategoryName, ProductCategoryDescription, ETLLoadID, LoadDate, UpdateDate.\n\n"
            "The database has another table named dbo.DimEntity with the following columns - EntityKey, EntityLabel, ParentEntityKey, ParentEntityLabel, EntityName, EntityDescription, EntityType, StartDate, EndDate, Status, ETLLoadID, LoadDate, UpdateDate.\n\n"
            "The database has another table named dbo.DimSalesTerritory with the following columns - SalesTerritoryKey, GeographyKey, SalesTerritoryLabel, SalesTerritoryName, SalesTerritoryRegion, SalesTerritoryCountry, SalesTerritoryGroup, SalesTerritoryLevel, SalesTerritoryManager, StartDate, EndDate, Status, ETLLoadID, LoadDate, UpdateDate.\n\n"
            "The database has another table named dbo.DimCurrency with the following columns - CurrencyKey, CurrencyLabel, CurrencyName, CurrencyDescription, ETLLoadID, LoadDate, UpdateDate.\n\n"
            "The database has another table named dbo.DimOutage with the following columns - OutageKey, OutageLabel, OutageName, OutageDescription, OutageType, OutageTypeDescription, OutageSubType, OutageSubTypeDescription, ETLLoadID, LoadDate, UpdateDate.\n\n"
            "The database has another table named dbo.DimChannel with the following columns - ChannelKey, ChannelLabel, ChannelName, ChannelDescription, ETLLoadID, LoadDate, UpdateDate.\n\n"
            "The database has another table named dbo.DimScenario with the following columns - ScenarioKey, ScenarioLabel, ScenarioName, ScenarioDescription, ETLLoadID, LoadDate, UpdateDate.\n\n"
            "The database has another table named dbo.DimAccount with the following columns - AccountKey, ParentAccountKey, AccountLabel, AccountName, AccountDescription, AccountType, Operator, CustomMembers, ValueType, CustomMemberOptions, ETLLoadID, LoadDate, UpdateDate.\n\n"
            "The database has another table named dbo.DimPromotion with the following columns - PromotionKey, PromotionLabel, PromotionName, PromotionDescription, DiscountPercent, PromotionType, PromotionCategory, StartDate, EndDate, MinQuantity, MaxQuantity, ETLLoadID, LoadDate, UpdateDate.\n\n"
            "The database has another table named dbo.DimCustomer with the following columns - CustomerKey, GeographyKey, CustomerLabel, Title, FirstName, MiddleName, LastName, NameStyle, BirthDate, MaritalStatus, Suffix, Gender, EmailAddress, YearlyIncome, TotalChildren, NumberChildrenAtHome, Education, Occupation, HouseOwnerFlag, NumberCarsOwned, AddressLine1, AddressLine2, Phone, DateFirstPurchase, CustomerType, CompanyName, ETLLoadID, LoadDate, UpdateDate.\n\n"
            "The database has another table named dbo.DimEmployee with the following columns - EmployeeKey, ParentEmployeeKey, FirstName, LastName, MiddleName, Title, HireDate, BirthDate, EmailAddress, Phone, MaritalStatus, EmergencyContactName, EmergencyContactPhone, SalariedFlag, Gender, PayFrequency, BaseRate, VacationHours, CurrentFlag, SalesPersonFlag, DepartmentName, StartDate, EndDate, Status, ETLLoadID, LoadDate, UpdateDate.\n\n"
            "The database has another table named dbo.DimDate with the following columns - Datekey, FullDateLabel, DateDescription, CalendarYear, CalendarYearLabel, CalendarHalfYear, CalendarHalfYearLabel, CalendarQuarter, CalendarQuarterLabel, CalendarMonth, CalendarMonthLabel, CalendarWeek, CalendarWeekLabel, CalendarDayOfWeek, CalendarDayOfWeekLabel, FiscalYear, FiscalYearLabel, FiscalHalfYear, FiscalHalfYearLabel, FiscalQuarter, FiscalQuarterLabel, FiscalMonth, FiscalMonthLabel, IsWorkDay, IsHoliday, HolidayName, EuropeSeason, NorthAmericaSeason, AsiaSeason.\n\n"
            "The database has another table named dbo.DimStore with the following columns - StoreKey, GeographyKey, StoreManager, StoreType, StoreName, StoreDescription, Status, OpenDate, CloseDate, EntityKey, ZipCode, ZipCodeExtension, StorePhone, StoreFax, AddressLine1, AddressLine2, CloseReason, EmployeeCount, SellingAreaSize, LastRemodelDate, GeoLocation, Geometry, ETLLoadID, LoadDate, UpdateDate.\n\n"
            "The database has another table named dbo.DimGeography with the following columns - GeographyKey, GeographyType, ContinentName, CityName, StateProvinceName, RegionCountryName, Geometry, ETLLoadID, LoadDate, UpdateDate.\n\n"
            "The database has a table named dbo.FactExchangeRate with the following columns - ExchangeRateKey, CurrencyKey, DateKey, AverageRate, EndOfDayRate, ETLLoadID, LoadDate, UpdateDate.\n\n"
            "The database has another table named dbo.FactITMachine with the following columns - ITMachinekey, MachineKey, Datekey, CostAmount, CostType, ETLLoadID, LoadDate, UpdateDate.\n\n"
            "The database has another table named dbo.FactITSLA with the following columns - ITSLAkey, DateKey, StoreKey, MachineKey, OutageKey, OutageStartTime, OutageEndTime, DownTime, ETLLoadID, LoadDate, UpdateDate.\n\n"
            "The database has another table named dbo.FactOnlineSales with the following columns - OnlineSalesKey, DateKey, StoreKey, ProductKey, PromotionKey, CurrencyKey, CustomerKey, SalesOrderNumber, SalesOrderLineNumber, SalesQuantity, SalesAmount, ReturnQuantity, ReturnAmount, DiscountQuantity, DiscountAmount, TotalCost, UnitCost, UnitPrice, ETLLoadID, LoadDate, UpdateDate.\n\n"
            "The database has another table named dbo.FactStrategyPlan with the following columns - StrategyPlanKey, Datekey, EntityKey, ScenarioKey, AccountKey, CurrencyKey, ProductCategoryKey, Amount, ETLLoadID, LoadDate, UpdateDate.\n\n"
            "The database has another table named dbo.FactSales with the following columns - SalesKey, DateKey, channelKey, StoreKey, ProductKey, PromotionKey, CurrencyKey, UnitCost, UnitPrice, SalesQuantity, ReturnQuantity, ReturnAmount, DiscountQuantity, DiscountAmount, TotalCost, SalesAmount, ETLLoadID, LoadDate, UpdateDate.\n\n"
            "The database has another table named dbo.FactInventory with the following columns - InventoryKey, DateKey, StoreKey, ProductKey, CurrencyKey, OnHandQuantity, OnOrderQuantity, SafetyStockQuantity, UnitCost, DaysInStock, MinDayInStock, MaxDayInStock, Aging, ETLLoadID, LoadDate, UpdateDate.\n\n"
            "The database has another table named dbo.FactSalesQuota with the following columns - SalesQuotaKey, ChannelKey, StoreKey, ProductKey, DateKey, CurrencyKey, ScenarioKey, SalesQuantityQuota, SalesAmountQuota, GrossMarginQuota, ETLLoadID, LoadDate, UpdateDate.\n\n"
            "Do not use any table and column except the ones mentioned here. Do not assume any table and column name. Use only the table and column names mentioned here.\n\n"
            "Other instructions: The database is a data warehouse database. "
            "If the question asks for number specific result, focus on the numeric values from the generated results that are most relevant to the question asked. "
            "If the question asks for name or text specific result, focus on the name or text values from the generated results that are most relevant to the question asked. "
            "If the question asks for a combination of number and name or text specific result, focus on the numeric and name or text values from the generated results that are most relevant to the question asked. "
            "Interpret them properly and convert them to proper English language questions. "
            "Understand the generated output and convert them to proper English language sentences. The results shall be correctly interpreted by you in order to do this. "
            "Do not just focus on the first field in the column. Analyze all the columns generated in the SQL output and interpret them. "
            "Consider that collective interpretation of the result generated, and convert it to a proper English language sentence. "
            "If the SQL output has more than one row, consider those rows too. Interpret them accurately. "
            "After interpreting all those rows, convert those interpretations to properly written English language sentence. "
            "Combine the information in each row and construct a properly written English language sentence for the natural language (English) output. "
            "For SQL outputs with more than one row, create a table for the final output in natural language (English). "
            "Remember you are most intelligent assistant for this work as a Microsoft SQL Server Analyst. "
            "The database has maximum year as 2011 and this is year 2024 as of now.\n\n"
            "The database schema features several key relationships through foreign keys. The DimCustomer table references DimGeography via the GeographyKey. "
            "DimMachine connects to DimStore through StoreKey. In product categorization, DimProduct links to DimProductSubcategory via ProductSubcategoryKey, "
            "while DimProductSubcategory references DimProductCategory through ProductCategoryKey. The DimStore table also references DimGeography through GeographyKey. "
            "Fact tables are interconnected with dimension tables, such as FactInventory, which links to DimCurrency, DimDate, DimProduct, and DimStore using their respective keys. "
            "FactOnlineSales connects with DimCurrency, DimCustomer, DimDate, DimProduct, DimPromotion, and DimStore. Similarly, FactSales references DimChannel, DimCurrency, DimDate, DimProduct, DimPromotion, and DimStore. "
            "Other fact tables like FactSalesQuota and FactStrategyPlan maintain relationships with various dimensions, ensuring robust connectivity across the database."
            "FactStrategyPlan.AccountKey references DimAccount.AccountKey to link strategic plans with specific accounts."
            "FactSales.channelKey references DimChannel.ChannelKey to associate sales data with particular sales channels."
            "FactSalesQuota.ChannelKey references DimChannel.ChannelKey to connect sales quotas to specific sales channels."
            "FactExchangeRate.CurrencyKey references DimCurrency.CurrencyKey to relate exchange rates to the respective currencies."
            "FactInventory.CurrencyKey references DimCurrency.CurrencyKey to tie inventory records to their corresponding currencies."
            "FactOnlineSales.CurrencyKey references DimCurrency.CurrencyKey to associate online sales transactions with the relevant currencies."
            "FactSales.CurrencyKey references DimCurrency.CurrencyKey to link sales data to the appropriate currencies."
            "FactSalesQuota.CurrencyKey references DimCurrency.CurrencyKey to connect sales quotas to their respective currencies."
            "FactStrategyPlan.CurrencyKey references DimCurrency.CurrencyKey to relate strategic plans to the appropriate currencies."
            "FactOnlineSales.CustomerKey references DimCustomer.CustomerKey to link online sales to specific customers."
            "FactExchangeRate.DateKey references DimDate.DateKey to associate exchange rates with specific dates."
            "FactInventory.DateKey references DimDate.DateKey to tie inventory records to their respective dates."
            "FactITMachine.DateKey references DimDate.DateKey to relate IT machine records to specific dates."
            "FactITSLA.DateKey references DimDate.DateKey to connect service level agreements to their corresponding dates."
            "FactOnlineSales.DateKey references DimDate.DateKey to associate online sales with specific transaction dates."
            "FactSales.DateKey references DimDate.DateKey to link sales data to the relevant transaction dates."
            "FactSalesQuota.DateKey references DimDate.DateKey to associate sales quotas with specific dates."
            "FactStrategyPlan.DateKey references DimDate.DateKey to relate strategic plans to their respective dates."
            "FactStrategyPlan.EntityKey references DimEntity.EntityKey to connect strategic plans to specific entities."
            "DimCustomer.GeographyKey references DimGeography.GeographyKey to associate customers with their geographical locations."
            "DimSalesTerritory.GeographyKey references DimGeography.GeographyKey to link sales territories to specific geographical areas."
            "DimStore.GeographyKey references DimGeography.GeographyKey to relate stores to their respective geographical regions."
            "FactITMachine.MachineKey references DimMachine.MachineKey to connect IT machine records to specific machines."
            "FactITSLA.MachineKey references DimMachine.MachineKey to link service level agreements to the relevant machines."
            "FactITSLA.OutageKey references DimOutage.OutageKey to associate service level agreements with specific outages."
            "FactInventory.ProductKey references DimProduct.ProductKey to connect inventory records to specific products."
            "FactOnlineSales.ProductKey references DimProduct.ProductKey to associate online sales transactions with the relevant products."
            "FactSales.ProductKey references DimProduct.ProductKey to link sales data to specific products sold."
            "FactSalesQuota.ProductKey references DimProduct.ProductKey to associate sales quotas with specific products."
            "DimProductSubcategory.ProductCategoryKey references DimProductCategory.ProductCategoryKey to link product subcategories to their respective categories."
            "FactStrategyPlan.ProductCategoryKey references DimProductCategory.ProductCategoryKey to connect strategic plans to specific product categories."
            "DimProduct.ProductSubcategoryKey references DimProductSubcategory.ProductSubcategoryKey to relate products to their respective subcategories."
            "FactOnlineSales.PromotionKey references DimPromotion.PromotionKey to associate online sales with specific promotions."
            "FactSales.PromotionKey references DimPromotion.PromotionKey to link sales data to relevant promotions."
            "FactSalesQuota.ScenarioKey references DimScenario.ScenarioKey to connect sales quotas to specific business scenarios."
            "FactStrategyPlan.ScenarioKey references DimScenario.ScenarioKey to relate strategic plans to particular business scenarios."
            "DimMachine.StoreKey references DimStore.StoreKey to associate machines with their respective stores."
            "FactInventory.StoreKey references DimStore.StoreKey to link inventory records to specific stores."
            "FactITSLA.StoreKey references DimStore.StoreKey to connect service level agreements to their respective stores."
            "FactOnlineSales.StoreKey references DimStore.StoreKey to associate online sales transactions with specific stores."
            "FactSales.StoreKey references DimStore.StoreKey to link sales data to the relevant stores."
            "FactSalesQuota.StoreKey references DimStore.StoreKey to connect sales quotas to specific stores.\n\n"
            "Here are some examples of questions and their corresponding SQL:\n"
            "1. What are the products in the database? -> SELECT * FROM dbo.DimProduct;\n"
            "2. List the names of all products. -> SELECT ProductName FROM dbo.DimProduct;\n"
            "3. Get the product with ID 1. -> SELECT * FROM dbo.DimProduct WHERE ProductKey = 1;\n"
            "4. How many items are there in the product category 'Economy'? -> SELECT COUNT(*) FROM dbo.DimProduct WHERE ClassName = 'Economy';\n"
            "5. What is the average price of products with size 'Small'? -> SELECT AVG(UnitPrice) FROM dbo.DimProduct WHERE Size = 'Small';\n"
            "6. What is the most expensive product? -> SELECT ProductName FROM dbo.DimProduct WHERE UnitPrice = (SELECT MAX(UnitPrice) FROM dbo.DimProduct);\n"
            "7. How many Contoso brand products do we have? -> SELECT COUNT(*) FROM dbo.DimProduct WHERE Manufacturer = 'Contoso, Ltd';\n"
            "8. What is the product description for the 'Contoso 4G MP3 Player E400 Green'? -> SELECT ProductDescription FROM dbo.DimProduct WHERE ProductName = 'Contoso 4G MP3 Player E400 Green';\n"
            "9. List all products with a unit price greater than $20. -> SELECT ProductName FROM dbo.DimProduct WHERE UnitPrice > 20;\n"
            "10. How many products are available for sale? -> SELECT COUNT(*) FROM dbo.DimProduct WHERE Status = 'On';\n"
            "11. What is the total weight of all Contoso products? -> SELECT SUM(Weight) FROM dbo.DimProduct WHERE Manufacturer = 'Contoso, Ltd';\n"
            "12. What is the cheapest product? -> SELECT ProductName, UnitPrice FROM dbo.DimProduct WHERE UnitPrice = (SELECT MIN(UnitPrice) FROM dbo.DimProduct);\n"
            "13. What is the average sales amount for products by Contoso, Ltd? -> SELECT DimProduct.Manufacturer AS Supplier, AVG(FactSales.SalesAmount) AS AverageSalesAmount FROM FactSales INNER JOIN DimProduct ON FactSales.ProductKey = DimProduct.ProductKey WHERE DimProduct.Manufacturer = 'Contoso, Ltd' GROUP BY DimProduct.Manufacturer;\n"
            "14. Which are the top 10 stores with highest excess inventory level for Contoso 2G MP3 Player E200 Silver? -> SELECT TOP 10 DimStore.StoreName, (FactInventory.OnHandQuantity - FactInventory.SafetyStockQuantity) AS ExcessInventory FROM DimStore INNER JOIN FactInventory ON DimStore.StoreKey = FactInventory.StoreKey INNER JOIN DimProduct ON FactInventory.ProductKey = DimProduct.ProductKey WHERE DimProduct.ProductName = 'Contoso 2G MP3 Player E200 Silver' AND FactInventory.OnHandQuantity > FactInventory.SafetyStockQuantity ORDER BY ExcessInventory DESC;\n"
            "15. What is the average sales amount for products by Contoso, Ltd? -> SELECT DimProduct.Manufacturer AS Supplier, AVG(FactSales.SalesAmount) AS AverageSalesAmount FROM FactSales INNER JOIN DimProduct ON FactSales.ProductKey = DimProduct.ProductKey WHERE DimProduct.Manufacturer = 'Contoso, Ltd' GROUP BY DimProduct.Manufacturer;\n"
            "16. List all the product categories. -> SELECT ProductCategoryName FROM DimProductCategory;\n"
            "17. How many products belong to Economy class? -> SELECT COUNT(*) AS NumberOfEconomyClassProducts FROM DimProduct WHERE ClassName = 'Economy';\n"
            "18. How many stores do we have in Japan? -> SELECT COUNT(*) AS NumberOfStoresInRegion FROM DimStore ds JOIN DimGeography dg ON ds.GeographyKey = dg.GeographyKey WHERE dg.RegionCountryName = 'Japan';\n"
            "19. What is the total quantity of Contoso 2G MP3 Player E200 Silver in stock? -> SELECT SUM(I.OnHandQuantity) FROM FactInventory I JOIN DimProduct P ON I.ProductKey = P.ProductKey WHERE P.ProductName = 'Contoso 2G MP3 Player E200 Silver';\n"
            "20. How many products need to be reordered due to on hand quantity being less than safety stock quantity? -> SELECT COUNT(*) AS ProductsToReorder FROM dbo.FactInventory WHERE OnHandQuantity < SafetyStockQuantity;\n"
            "21. Which products are currently out of stock at each store? -> SELECT s.StoreName, p.ProductName FROM dbo.FactInventory i JOIN dbo.DimProduct p ON i.ProductKey = p.ProductKey JOIN dbo.DimStore s ON i.StoreKey = s.StoreKey WHERE i.OnHandQuantity = 0;\n"
            "22. Which products have the lowest inventory levels in each store? -> SELECT s.StoreName, p.ProductName, i.OnHandQuantity FROM dbo.FactInventory i JOIN dbo.DimProduct p ON i.ProductKey = p.ProductKey JOIN dbo.DimStore s ON i.StoreKey = s.StoreKey WHERE i.OnHandQuantity < i.SafetyStockQuantity ORDER BY s.StoreName, i.OnHandQuantity ASC;\n"
            "23. What is the total inventory value of each product in Contoso Redmond store? -> SELECT s.StoreName, p.ProductName, SUM(i.OnHandQuantity * p.UnitCost) AS TotalInventoryValue FROM dbo.FactInventory i JOIN dbo.DimProduct p ON i.ProductKey = p.ProductKey JOIN dbo.DimStore s ON i.StoreKey = s.StoreKey WHERE s.StoreName = 'Contoso Redmond Store' GROUP BY s.StoreName, p.ProductName;\n"
            "24. Which products are about to reach their safety stock level at Contoso Sunnyside store? -> SELECT p.ProductName, i.OnHandQuantity, i.SafetyStockQuantity FROM dbo.FactInventory i JOIN dbo.DimProduct p ON i.ProductKey = p.ProductKey JOIN dbo.DimStore s ON i.StoreKey = s.StoreKey WHERE s.StoreName = 'Contoso Sunnyside Store' AND i.OnHandQuantity <= i.SafetyStockQuantity + 5;\n"
            "25. What is the average days in stock for all products at Contoso Appleton store? -> SELECT AVG(i.DaysInStock) AS AverageDaysInStock FROM dbo.FactInventory i JOIN dbo.DimStore s ON i.StoreKey = s.StoreKey WHERE s.StoreName = 'Contoso Appleton Store';\n"
            "26. Which product has the highest unit cost at Contoso Englewood store? -> SELECT TOP 1 p.ProductName, p.UnitCost FROM dbo.DimProduct p JOIN dbo.FactInventory i ON p.ProductKey = i.ProductKey JOIN dbo.DimStore s ON i.StoreKey = s.StoreKey WHERE s.StoreName = 'Contoso Englewood Store' ORDER BY p.UnitCost DESC;\n"
            "27. Which are the top 5 products that have sold more than the current on hand quantity at Contoso Humble store? -> SELECT TOP 5 p.ProductName, i.OnHandQuantity, SUM(s.SalesQuantity) AS TotalSold FROM dbo.FactInventory i JOIN dbo.DimProduct p ON i.ProductKey = p.ProductKey JOIN dbo.FactSales s ON p.ProductKey = s.ProductKey JOIN dbo.DimStore st ON i.StoreKey = st.StoreKey WHERE st.StoreName = 'Contoso Humble Store' GROUP BY p.ProductName, i.OnHandQuantity HAVING SUM(s.SalesQuantity) > i.OnHandQuantity ORDER BY TotalSold DESC;\n"
            "28. What is the average unit price of products that are in stock at Contoso Dallas store? -> SELECT AVG(p.UnitPrice) AS AverageUnitPrice FROM dbo.DimProduct p JOIN dbo.FactInventory i ON p.ProductKey = i.ProductKey JOIN dbo.DimStore st ON i.StoreKey = st.StoreKey WHERE st.StoreName = 'Contoso Dallas Store' AND i.OnHandQuantity > 0;\n"
            "29. Which product has the lowest available stock at Contoso Georgetown store? -> SELECT TOP 1 p.ProductName, i.OnHandQuantity FROM dbo.DimProduct p JOIN dbo.FactInventory i ON p.ProductKey = i.ProductKey JOIN dbo.DimStore st ON i.StoreKey = st.StoreKey WHERE st.StoreName = 'Contoso Georgetown Store' ORDER BY i.OnHandQuantity ASC;\n"
            "30. What is the total quantity of a specific product currently in stock across all stores? -> SELECT SUM(i.OnHandQuantity) AS TotalQuantity FROM dbo.FactInventory i JOIN dbo.DimProduct p ON i.ProductKey = p.ProductKey WHERE p.ProductName = 'Contoso 4G MP3 Player E400 Orange';\n"
            "31. Which product category has the highest average unit cost at Contoso Brooklyn store? -> SELECT TOP 1 cat.ProductCategoryName, AVG(p.UnitCost) AS AverageUnitCost FROM dbo.DimProduct p JOIN dbo.DimProductSubcategory subcat ON p.ProductSubcategoryKey = subcat.ProductSubcategoryKey JOIN dbo.DimProductCategory cat ON subcat.ProductCategoryKey = cat.ProductCategoryKey JOIN dbo.FactInventory i ON p.ProductKey = i.ProductKey JOIN dbo.DimStore st ON i.StoreKey = st.StoreKey WHERE st.StoreName = 'Contoso Brooklyn Store' GROUP BY cat.ProductCategoryName ORDER BY AverageUnitCost DESC;\n"
            "32. How many products are currently out of stock at Contoso Queens store? -> SELECT COUNT(*) AS OutOfStockCount FROM dbo.FactInventory i JOIN dbo.DimStore st ON i.StoreKey = st.StoreKey WHERE st.StoreName = 'Contoso Queens Store' AND i.OnHandQuantity = 0;\n"
            "33. What is the total safety stock quantity for all products at Contoso Lewiston store? -> SELECT SUM(i.SafetyStockQuantity) AS TotalSafetyStock FROM dbo.FactInventory i JOIN dbo.DimStore st ON i.StoreKey = st.StoreKey WHERE st.StoreName = 'Contoso Lewiston Store';\n"
            "34. Which product has the largest difference between on-hand quantity and safety stock quantity at Contoso Bellevue store? -> SELECT TOP 1 p.ProductName, (i.OnHandQuantity - i.SafetyStockQuantity) AS QuantityDifference FROM dbo.FactInventory i JOIN dbo.DimProduct p ON i.ProductKey = p.ProductKey JOIN dbo.DimStore st ON i.StoreKey = st.StoreKey WHERE st.StoreName = 'Contoso Bellevue Store' ORDER BY QuantityDifference DESC;\n"
            "35. Which three products have the lowest stock levels at a Contoso Madison store, Contoso Burlington store, and Contoso Appleton store? What are those levels? -> SELECT TOP 3 p.ProductName, i.OnHandQuantity FROM dbo.FactInventory i JOIN dbo.DimProduct p ON i.ProductKey = p.ProductKey JOIN dbo.DimStore st ON i.StoreKey = st.StoreKey WHERE st.StoreName IN ('Contoso Madison Store', 'Contoso Burlington Store', 'Contoso Appleton Store') ORDER BY i.OnHandQuantity ASC;\n"
            "36. Which product category has the highest total inventory cost at Contoso Midland store, and what is the total cost? -> SELECT TOP 1 pc.ProductCategoryName, SUM(i.OnHandQuantity * p.UnitCost) AS TotalInventoryCost FROM dbo.FactInventory i JOIN dbo.DimProduct p ON i.ProductKey = p.ProductKey JOIN dbo.DimProductSubcategory ps ON p.ProductSubcategoryKey = ps.ProductSubcategoryKey JOIN dbo.DimProductCategory pc ON ps.ProductCategoryKey = pc.ProductCategoryKey JOIN dbo.DimStore st ON i.StoreKey = st.StoreKey WHERE st.StoreName = 'Contoso Midland Store' GROUP BY pc.ProductCategoryName ORDER BY TotalInventoryCost DESC;\n"
            "37. What are the total quantities on order and on hand for each manufacturer at the Contoso Longview store, sorted by the highest on-order quantity first? -> SELECT p.Manufacturer AS VendorName, SUM(i.OnOrderQuantity) AS TotalOnOrder, SUM(i.OnHandQuantity) AS TotalOnHand FROM dbo.FactInventory i JOIN dbo.DimProduct p ON i.ProductKey = p.ProductKey JOIN dbo.DimStore st ON i.StoreKey = st.StoreKey WHERE st.StoreName = 'Contoso Longview Store' GROUP BY p.Manufacturer ORDER BY TotalOnOrder DESC, TotalOnHand DESC;\n"
            "38. Which products at Contoso Texas City store and Contoso Humble store have the highest unit cost and also meet or exceed their safety stock levels? -> SELECT TOP 1 p.ProductName, p.UnitCost, i.OnHandQuantity FROM dbo.FactInventory i JOIN dbo.DimProduct p ON i.ProductKey = p.ProductKey JOIN dbo.DimStore st ON i.StoreKey = st.StoreKey WHERE st.StoreName IN ('Contoso Texas City Store', 'Contoso Humble Store') AND i.OnHandQuantity >= i.SafetyStockQuantity ORDER BY p.UnitCost DESC;\n"
            "39. Which products at Contoso Humble store, Contoso Texas City store, Contoso Austin store, Contoso Pasadena store, and Contoso Georgetown store have the highest unit cost and also meet or exceed their safety stock levels? -> SELECT TOP 10 st.StoreName, p.ProductName, p.UnitCost, i.OnHandQuantity FROM dbo.FactInventory i JOIN dbo.DimProduct p ON i.ProductKey = p.ProductKey JOIN dbo.DimStore st ON i.StoreKey = st.StoreKey WHERE st.StoreName IN ('Contoso Humble Store', 'Contoso Texas City Store', 'Contoso Austin Store', 'Contoso Pasadena Store', 'Contoso Georgetown Store') AND i.OnHandQuantity >= i.SafetyStockQuantity ORDER BY p.UnitCost DESC;\n"
            "40. Which are the top 5 vendors with the highest total inventory value at the Contoso Plano store? -> SELECT TOP 5 p.Manufacturer AS VendorName, SUM(i.OnHandQuantity * p.UnitCost) AS TotalInventoryValue FROM dbo.FactInventory i JOIN dbo.DimProduct p ON i.ProductKey = p.ProductKey JOIN dbo.DimStore st ON i.StoreKey = st.StoreKey WHERE st.StoreName = 'Contoso Plano Store' GROUP BY p.Manufacturer ORDER BY TotalInventoryValue DESC;\n"
            "41. What are the three highest-selling product categories in terms of on-hand quantity across all stores, and what are their total quantities? -> SELECT TOP 3 pc.ProductCategoryName, SUM(i.OnHandQuantity) AS TotalOnHandQuantity FROM dbo.FactInventory i JOIN dbo.DimProduct p ON i.ProductKey = p.ProductKey JOIN dbo.DimProductSubcategory ps ON p.ProductSubcategoryKey = ps.ProductSubcategoryKey JOIN dbo.DimProductCategory pc ON ps.ProductCategoryKey = pc.ProductCategoryKey GROUP BY pc.ProductCategoryName ORDER BY TotalOnHandQuantity DESC;\n"
            "42. For Contoso New Brunswick store, what are the top 5 products with the highest total inventory value in stock, and what is the value for each? -> SELECT TOP 5 p.ProductName, (i.OnHandQuantity * p.UnitCost) AS TotalInventoryValue FROM dbo.FactInventory i JOIN dbo.DimProduct p ON i.ProductKey = p.ProductKey JOIN dbo.DimStore st ON i.StoreKey = st.StoreKey WHERE st.StoreName = 'Contoso New Brunswick Store' ORDER BY TotalInventoryValue DESC;\n"
            "43. What are the total inventory value and on-order quantity for each vendor at the Contoso Northampton store? -> SELECT m.VendorName, SUM(i.OnHandQuantity * p.UnitCost) AS TotalInventoryValue, SUM(i.OnOrderQuantity) AS TotalOnOrderQuantity FROM dbo.FactInventory i JOIN dbo.DimProduct p ON i.ProductKey = p.ProductKey JOIN dbo.DimStore st ON i.StoreKey = st.StoreKey JOIN dbo.DimMachine m ON i.StoreKey = m.StoreKey WHERE st.StoreName = 'Contoso Northampton Store' GROUP BY m.VendorName ORDER BY TotalInventoryValue DESC, TotalOnOrderQuantity DESC;\n"
            "44. Which countries do we have our stores in? Mention all those countries. -> SELECT DISTINCT RegionCountryName FROM DimGeography dg JOIN DimStore ds ON dg.GeographyKey = ds.GeographyKey ORDER BY RegionCountryName;\n"
            "45. How many stores do we have in India? Mention the number of stores we have in India. -> SELECT COUNT(*) AS NumberOfStoresInIndia FROM DimStore ds JOIN DimGeography dg ON ds.GeographyKey = dg.GeographyKey WHERE dg.RegionCountryName = 'India';\n"
            "46. How many colours are there in the product table? -> SELECT COUNT(DISTINCT ColorName) as cnt FROM dbo.DimProduct;\n"
            "47. Give top 10 rows from the product table -> SELECT TOP 10 * from dbo.DimProduct;\n"
            "48. How many products are there by each manufacturer? -> SELECT Manufacturer, COUNT(*) as num_products FROM dbo.DimProduct GROUP BY Manufacturer ORDER BY num_products DESC;\n"
            "49. What are sales for 2007 to 2009 from FactSales table -> SELECT YEAR(DateKey) AS Year, SUM(SalesAmount) AS TotalSales FROM [dbo].[FactSales] WHERE YEAR(DateKey) >= 2007 and YEAR(DateKey) <= 2009 GROUP BY YEAR(DateKey);\n"
            "50. Display if there is a relationship between inventory levels and sales quantity for product with ProductKey = 9 using a scatter plot. -> SELECT fi.OnHandQuantity AS Inventory, fs.SalesQuantity AS Sales FROM dbo.FactInventory fi JOIN dbo.FactSales fs ON fi.ProductKey = fs.ProductKey WHERE fi.ProductKey = 9 AND fs.DateKey = fi.DateKey;\n"
            "51. What is the total sales by each sales channel? -> SELECT DimChannel.ChannelName, SUM(FactSales.SalesAmount) AS TotalSales FROM FactSales JOIN DimChannel ON FactSales.ChannelKey = DimChannel.ChannelKey GROUP BY DimChannel.ChannelName ORDER BY TotalSales DESC;\n"
            "Check how the spacing for specific things are mentioned in the question, based on which you can generate and run the query. Generate full sentences and grammatically correct sentences in the output. "
            "For example: There are 710 products from Contoso, Ltd. Understand, and identify the context of the question asked correctly. "
            "Respond in very natural human like manner based on the question asked without missing specific natural language and grammatical components of the question asked. "
            "Return only the SQL query based on the following question, and don't include ``` and \\n in the output:\n"
            "Check the entire data given in the prompt. If any of the questions matches with the questions in the prompt, use the respective query only unless mentioned"
            f"Q: {natural_language_query}\nA:"
        )
        result = subprocess.run(
            ["ollama", "run", "llama3.2", prompt],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        sql_query = result.stdout.split("A:")[-1].strip()
        return sql_query

    # Function to determine chart type
    def generate_chart_type(natural_language_query):
        chart_types = {"bar": "bar", "line": "line", "pie": "pie", "scatter": "scatter"}
        for key in chart_types:
            if key in natural_language_query.lower():
                return chart_types[key]
        return "bar"  # Default to bar chart

    # Function to generate a graph
    def generate_graph(natural_language_query):
        try:
            sql_query = generate_sql(natural_language_query)
            chart_type = generate_chart_type(natural_language_query)
            df = execute_sql(sql_query)

            if df is None or df.empty:
                logging.error("No data returned from the query.")
                return

            prompt_viz = f"""
        Based on the SQL query results, please generate Python code to display a '{chart_type}' chart 
        using the provided DataFrame `df` (which already contains the data).
        
        Use the following columns:
        - x-axis: '{df.columns[0]}'
        - y-axis: '{df.columns[1]}'

        Do not redefine or create any sample data within the code. Use Matplotlib for plotting, 
        and include labels for both axes, a title, and rotated x-ticks.

        "Here are some examples of questions and their corresponding graphs:\n"
        1. "Display how many products are there by each manufacturer using bar graph."--> 
        # Assuming df is your DataFrame containing the data
        plt.figure(figsize=(10, 6)) # Setting figure size for better display

        # Plotting 'bar' chart
        plt.bar(df['Manufacturer'], df['num_products'])

        # Adding labels for both axes and a title
        plt.xlabel('Manufacturer')
        plt.ylabel('Number of Products')
        plt.title('Distribution of Manufacturers by Number of Products')

        # Rotating x-ticks for better readability
        plt.xticks(rotation=45)

        # Displaying the chart
        plt.tight_layout() # This is used to ensure that all elements are visible in the figure area
        plt.show()
        
        2. "Display how many products are there by each manufaturer using pie chart"--> 
        import matplotlib.pyplot as plt

        # Assuming df is your DataFrame containing the data
        plt.figure(figsize=(10, 6))  # Setting figure size for better display

        # Plotting the pie chart
        plt.pie(df['num_products'], labels=df['ColorName'], autopct='%1.1f%%', startangle=140)

        # Adding a title
        plt.title('Distribution of Products by Color Name')

        # Displaying the chart
        plt.show()
        
        3. "Display if there is a relationship between inventory levels and sales quantity for product with ProductKey = 9 using a scatter plot."-->
        # Set figure size for better display
        plt.figure(figsize=(10, 6))
        
        x_values = df.iloc[:,0]
        y_values = df.iloc[:,1]
        x_label = df.columns[0]
        y_label = df.columns[1]

        # Plotting scatter plot
        plt.scatter(x_values, y_values, color='blue', alpha=0.7)

        # Adding labels for both axes and a title
        plt.xlabel('Variable X')
        plt.ylabel('Variable Y')
        plt.title('Scatter Plot of Variable X vs Variable Y')

        # Displaying the chart
        plt.tight_layout()  # Ensures all elements are visible in the figure area
        plt.show()
        
        4. "Plot a line graph for sales from 2007 to 2009"-->
        "The generic response does not dynamically handle x-axis ticks for integer values like years. Below is the modified code to integrate this functionality explicitly".
        import matplotlib.pyplot as plt

        # Set figure size for better display
        plt.figure(figsize=(10, 6))

        # Extracting x and y values, and column labels dynamically
        x_values = df.iloc[:, 0]
        y_values = df.iloc[:, 1]
        x_label = df.columns[0]
        y_label = df.columns[1]

        # Plotting line chart
        plt.plot(x_values, y_values, color='blue', marker='o', linestyle='-')

        # Adding labels and integer x-axis tick settings directly
        plt.xlabel(x_label)
        plt.ylabel(y_label)
        plt.title(f'Line Plot of x_label vs y_label')
        plt.gca().set_xticks(x_values.astype(int))
        plt.gca().set_xticklabels(x_values.astype(int), rotation=45)

        plt.tight_layout()
        plt.show()

        "Check the entire data given in the prompt. If any of the questions matches with the questions in the prompt, use the respective query only unless mentioned"
        """
            result = subprocess.run(
                ["ollama", "run", "llama3.2", prompt_viz],
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            output = result.stdout
            code_match = re.search(r"```python\n(.*?)\n```", output, re.DOTALL)
            if not code_match:
                logging.error("No valid Python code block found in LLM response.")
                return

            visualization_code = code_match.group(1)
            # logging.info(f"Generated Python code: {visualization_code}")

            exec(
                visualization_code, {"df": df, "plt": plt, "st": st}
            )  # Pass 'st' to allow use of st.pyplot
            st.pyplot(plt)  # This will display the plot in the Streamlit interface

        except Exception as e:
            logging.error(f"An error occurred: {e}")
            st.error(f"An error occurred: {e}")

    # Function to generate a concise, question-specific natural language response
    def generate_response(natural_language_query, result_df):
        if result_df is None or result_df.empty:
            return "No results returned or an error occurred."

        data_as_dict = result_df.to_dict(orient="records")

        # Tailored prompt to generate a human-like sentence with no extra commentary
        response_prompt = f"""
        Answer the following question based on this data:
        Question: {natural_language_query}
        Data: {data_as_dict}
        Provide a concise and direct natural language sentence as the response, similar to how a human would write or speak the answer. Avoid including extra points or unrelated commentary.
        """

        result = subprocess.run(
            ["ollama", "run", "llama3.2", response_prompt],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

        return result.stdout.strip()

    # Main function for Streamlit interface for AI Assistant
    def ai_assistant():
        natural_query = st.text_input("Enter your question:")

        if st.button("Ask") or natural_query:  # Added button and Enter functionality
            start_time = time.time()
            process_memory_before = psutil.Process().memory_info().rss

            if any(
                keyword in natural_query.lower()
                for keyword in ["bar", "line", "pie", "scatter"]
            ):
                generate_graph(natural_query)
            else:
                sql_query = generate_sql(natural_query)
                # logging.info(f"Generated SQL query: {sql_query}")
                result_df = execute_sql(sql_query)
                final_response = generate_response(natural_query, result_df)
                st.write(final_response)

            process_memory_after = psutil.Process().memory_info().rss
            # logging.info(
            #     f"Memory Usage: {(process_memory_after - process_memory_before) / 1024:.2f} KB"
            # )
            # logging.info(f"Execution Time: {time.time() - start_time:.4f} seconds")

    ai_assistant()

# --- Forecast Code ---

elif app_selector == "Sales Forecast":
    data = pd.read_csv(r"/Users/ForecastResults.csv")
    data.rename(columns={"ds": "future_period"}, inplace=True)
    data.rename(columns={"yhat": "predictions"}, inplace=True)

    data["future_period"] = pd.to_datetime(data["future_period"], errors="coerce")

    def final_forecast(input_date, store_key, product_key, data):
        input_date = pd.to_datetime(input_date).strftime("%Y-%m-%d")
        filter_df = data[
            (data["future_period"] == input_date)
            & (data["store_key"] == store_key)
            & (data["product_key"] == product_key)
        ]

        if filter_df.empty:
            st.error(
                f"No data found for StoreKey={store_key}, ProductKey={product_key}, and input_date={input_date}"
            )
            return None, None

        result = filter_df["predictions"].iloc[0]
        entire_period_df = data[
            (data["store_key"] == store_key) & (data["product_key"] == product_key)
        ]

        plt.figure(figsize=(12, 6))
        plt.plot(
            entire_period_df["future_period"],
            entire_period_df["predictions"],
            label="Predicted Sales",
            color="orange",
        )

        ax = plt.gca()
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
        plt.gcf().autofmt_xdate(rotation=45)

        plt.title(f"Predictions for Store {store_key}, Product {product_key}")
        plt.xlabel("Future Period")
        plt.ylabel("Predicted Sales")
        plt.legend()
        plt.grid(True)
        plt.tight_layout()

        return result, plt

    input_date = st.date_input("Select a Date", pd.to_datetime("2010-01-01"))
    store_key = st.number_input("Enter Store Key", min_value=1, value=199)
    product_key = st.number_input("Enter Product Key", min_value=1, value=1752)

    if st.button("Generate Forecast"):
        result, plot = final_forecast(input_date, store_key, product_key, data)
        if result is not None:
            st.write(f"The prediction for {input_date} is: {result}")
            st.pyplot(plot)

# streamlit run Llama_code.py
