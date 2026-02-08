from fastapi import FastAPI, Request
from datetime import datetime
import json

app = FastAPI(title="Giorgio Test")

@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    
    print("\n" + "="*60)
    print(f"⏰ {datetime.now().strftime('%H:%M:%S')}")
    print(f"📨 Event: {data.get('NotificationType', 'Unknown')}")
    
    user = data.get('User', {})
    print(f"👤 User: {user.get('Name')} ({user.get('Id', 'no-id')[:8]}...)")
    
    item = data.get('Item', {})
    print(f"🎬 Content: {item.get('Name')} ({item.get('Type')})")
    print(f"   Year: {item.get('Year')}")
    print(f"   Genres: {item.get('Genres', [])}")
    
    print(f"✅ PlayedToCompletion: {data.get('PlayedToCompletion')}")
    
    # Sauvegarde le payload complet
    filename = f"webhook_{datetime.now().strftime('%H%M%S')}.json"
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"💾 Saved to {filename}")
    
    print("="*60)
    
    return {"status": "received"}

if __name__ == "__main__":
    import uvicorn
    print("🚀 Giorgio Test Server (FastAPI)")
    print("   Swagger UI: http://localhost:5555/docs")
    print("   Webhook endpoint: http://<ton-ip>:5555/webhook\n")
    uvicorn.run(app, host="0.0.0.0", port=5555)