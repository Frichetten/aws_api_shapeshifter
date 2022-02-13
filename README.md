# aws_api_shapeshifter
A small library to alter AWS API requests; Used for fuzzing research

## NOTE
This tool was used to identify two XSS vulnerabilities in the [AWS Console](https://frichetten.com/blog/xss_in_aws_console/) and is based off previous work in [silently enumerating API permissions](https://frichetten.com/blog/aws-api-enum-vuln/). It is also what almost got me stuck with a $3,000/month bill (thank you to AWS for getting me out of that).

**This software is VERY hacky and should be considered alpha-quality at best**. It was originally designed with a very different intention and grew from there. If you are intendeding to use it I would advise you to intercept all traffic (https_proxy) with something like [Burp Suite](https://frichetten.com/blog/aws-api-enum-vuln/) so that you can inspect it.

This library is **NOT** maintained and is provided as is. I realized it was marked as private and didn't see a reason not to make it public.

**DO NOT BLINDLY FUZZ EVERY API ACTION. YOU WILL END UP WITH A HEFTY BILL. I DO NOT TAKE RESPONSIBILITY FOR ANY COSTS ASSOCIATED WITH USING THIS SOFTWARE.**

## How to Use
There are some examples in [this](https://twitter.com/Frichette_n/status/1492707114250383368?s=20&t=7h1yvuHaKwVu60q9e2Y_uQ) Twitter thread. 

## Currently Supported Parameter Options
* content_type (String) 
* noparams (Boolean) 
* creds (Credentials object) 
* host (String) 
* param (dictionary for params)
* protocol (json | ec2 | query | rest-json | rest-xml)
