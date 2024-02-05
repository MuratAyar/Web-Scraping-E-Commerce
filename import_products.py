import json
import mysql.connector
# import pymysql

# Read JSON data from file
with open('petlebi_products.json', 'r', encoding='utf-8') as file:
    json_data = json.load(file)

# MySQL database configuration
db_config = {
    'host': 'localhost',
    'user': 'ayarm',
    'password': '321321',
    'database': 'petlebidb',
}

# Connect to the MySQL server
conn = mysql.connector.connect(**db_config)
# conn = pymysql.connect(**db_config)
cursor = conn.cursor()

# Insert JSON data into the 'petlebi' table
try:
    for record in json_data:
        product_price_str = json.dumps(record.get('product_price', []))
        product_images_str = json.dumps(record.get('product_images', []))

        query = "INSERT INTO petlebi (product_URL, product_name, product_barcode, product_price, product_stock, " \
                "product_images, product_description, product_sku, product_category, product_ID, product_brand) " \
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        values = (
            record['product_URL'],
            record['product_name'],
            record['product_barcode'],
            product_price_str,  # Assuming 'product_price' is a list
            record['product_stock'],
            product_images_str,
            record['product_description'],
            record['product_sku'],
            record['product_category'],
            record['product_ID'],
            record['product_brand']
        )
        cursor.execute(query, values)

    # Commit changes
    conn.commit()
    print("Data inserted successfully.")

except mysql.connector.Error as err:
    print(f"Error: {err}")
    conn.rollback()

finally:
    # Close the cursor and connection
    cursor.close()
    conn.close()
