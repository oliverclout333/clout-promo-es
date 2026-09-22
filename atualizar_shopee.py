import os
import time
import json
import hashlib
import urllib.request

APP_ID = os.environ["SHOPEE_APP_ID"]
SECRET = os.environ["SHOPEE_SECRET"]

URL = "https://open-api.affiliate.shopee.com.br/graphql"

query = """
query {
  productOfferV2(
    listType: 0
    sortType: 2
    page: 1
    limit: 5
  ) {
    nodes {
      productName
      price
      imageUrl
      productLink
      offerLink
      priceMin
      priceMax
      priceDiscountRate
      commissionRate
      commission
    }
  }
}
"""

payload = json.dumps(
    {"query": query, "variables": {}},
    separators=(",", ":")
)

timestamp = int(time.time())

signature_string = f"{APP_ID}{timestamp}{payload}{SECRET}"
signature = hashlib.sha256(
    signature_string.encode("utf-8")
).hexdigest()

authorization = (
    f"SHA256 Credential={APP_ID}, "
    f"Timestamp={timestamp}, "
    f"Signature={signature}"
)

request = urllib.request.Request(
    URL,
    data=payload.encode("utf-8"),
    headers={
        "Content-Type": "application/json",
        "Authorization": authorization
    },
    method="POST"
)

with urllib.request.urlopen(request) as response:
    resultado = json.loads(response.read().decode("utf-8"))

if "errors" in resultado:
    print("ERRO DA SHOPEE:")
    print(json.dumps(resultado["errors"], indent=2, ensure_ascii=False))
    raise SystemExit(1)

produtos = resultado["data"]["productOfferV2"]["nodes"]

print(f"SUCESSO! A Shopee retornou {len(produtos)} produtos.")

for numero, produto in enumerate(produtos, 1):
    print(
        f"{numero}. {produto.get('productName')} | "
        f"R$ {produto.get('price')}"
    )

with open("produtos_shopee.json", "w", encoding="utf-8") as arquivo:
    json.dump(
        produtos,
        arquivo,
        ensure_ascii=False,
        indent=2
    )

print("Arquivo produtos_shopee.json criado.")
