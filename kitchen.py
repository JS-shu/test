from escpos.printer import Network

kitchen = Network("10.168.168.87") #Printer IP Address
kitchen.text("Hello World\n")
kitchen.barcode('4006381333931', 'EAN13', 64, 2, '', '')
kitchen.qr("Rg1/6Du6spoAWjDd1FA82XDQxOWhSi7AQRuWcAwjXJpwulJYRdqAWRfDoGn44MOBxSFjMZFS6esdlQhFu+snj3y9B8sA7/YCoicqhJWxNwLK90sAVLfdKlVQAgrM2cFILY3e2c6tQIu/CKwsn7JXMCqi+CxUH2kT6Bpj5rND5+8w2nToad2ySWP86SQF3u42NwfCXBKD3Ah64UENFl7/rzjEcYMkxf3hza+0Sx0TKgk=prAdXHbE2GvUp===",size=8)
kitchen.image()
kitchen.cut()

# winpos 測試
