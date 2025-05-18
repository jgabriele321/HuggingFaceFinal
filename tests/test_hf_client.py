import os
from huggingface_hub import InferenceClient, HfApi

# Print the token we're using (masked for security)
token = os.environ.get("HF_TOKEN", "")
if token:
    print(f"Using token: hf_...{token[-4:]}")
else:
    print("No HF_TOKEN found in environment")

# Verify we can authenticate using the HfApi
try:
    api = HfApi()
    user_info = api.whoami()
    print(f"Successfully authenticated as: {user_info.get('name')}")
except Exception as e:
    print(f"Authentication error with HfApi: {e}")

# Try to use the InferenceClient
try:
    print("\nTesting InferenceClient...")
    client = InferenceClient(model="mistralai/Mistral-7B-Instruct-v0.2")
    print("Client created successfully")
    
    response = client.text_generation(
        "Hello, how are you?",
        max_new_tokens=10,
        temperature=0.7
    )
    print(f"Success! Response: {response}")
except Exception as e:
    print(f"Error with InferenceClient: {e}") 