# scrapyEurex

Scrapy spider to get information from Eurexchange

### Instructions
Run Python 3 scrapy with:
> scrapy crawl estx50spider -o option_chain.json

Then you can calculate greeks and IV for each option, but due to the libraries used you have to execute using Python 2.7:
> python27 add_greeks_to_json.py --risk_free_rate 0.01 --underlying_price 3000.0 --input_json option_chain.json
Session date can also be specified. Otherwise, the script will consider today as the session date for all the options listed in input json file.

Finally, you can get some graphs from the json file:
> python eurex_data_loader.py --input_file option_chain.json --expiration_date 17/03/2017
You can also use a whole input folder and see the evolution of open interest along time for a certain option:
> python eurex_data_loader.py --input_folder data/ --expiration_date 17/03/2017 --strike 3000.0

Enjoy (and if you get rich, I accept some tips :D)

### License
Privative for commercial and professional usage. Contact the author