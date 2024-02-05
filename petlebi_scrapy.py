import json
import scrapy
from scrapy import Selector
import re
from w3lib.html import remove_tags


class ProductItem(scrapy.Item):  # product class for necessary fields
    product_URL = scrapy.Field()
    product_name = scrapy.Field()
    product_barcode = scrapy.Field()
    product_price = scrapy.Field()
    product_stock = scrapy.Field()
    product_images = scrapy.Field()
    product_description = scrapy.Field()
    product_sku = scrapy.Field()
    product_category = scrapy.Field()
    product_ID = scrapy.Field()
    product_brand = scrapy.Field()


class ScrapyPetlebiSpider(scrapy.Spider):    # spider class to run
    name = "scrapy_petlebi"
    allowed_domains = ["petlebi.com"]
    start_urls = ["https://www.petlebi.com/alisveris/ara?page=1"]   # start from parameter ?page=1 and goes to ?page=220

    custom_settings = {
        'ROBOTSTXT_OBEY': False,
    }
    all_products = []   # list of my products

    def parse(self, response):
        selector = Selector(text=response.text)

        products = selector.css('#products .search-product-box')
        for product in products:
            current_product = ProductItem()

            product_url = product.css('a.p-link::attr(href)').get()
            current_product['product_URL'] = product_url
            yield scrapy.Request(url=product_url, callback=self.parseDetails, meta={'current_product': current_product})

            # next page configuration
            script_text = response.css('script:contains("next_data_url")::text').get()
            if script_text:
                match = re.search(r"next_data_url\s*=\s*'([^']+)'", script_text)
                if match:
                    next_data_url = match.group(1)
                    next_data_url = next_data_url[:-6]
                    if next_data_url:
                        yield scrapy.Request(url=next_data_url, callback=self.parse)  # request to the products' page url
                    else:
                        self.logger.info('next_data_url is blank or null. No request yielded.')
                else:
                    self.logger.warning('No next_data_url found in the script.')
            else:
                self.logger.warning('No script element found containing "next_data_url".')

    def parseDetails(self, response):
        selector = Selector(text=response.text)
        current_product = response.meta.get('current_product', ProductItem())

        # product_sku
        text_of_json = selector.css('script[type="application/ld+json"]::text').get()
        pattern = r'"sku"\s*:\s*"([^"]+)"'
        match = re.search(pattern, text_of_json)
        if match:
            sku_value = match.group(1)
        current_product['product_sku'] = sku_value

        # product_category
        pattern = r'"category"\s*:\s*"([^"]+)"'
        match = re.search(pattern, text_of_json)
        if match:
            category_value = match.group(1)
        current_product['product_category'] = category_value

        # product_id
        pattern_for_id = r'"productID":(\d+)'
        text_content_for_id = ''.join(selector.css('::text').extract())
        match = re.search(pattern_for_id, text_content_for_id)
        if match:
            id_value = match.group(1)
        current_product['product_ID'] = id_value

        # other values
        details = selector.css('.row.product-detail-main')
        # product_name
        current_product['product_name'] = details.css('.product-h1::text').get()

        # product_price
        new_price = details.css('.new-price::text').get()
        old_price = details.css('.old-price::text').get()
        discount_price = details.css('.pd-price .pd-price .new-price::text').get()
        current_product['product_price'] = [old_price, new_price, discount_price]

        # product_stock
        quantity_values = details.css('#quantity option::attr(value)').getall()
        if quantity_values:
            stock = max(int(value) for value in quantity_values)
        else:
            stock = 0
        current_product['product_stock'] = stock

        # product_images
        main_image_url = details.css('.MagicZoom img.img-fluid::attr(src)').get()
        small_image_urls = details.css('.MagicScroll img:first-of-type::attr(src)').getall()
        all_images = [main_image_url, small_image_urls]
        current_product['product_images'] = all_images

        details = selector.css('#myTabContent')
        # product_brand
        current_product['product_brand'] = details.css('.col-10 span a::text').get()

        # product_barcode
        current_product['product_barcode'] = details.css('div:contains("BARKOD") + div::text').get()

        # product_description
        description_text = details.css(
            '#productDescription p, #productDescription ul li, #productDescription p strong::text').getall()
        cleaned_description = []
        for text in description_text:
            cleaned_text = remove_tags(text)
            cleaned_text = re.sub(r'\s*\u200b\s*', ' ', cleaned_text)  # Remove non-breaking space characters
            cleaned_description.append(cleaned_text.strip())
        joined_description = ' '.join(cleaned_description).strip()
        current_product['product_description'] = joined_description if joined_description else None

        desired_order = ['product_URL', 'product_name', 'product_barcode', 'product_price',
                         'product_stock', 'product_images', 'product_description', 'product_sku',
                         'product_category', 'product_ID', 'product_brand']
        ordered_product = {key: current_product[key] for key in desired_order}
        self.all_products.append(ordered_product)

    def closed(self, response):

        for product in self.all_products:
            print("current product: ", product)

        with open('petlebi_products.json', 'w', encoding='utf-8') as json_file:
            json.dump(self.all_products, json_file, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    from scrapy.crawler import CrawlerProcess

    process = CrawlerProcess()
    process.crawl(ScrapyPetlebiSpider)
    process.start()
