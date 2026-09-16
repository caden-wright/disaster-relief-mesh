import secrets
import json
import os
import sys

def generate_deployment_keys(num_help_points: int, output_dir: str = "keys"):
    os.makedirs(output_dir, exist_ok=True)
    
    gateway_key_store = {}
    
    for i in range(1, num_help_points + 1):
        raw_key = secrets.token_bytes(32)
        gateway_key_store[i] = raw_key.hex()
        
        hp_file = os.path.join(output_dir, f"help_point_{i}.key")
        with open(hp_file, "wb") as f:
            f.write(raw_key)
        print(f"Generated key for Help Point {i} -> {hp_file}")
        
    gw_file = os.path.join(output_dir, "gateway_key_store.json")
    with open(gw_file, "w") as f:
        json.dump(gateway_key_store, f, indent=2)
    print(f"Generated Gateway key store -> {gw_file}")

if __name__ == "__main__":
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    generate_deployment_keys(count)
