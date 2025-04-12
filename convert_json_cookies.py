import json

with open("cookies.json", "r") as f:
    cookies = json.load(f)

with open("cookies.txt", "w") as f:
    f.write("# Netscape HTTP Cookie File\n")
    for cookie in cookies:
        domain = cookie["domain"]
        flag = "TRUE" if not cookie.get("hostOnly", False) else "FALSE"
        path = cookie["path"]
        secure = "TRUE" if cookie.get("secure") else "FALSE"
        expiry = int(cookie.get("expirationDate", 1893456000))  # default to ~2030
        name = cookie["name"]
        value = cookie["value"]
        f.write(f"{domain}\t{flag}\t{path}\t{secure}\t{expiry}\t{name}\t{value}\n")
