#!/Users/colinr/miniconda3/bin/python3

# general utilities
import json, os, datetime, csv

# HMAC
import base64, binascii, hmac, hashlib
from collections import OrderedDict

# HTTP parsing
from urllib.parse import parse_qs, urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError

# browser control
import webbrowser

##################################
##		HARDCODED VALUES		##
##################################

LOCAL_ADDRESS = "http://localhost:8000"
RETURN_URL = "{}/cgi-bin/submit.py?endpoint=result_page".format(LOCAL_ADDRESS)

##############################
##		AUTHENTICATION		##
##############################

# hardcoded authentication values
MERCHANT_ACCOUNT = "ColinRood"

'''
load credentials from file for specified Merchant Account

first row is keys
subsequent rows are sets of credentials

for example:
merchantAccount,wsUser,wsPass,apiKey
ColinRood,ws@Company.AdyenTechSupport,superSecurePassword,AQEyhmfxLIrIaBdEw0m...
'''
with open("credentials.csv") as credentials_file:
	reader = csv.DictReader(credentials_file)

	merchant_account_found = False
	for row in reader:
		if row["merchantAccount"] == MERCHANT_ACCOUNT:
			WS_USERNAME = row["wsUser"]
			WS_PASSWORD = row["wsPass"]
			CHECKOUT_API_KEY = row["apiKey"]
			merchant_account_found = True

	# send an error if credentials aren't provided for Merchant Account
	if not merchant_account_found:
		send_debug("Merchant Account {} not found in credentials.csv".format(MERCHANT_ACCOUNT))
		exit(1)

##############################
##		HELPER METHODS		##
##############################

# send request to server and return bytecode response
def send_request(url, data, headers, data_type="json"):

	# encode data
	if data_type == "formdata":
		formatted_data = urlencode(data).encode("utf8")
	elif data_type == "json":
		formatted_data = json.dumps(data).encode("utf8")
	else:
		formatted_data = data

	# create request object
	request = Request(url, formatted_data, headers)

	# handle errors in response from server
	try:
		return urlopen(request).read()
	except HTTPError as e:
		return "{}".format(e).encode("utf8")
	except:
		return "error sending request".encode("utf8")

# respond with result
def send_response(result, content_type="text/html", skipHeaders=False):
	if not skipHeaders:
		print("Content-type:{}\r\n".format(content_type), end="")
		print("Content-length:{}\r\n".format(len(result)), end="")
		print("\r\n", end="")

	if type(result) is bytes:
		print("{}\r\n".format(result.decode("utf8")), end="")
	elif type(result) is str:
		print("{}\r\n".format(result), end="")
	else:
		print("Invalid data type in send_response")

# respond with raw data
def send_debug(data, content_type="text/plain", duplicate=False):
	if not duplicate:
		print("Content-type:{}\r\n".format(content_type))
	print(data)
	
	if content_type == "text/html":
		print("<br><br>")
	else:
		print("\r\n\r\n")

# indent fields in data object
def indent_field(data, parent, target):
	if not parent in data.keys():
		data[parent] = {}
	
	data[parent][target] = data[target]
	del data[target]

# reformat amount data into indented object for Adyen
def reformat_amount(data):
	indent_field(data, "amount", "value")
	indent_field(data, "amount", "currency")

# reformat card data into indented object for Adyen
def reformat_card(data):
	indent_field(data, "card", "number")
	indent_field(data, "card", "expiryMonth")
	indent_field(data, "card", "expiryYear")
	indent_field(data, "card", "holderName")
	indent_field(data, "card", "cvc")

def reformat_card_checkout(data, encrypted=True):
	if encrypted:
		indent_field(data, "paymentMethod", "encryptedCardNumber")
		indent_field(data, "paymentMethod", "encryptedExpiryMonth")
		indent_field(data, "paymentMethod", "encryptedExpiryYear")
		indent_field(data, "paymentMethod", "holderName")
		indent_field(data, "paymentMethod", "encryptedSecurityCode")
		data["paymentMethod"]["type"] = "scheme"

		# change spaces back to plus signs
		data["paymentMethod"]["encryptedCardNumber"] = data["paymentMethod"]["encryptedCardNumber"].replace(" ", "+")
		data["paymentMethod"]["encryptedExpiryMonth"] = data["paymentMethod"]["encryptedExpiryMonth"].replace(" ", "+")
		data["paymentMethod"]["encryptedExpiryYear"] = data["paymentMethod"]["encryptedExpiryYear"].replace(" ", "+")
		data["paymentMethod"]["holderName"] = data["paymentMethod"]["holderName"].replace(" ", "+")
		data["paymentMethod"]["encryptedSecurityCode"] = data["paymentMethod"]["encryptedSecurityCode"].replace(" ", "+")
	else:
		indent_field(data, "paymentMethod", "number")
		indent_field(data, "paymentMethod", "expiryMonth")
		indent_field(data, "paymentMethod", "expiryYear")
		indent_field(data, "paymentMethod", "holderName")
		indent_field(data, "paymentMethod", "cvc")
		data["paymentMethod"]["type"] = "scheme"

##############################
##		SECURED FIELDS		##
##############################

# adyen-hosted iframes for card data entry
def secured_fields_setup(data):

	# request info
	url = "https://checkout-test.adyen.com/services/PaymentSetupAndVerification/v30/setup"
	headers = {
		"Content-Type": "application/json",
		"X-API-Key": CHECKOUT_API_KEY
	}

	# static fields
	data["origin"] = LOCAL_ADDRESS
	data["returnUrl"] = RETURN_URL

	data["additionalData"] = {}
	data["additionalData"]["executeThreeD"] = "True"

	# move amount data into parent object
	reformat_amount(data)

	# get and return response
	result = send_request(url, data, headers)
	send_response(result, "application/json")

# send encrypted card data to Adyen
def secured_fields_submit(data):

	# request info
	url = "https://checkout-test.adyen.com/services/PaymentSetupAndVerification/v32/payments"
	headers = {
		"Content-Type": "application/json",
		"X-API-Key": CHECKOUT_API_KEY
	}

	# static fields
	data["origin"] = LOCAL_ADDRESS
	data["returnUrl"] = RETURN_URL

	# move amount data into parent object
	reformat_amount(data)

	# move card data into paymentMethod object
	reformat_card_checkout(data)

	# get and return response
	result = send_request(url, data, headers)
	send_response(result, "application/json")

##########################
##		RESULT PAGE		##
##########################

# landing page for complete transactions
def result_page(data):
	send_debug("Response from Adyen:")
	send_debug(data, duplicate=True)

##############################
##		ROUTER METHOD		##
##############################

# parse payment data from URL params 
request_data = parse_qs(os.environ["QUERY_STRING"])
data = {}
for param in request_data.keys():
	data[param] = request_data[param][0]

# map data["endpoint"] value to server methods
router = {
	"secured_fields_setup": secured_fields_setup,
	"secured_fields_submit": secured_fields_submit,
	"result_page": result_page
}

try:
	# parse endpoint from request
	endpoint = data["endpoint"]
	del data["endpoint"]

except:
	send_debug("endpoint value missing in request data:")
	send_debug(data, duplicate=True)
	exit(1)

# add merchantAccount to data
data["merchantAccount"] = MERCHANT_ACCOUNT

try:
	# send to proper method
	router[endpoint](data)
	
except KeyError as e:
	# in case of errors echo data back to client
	send_debug("SERVER ERROR")
	send_debug("Method not found: \n{}".format(e), duplicate=True)
	send_debug("\n{}".format(data), duplicate=True)
