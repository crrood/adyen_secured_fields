// Define a custom style.
var styleObject = {
	base: {
		color: 'black',
		fontSize: '16px',
		fontSmoothing: 'antialiased',
		fontFamily: 'Helvetica'
	},
	error: {
		color: 'red'
	},
	placeholder: {
		color: '#d8d8d8'
	},
	validated: {
		color: 'green'
	}
};

window._$bsdl = true;

// Send request to server
function AJAXPost(path, headers, params, method, callback) {
	var request = new XMLHttpRequest();
	request.open(method || "POST", path, true);
	request.onreadystatechange = callback;

	for (var key in headers) {
		request.setRequestHeader(key, headers[key]);
	}

	request.send(params);
};

// Called on page load
function initForms() {
	// Logging
	document.querySelector("#logInputs").addEventListener("click", function() {
		console.log(document.querySelectorAll("input:not([type='button']):not([type='submit'])"));
	});

	// Initialize object
	var securedFields = csf(
		{
			configObject : {
				originKey : "pub.v2.8115054323780109.aHR0cDovL2xvY2FsaG9zdDo4MDAw.B92basPQjzeM7_TtJ2IKZoln780QtvwAiPFDEbKs7Ng"
			},
			rootNode: '.cards-div',
			paymentMethods : {
				card : {
					sfStyles : styleObject,
				}
			}
		}
	);

	// Listen to events.
	securedFields.onLoad(function(){
		console.log('All fields have been loaded');
	});

	securedFields.onAllValid(function(allValidObject){
		// Triggers when all credit card input fields are valid - and triggers again if this state changes.
		if(allValidObject.allValid === true){
			console.log('All credit card input is valid :-)');
		}
	});

	securedFields.onBrand(function(brandObject){
		// Triggers when receiving a brand callback from the credit card number validation.
		if(brandObject.brand) {
			document.getElementById('card-type').innerHTML = brandObject.brand;
		}
	});

	// Send data to server
	document.querySelector("#submitPayment").addEventListener("click", function() {

		url = "http://localhost:8000/cgi-bin/submit.py";
		paramString = "?";
		elems = document.querySelectorAll("input:not([type='button']):not([type='submit'])");
		for (elem of elems) {
			paramString = paramString + elem.name + "=" + elem.value + "&";
		}

		console.log("Data sent to local server:");
		console.log(paramString);

		AJAXPost(url + paramString, "", "", "POST", function() {
			if (this.readyState == 4) {
				console.log("Response from local server:");
				console.log(this.responseText);

				document.querySelector("#output").innerHTML = this.responseText;
			}
		});
	});
}