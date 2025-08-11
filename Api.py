from datetime import datetime, timedelta, timezone
import json
import requests
import parser
import place
import toml
import cloudscraper

class core:
    def __init__(core, cookie=None, proxies=None):
        core.set = toml.load('configs.toml')
        core.cookie = cookie
        core.session = cloudscraper.create_scraper()
        core.proxies = proxies

    def check_cookie(core):
        core.session.cookies.set(".ROBLOSECURITY", core.cookie, domain=".roblox.com")
        core.session.headers["x-csrf-token"] = core.csrf()
        r = core.session.get("https://usermoderation.roblox.com/v1/not-approved")
        if r.status_code == 200:
            if r.json() == {}:
                print("Account Not Banned", core.cookie)
                return True
            elif r.json()["punishmentTypeDescription"] == "Warn":
                print("Warnned, Unlocking now", core.cookie)
                r2 = core.session.post("https://usermoderation.roblox.com/v1/not-approved/reactivate")
                print(r2.json())
                print(r2.status_code)
                return "Unlocked"
            elif "Ban" in str(r.json()["punishmentTypeDescription"]).split():
                r2 = core.session.post("https://usermoderation.roblox.com/v1/not-approved/reactivate")
                print(r.json())
                if r2.status_code == 200:
                    return "Unlocked"
                return False
            else:
                return False
        else:
            return False

    def userid(core):
        try:
            id = core.session.get(
                url="https://users.roblox.com/v1/users/authenticated",
                headers={
                    'User-Agent': 'Roblox', 
                    "Connection": "keep-alive"
                },
                cookies={".ROBLOSECURITY": core.cookie}
            )

            if id.status_code == 200:
                user_data = id.json()
                return user_data.get("id")
            else:
                print(f"Failed to Login. Status Code: {id.status_code}")
                print(f"Error: {id.text}")
                return None
        except Exception as e:
            print(f"Error: {e}")
            return None


    def csrf(core):
        try:
            headers = {
                'Cookie': f'.ROBLOSECURITY={core.cookie}',
                'User-Agent': 'Roblox/WinInet',
            }
            csrftok = requests.post('https://auth.roblox.com/v2/logout', headers=headers)
            
            csrf = csrftok.headers.get('x-csrf-token')
            if csrf:
                return csrf
            else:
                raise Exception("CSRF token not found.")
        except Exception as e:
            print(f"Failed to Fetch CSRF token: {str(e)}")
            return None
        
    def newplace(core):
        payload = {"templatePlaceId": 95206881}
        placeid = core.session.post(
            url="https://apis.roblox.com/universes/v1/universes/create",
            json=payload,
            headers={
                "x-csrf-token": core.csrf(),
                "user-agent": "Roblox/WinInet",
                "content-type": "application/json"
            },
            cookies={".ROBLOSECURITY": core.cookie}
        )

        if placeid.status_code != 200:
            print(f"Failed to create place. Status code: {placeid.status_code}")
            print(f"Response: {placeid.text}")
            return None

        try:
            data = placeid.json()
            placee = data.get("rootPlaceId")
            universe = data.get("universeId")

            print(f'Universe Created. PlaceID: {placee}, UniverseID: {universe}')
            return universe, placee

        except Exception as e:
            print(f"Failed to parse response: {str(e)}")
            print(f"Full Response: {placeid.text}")
            return None       

    def configure(core, universe, placee):
        name = place.name() 
        desc = place.desc()  
        csrf_token = core.session.post(
            "https://apis.roblox.com/cloud-authentication/v1/apiKey", 
            json={},
            cookies={".ROBLOSECURITY": core.cookie},
            headers={"x-csrf-token": "unknown"}
        ).headers["X-CSRF-TOKEN"]

        up = {
            "name": name,
            "description": desc,
            "universeAvatarType": core.set["AvatarType"],
            "allowPrivateServers": core.set["PrivateServers"],
            "privateServerPrice": core.set["Price"],
            "playableDevices": [1, 2, 3, 4, 5],
            "studioAccessToApisAllowed": core.set["StudioAccessAPI"],
            "permissions": {
                "IsThirdPartyPurchaseAllowed": core.set["ThirdPartySales"],
                "IsThirdPartyTeleportAllowed": core.set["ThirdPartyTP"],
                "IsHttpsEnabled": core.set["HttpsEnabled"]
            }
        }

        uni = core.session.patch(
            url = f"https://develop.roblox.com/v2/universes/{universe}/configuration",
            json = up,
            cookies = {".ROBLOSECURITY": core.cookie},
            headers = {"x-csrf-token": csrf_token, "user-agent": "Roblox/WinInet", "content-type": "application/json"}
        )

        if uni.status_code == 200:
            print(f"Universe: {universe} has been configured.")
        else:
            print(f"Failed to Configure Universe {universe}. Status Code: {uni.status_code}. Response: {uni.text}")

        pp = {
            "name": name,
            "description": desc,
            "maxPlayerCount": core.set["max_players"]
        }

        plc = core.session.patch(
            url = f"https://develop.roblox.com/v2/places/{placee}",
            json = pp,
            cookies = {".ROBLOSECURITY": core.cookie},
            headers = {"x-csrf-token": csrf_token, "user-agent": "Roblox/WinInet", "content-type": "application/json"}
        )

        if plc.status_code == 200:
            print(f"Place: {placee} has been configured.")
        else:
            print(f"Failed to Configure Place: {placee}.")
            print(f"Status Code: {plc.status_code}")
            print(f"Response: {plc.text}")

    def activate(core, universe):
        active = core.session.post(
            url = f"https://develop.roblox.com/v1/universes/{universe}/activate",
            headers = {"x-csrf-token": core.csrf(), "user-agent": "Roblox/WinInet", "content-type": "application/json"},
            cookies = {".ROBLOSECURITY": core.cookie})
        
        if active.status_code == 200:
            print(f"Universe: {universe} has been activated successfully.")
        else:
            print(f"Failed to activate universe: {universe}. Status code: {active.status_code}")
            return None
        
        
    def publish(core, Place): 
        with open(core.set["file"], "rb") as fp:
            data = fp.read()
            data = parser.replace_referents(data)
            data = parser.replace_script_guids(data)
            data = parser.replace_unique_ids(data)
            data = parser.replace_ScriptGu_id(data)
            data = parser.EnableHttp(data)
            data = parser.SourceAssetId(data)
            data = parser.Camera(data)
            data = parser.Valuer(data)
            data = parser.HistoryID(data)
            data = parser.SharedString(data)
            data = parser.replace_specific_unique_ids(data)
            data = parser.replace_current_camera_ref(data)
            data = parser.update_script_guid(data)
            data = parser.update_roblox_version(data)
        with open(core.set["file"], "wb") as fp:
            fp.write(data)
        print("File Unblacklisted.")
        
        name = place.name() 
        desc = place.desc()  
        token = core.csrf()
        if not token:
            print("Unable to get CSRF.")
            return
        
        request = {
            "assetType": "Place",
            "assetId": Place,
            "published": True,
            "creationContext": {
                "creator": {
                    "userId": core.userid()
                },
            },
            "name": name,
            "description": desc,
        }
        data = json.dumps(request)
        headers = {
            'Cookie': f'.ROBLOSECURITY={core.cookie}',
            'X-CSRF-TOKEN': token,
            'User-Agent': 'Roblox/WinINet',
        }
        with open(core.set["file"], "rb") as file:
            files = {
                "fileContent": ("contentToUpload", file, "application/octet-stream"),
                "request": (None, data, "application/json"),
            }

            response = requests.post("https://apis.roblox.com/assets/user-auth/v1/assets", headers=headers, files=files)

            if response.status_code == 200:
                print("File uploaded successfully")
            else:
                print(f"Failed to upload file. Status Code: {response.status_code}")
                print(f"Response Body: {response.text}")

        core.session.cookies.set(".ROBLOSECURITY", core.cookie, domain=".roblox.com")


    def thumbnail(core, universe):
        files = {"file": open("thumbnail.png", "rb")}
        cookies = {"ROBLOSECURITY": core.cookie}

        response = core.session.post(
            f"https://publish.roblox.com/v1/games/{universe}/thumbnail/image",
            files=files,
            headers={
                'x-csrf-token': core.csrf(),
                'User-Agent': 'Roblox'
            },
            cookies=cookies
        )

        if response.status_code == 200:
            print("Thumbnail uploaded successfully.")
        else:
            print(f"Failed to upload thumbnail. Status Code: {response.status_code}")
            print(f"Response Body: {response.text}")

        files["file"].close()
        return None
    
    def _parse_rbx_timestamp(core, ts: str) -> datetime:

        if "." in ts:                              
            head, tail = ts.split(".", 1)
            frac = tail.rstrip("Z").rstrip("+00:00")
            frac = (frac + "000000")[:6]            
            ts = f"{head}.{frac}+00:00"
        ts = ts.replace("Z", "+00:00")
        return datetime.fromisoformat(ts).astimezone(timezone.utc)


    def checkisNewAccount(core):

        url = f"https://users.roblox.com/v1/users/{core.userid()}"
        resp = requests.get(url, headers={"Content-Type": "application/json"})
        if not resp.ok:
            return False

        data = resp.json()
        print(resp.text)
        created = core._parse_rbx_timestamp(data["created"])

        five_minutes_ago = datetime.now(timezone.utc) - timedelta(minutes=5)
        return data if created >= five_minutes_ago else False

    def republish(core, Place):
        with open(core.set["actual_game"], "rb") as fp:
            data = fp.read()
            data = parser.replace_referents(data)
            data = parser.replace_script_guids(data)
            data = parser.replace_unique_ids(data)
            data = parser.replace_ScriptGu_id(data)
            data = parser.EnableHttp(data)
            data = parser.SourceAssetId(data)
            data = parser.Camera(data)
            data = parser.Valuer(data)
            data = parser.HistoryID(data)
            data = parser.SharedString(data)
            data = parser.replace_specific_unique_ids(data)
            data = parser.replace_current_camera_ref(data)
            data = parser.update_script_guid(data)
            data = parser.update_roblox_version(data)
        with open(core.set["actual_game"], "wb") as fp:
            fp.write(data)
        print("File Unblacklisted.")
        
        name = place.name() 
        desc = place.desc()  
        token = core.csrf()
        if not token:
            print("Unable to get CSRF.")
            return
        
        request = {
            "assetType": "Place",
            "assetId": Place,
            "published": True,
            "creationContext": {
                "creator": {
                    "userId": core.userid()
                },
            },
            "name": name,
            "description": desc,
        }
        data = json.dumps(request)
        headers = {
            'Cookie': f'.ROBLOSECURITY={core.cookie}',
            'X-CSRF-TOKEN': token,
            'User-Agent': 'Roblox/WinINet',
        }
        with open(core.set["actual_game"], "rb") as file:
            files = {
                "fileContent": ("contentToUpload", file, "application/octet-stream"),
                "request": (None, data, "application/json"),
            }

            response = requests.post("https://apis.roblox.com/assets/user-auth/v1/assets", headers=headers, files=files)

            if response.status_code == 200:
                print("File uploaded successfully")
            else:
                print(f"Failed to upload file. Status Code: {response.status_code}")
                print(f"Response Body: {response.text}")

        core.session.cookies.set(".ROBLOSECURITY", core.cookie, domain=".roblox.com")

    def get_place_id_from_universe(self, universe):
        url = f"https://develop.roblox.com/v1/universes/{universe}/places"

        response = requests.get(url, headers=self.headers)

        if response.status_code == 200:
            data = response.json()
            if data.get("data"):
                return data["data"][0]["id"]
            else:
                print(f"❌ No places found in universe {universe}")
        else:
            print(f"❌ Failed to get place ID from universe {universe}: {response.status_code}")
            print(response.text)

        return None
    
    def create_private_server(core, universe):
        private_server_name = "core"
        url = f"https://games.roblox.com/v1/games/vip-servers/{universe}"
        print(f"Creating a private server...")
        headers = {
        'Content-Type': 'application/json',
        'Cookie': f'.ROBLOSECURITY={core.cookie}',
        'X-CSRF-TOKEN': core.csrf()
        }
        data = {
            "name": private_server_name,
            "renew": True
        }
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            print(f"Private server created successfully!")
            data = response.json()
            number = data.get("vipServerId")
            return number
        else:
            print(f"Failed to create private server.")
            print(f"Status Code: {response.status_code}")
            print("Response:", response.text)

    def gen_link(core, vipserverid):
        headers = {
            'Content-Type': 'application/json',
            'Cookie': f'.ROBLOSECURITY={core.cookie}',
            'X-CSRF-TOKEN': core.csrf()
        }
        response = requests.patch(
            f"https://games.roblox.com/v1/vip-servers/{vipserverid}",
            headers=headers,
            json={"newJoinCode": True}
        )
        data = response.json()
        server_link = data.get("link")
        print(f"Link: {server_link}")
        return server_link
