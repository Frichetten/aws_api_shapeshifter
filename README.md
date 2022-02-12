# aws_api_shapeshifter
A small library to alter AWS API requests; Used for fuzzing research

## NOTE
This tool was used to identify two XSS vulnerabilities in the [AWS Console](https://frichetten.com/blog/xss_in_aws_console/) and is based off previous work in [silently enumerating API permissions](https://frichetten.com/blog/aws-api-enum-vuln/). It is also what almost got me stuck with a $3,000/month bill (thank you to AWS for getting me out of that).

**This software is VERY hacky and should be considered alpha-quality at best**. It was originally designed with a very different intention and grew from there. If you are intendeding to use it I would advise you to intercept all traffic (https_proxy) with something like [Burp Suite](https://frichetten.com/blog/aws-api-enum-vuln/) so that you can inspect it. 

**DO NOT BLINDLY FUZZ EVERY API ACTION. YOU WILL END UP WITH A HEFTY BILL. I DO NOT TAKE RESPONSIBILITY FOR ANY COSTS ASSOCIATED WITH USING THIS SOFTWARE.**

## Currently Supported Parameter Options
* content_type (String) 
* noparams (Boolean) 
* creds (Credentials object) 
* host (String) 
* param (dictionary for params)
* protocol (json | ec2 | query | rest-json | rest-xml)
