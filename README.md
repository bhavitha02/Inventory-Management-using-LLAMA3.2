# Simplifying Inventory Management through Natural Language Queries:

Effective inventory management is a critical need in today’s fast-paced business world. Leveraging advancements in large language models (LLMs), we developed a solution that enables users to retrieve and visualize historical data, providing essential insights through natural language inputs. This approach is particularly beneficial for individuals without technical expertise in handling complex datasets.

This solution contains 3 main components – 
1.	Web Interface
2.	Llama power querying
3.	Sales forecasting

## Components:

### 1.	Web Interface

- Built a user-friendly web platform for accessing inventory data through natural language queries using Streamlit.

![UI](/assets/ui.png "UI")

    
- Configured an MSSQL server in a Docker container with the Data Warehouse, seamlessly connecting it to Azure Data Factory for streamlined database access.
 
 ![docker](/assets/docker.png "docker")


### 2.	Llama powered Querying and Visualization:
- Integrated Llama LLM (v3.2) with few-shot learning and prompt engineering to translate natural language into SQL queries and Python visualization scripts.
- Enabled users to generate interactive visualizations such as bar, pie, and line charts for clear and effective data insights.

### 3.	Sales Forecasting:
- Leveraged the Prophet model to forecast sales.
- Implemented features to predict sales for specific store and product combinations on future dates, including a yearly forecast display.
- Designed an interface for users to query forecasts by selecting store keys, product keys, and dates.



## Example usage
We will use publicly available contoso dataset (link and more details on this) for demo purposes.

### Part 1 – Loading Contoso data warehouse in SQL server
Data loading steps for Contoso

1. Download Contoso BAK file from: https://drive.google.com/file/d/1LwiXsyltPHoiSmO301j8xGcajWzo3u9d/view?usp=sharing

2. Copy this backup file into the container using the command below 
```docker cp [folder location where you downloaded the backup file]/ContosoRetailDW.bak localmssql:/tmp/ContosoRetailDW.bak```

3. Follow the instructions at this link to restore the database from recently downloaded .bak file

4. https://www.quackit.com/sql_server/mac/how_to_restore_a_bak_file_using_azure_data_studio.cfm

### Part 2 - Asking question on inventory in natural language
1.	Let’s ask the question “What is the total inventory value and on-order quantity for each vendor at the Contoso Northampton store?” or
“Display how many products are there by each manufacturer using bar graph”

Demo:


